"""Portable Extra Trees inference. Training libraries are never imported by the API.

The bundled model learns synthetic per-person relief demand, not flood depth.
Intervals are split-conformal estimates calibrated on synthetic data only.
"""
import json
import math
import hashlib
import struct
from functools import lru_cache
from pathlib import Path

ITEMS = ("water_litres", "food_rations", "medical_kits")
FEATURES = ("Rainfall_mm_hr", "Flood_Depth_m", "Pop_Density_sqkm", "Vulnerability_Score")


class DemandPredictor:
    def __init__(self, path=None):
        self.is_loaded = False
        self.model = None
        self.load_error = None
        directory = Path(__file__).parents[2] / 'ml_pipeline/models'
        path = Path(path) if path else (directory / 'demand_ensemble_v2.json' if (directory / 'demand_ensemble_v2.json').exists() else directory / 'demand_forest.json')
        self.path = path
        self.model_sha256 = None
        try:
            raw = path.read_bytes()
            self.model_sha256 = hashlib.sha256(raw).hexdigest()
            model = json.loads(raw)
            if model["schema_version"] not in (1, 2) or model["features"] != list(FEATURES) or not model["trees"]:
                raise ValueError("Unsupported demand model schema")
            self._validate(model)
            self.model = model
            self.is_loaded = True
        except (OSError, ValueError, KeyError, TypeError, IndexError) as exc:
            self.load_error = str(exc)

    @staticmethod
    def _validate(model):
        if model['schema_version'] == 2:
            weights = model['component_weights']
            linear = model['linear']
            if (len(weights) != 3 or any(len(row) != 3 or not all(math.isfinite(w) and w >= 0 for w in row)
                                          or abs(sum(row) - 1) > 1e-8 for row in weights)
                    or len(linear['coef']) != 3 or any(len(row) != 4 or not all(math.isfinite(v) for v in row) for row in linear['coef'])
                    or len(linear['intercept']) != 3 or not all(math.isfinite(v) for v in linear['intercept'])
                    or any(t.get('component') not in (0, 1) for t in model['trees'])
                    or not all(any(t['component'] == k for t in model['trees']) for k in (0, 1))):
                raise ValueError('Invalid blend weights or linear component')
        ranges = model["feature_ranges"]
        radius = model["conformal_radius_per_person"]
        if (len(ranges) != 4 or any(len(b) != 2 or not all(math.isfinite(v) for v in b) or b[0] > b[1] for b in ranges)
                or len(radius) != 3 or any(not math.isfinite(v) or v < 0 for v in radius)
                or not 0 < model["nominal_coverage"] < 1):
            raise ValueError("Invalid demand model ranges or uncertainty calibration")
        for tree in model["trees"]:
            size = len(tree["left"])
            if not size or any(len(tree[k]) != size for k in ("right", "feature", "threshold", "value")):
                raise ValueError("Invalid demand tree arrays")
            for node in range(size):
                left, right = tree["left"][node], tree["right"][node]
                if left == -1:
                    if right != -1 or len(tree["value"][node]) != 3 or not all(math.isfinite(v) and v >= 0 for v in tree["value"][node]):
                        raise ValueError("Invalid demand tree leaf")
                elif (not isinstance(left, int) or not isinstance(right, int)
                      or not node < left < size or not node < right < size
                      or not isinstance(tree["feature"][node], int)
                      or not 0 <= tree["feature"][node] < 4
                      or not math.isfinite(tree["threshold"][node])):
                    raise ValueError("Invalid demand tree branch")

    def metadata(self):
        return {
            "name": self.model.get('name', 'Extra Trees + split conformal') if self.is_loaded else "Planning rules",
            'model_sha256': self.model_sha256,
            'artifact_name': self.path.name,
            'component_weights': self.model.get('component_weights') if self.model else None,
            'components': self.model.get('components', ['Extra Trees']) if self.model else [],
            "training_data": "synthetic",
            "validated_for_live_use": False,
            "features": list(FEATURES),
            "tree_count": len(self.model["trees"]) if self.model else 0,
            "dataset_sha256": self.model.get("dataset_sha256") if self.model else None,
            "load_error": self.load_error,
            "evaluation": self.model.get("evaluation") if self.model else None,
        }

    def predict_demand(self, rainfall_mm_hr, flood_depth_m, pop_density_sqkm, vulnerability, shelter_occupancy):
        if not self.is_loaded:
            return None
        values = [rainfall_mm_hr, flood_depth_m, pop_density_sqkm, vulnerability]
        if not all(math.isfinite(v) for v in values) or not math.isfinite(shelter_occupancy) or shelter_occupancy < 0:
            return None
        # Avoid extrapolating a tree model into unrepresented conditions.
        if any(v < bounds[0] or v > bounds[1] for v, bounds in zip(values, self.model["feature_ranges"])):
            return None
        pop = int(shelter_occupancy)
        predictions = self._predict_per_person(tuple(values))
        floors = [3.0, 3.0, 0.02]
        result = {"is_ai_predicted": True, "model": "extra_trees_conformal", "training_data": "synthetic"}
        intervals = {}
        for i, item in enumerate(ITEMS):
            estimate = max(floors[i], predictions[i]) * pop
            radius = self.model["conformal_radius_per_person"][i] * pop
            result[item] = math.ceil(estimate)
            intervals[item] = {
                "lower": max(math.ceil(floors[i] * pop), math.floor(estimate - radius)),
                "upper": math.ceil(estimate + radius),
            }
        result["prediction_intervals"] = intervals
        result["interval_nominal_coverage"] = self.model["nominal_coverage"]
        result['model'] = 'event_cv_blend_conformal' if self.model['schema_version'] == 2 else 'extra_trees_conformal'
        return result

    @lru_cache(maxsize=1024)
    def _predict_per_person(self, values):
        # Occupancy scales outputs after inference; identical conditions share
        # one bounded cache entry even across different shelter headcounts.
        predictions = [0.0, 0.0, 0.0]
        components = [[0.0] * 3 for _ in range(2)]
        counts = [0, 0]
        tree_values = [struct.unpack('f', struct.pack('f', v))[0] for v in values]
        for tree in self.model["trees"]:
            node = 0
            while tree["left"][node] != -1:
                node = tree["left"][node] if tree_values[tree["feature"][node]] <= tree["threshold"][node] else tree["right"][node]
            component = tree.get('component', 0)
            counts[component] += 1
            for i, value in enumerate(tree["value"][node]):
                components[component][i] += value
        if self.model['schema_version'] == 2:
            linear = self.model['linear']
            for i, weights in enumerate(self.model['component_weights']):
                lin = linear['intercept'][i] + sum(c * v for c, v in zip(linear['coef'][i], values))
                predictions[i] = (weights[0] * components[0][i] / counts[0]
                                  + weights[1] * components[1][i] / counts[1] + weights[2] * lin)
        else:
            predictions = [value / counts[0] for value in components[0]]
        return tuple(predictions)

    def explain(self, values):
        """Exact four-feature Shapley decomposition against one training median.

        This is a local baseline-dependent attribution, not causal evidence or
        conditional SHAP. Intervals and planning-floor adjustments are separate.
        """
        if not self.is_loaded:
            return None
        reference = self.model.get('reference', [(lo + hi) / 2 for lo, hi in self.model['feature_ranges']])
        outputs = {}
        for mask in range(16):
            coalition = tuple(values[i] if mask & (1 << i) else reference[i] for i in range(4))
            outputs[mask] = self._predict_per_person(coalition)
        contributions = [[0.0] * 3 for _ in range(4)]
        for i in range(4):
            for mask in range(16):
                if mask & (1 << i):
                    continue
                size = mask.bit_count()
                weight = math.factorial(size) * math.factorial(3 - size) / math.factorial(4)
                for j in range(3):
                    contributions[i][j] += weight * (outputs[mask | (1 << i)][j] - outputs[mask][j])
        return {'method': 'exact_baseline_shapley_4_features', 'reference_features': dict(zip(FEATURES, reference)),
                'baseline_per_person': dict(zip(ITEMS, outputs[0])),
                'prediction_per_person_before_floor': dict(zip(ITEMS, outputs[15])),
                'contributions_per_person': {f: dict(zip(ITEMS, row)) for f, row in zip(FEATURES, contributions)},
                'floor_adjustment_per_person': dict(zip(ITEMS, [max(0, floor - value) for floor, value in zip([3, 3, .02], outputs[15])])),
                'interpretation': 'Add contributions to the baseline, then apply planning floors. Baseline dependent, not causal.'}
