import json
from types import SimpleNamespace

import pytest

from backend.app.services.demand_predictor import DemandPredictor, FEATURES, ITEMS
from backend.app.services.road_network import RoadNetworkEngine
from backend.app.services.supply_solver import SupplyChainSolver


def small_model():
    return {
        "schema_version": 1, "features": list(FEATURES),
        "feature_ranges": [[0, 500], [0, 5], [0, 50000], [0, 1]],
        "nominal_coverage": .9, "conformal_radius_per_person": [.2, .2, .01],
        "trees": [{"left": [-1], "right": [-1], "feature": [-2],
                   "threshold": [-2.], "value": [[4., 3.5, .04]]}],
    }


@pytest.mark.parametrize("corruption", ["missing_calibration", "cyclic_tree", "invalid_leaf", "invalid_ranges"])
def test_malformed_model_uses_rules_instead_of_crashing(tmp_path, corruption):
    artifact = small_model()
    if corruption == "missing_calibration":
        del artifact["conformal_radius_per_person"]
    elif corruption == "cyclic_tree":
        artifact["trees"][0]["left"][0] = 0
    elif corruption == "invalid_leaf":
        artifact["trees"][0]["value"][0] = [float("nan"), 3, 1]
    else:
        artifact["feature_ranges"] = [[0, 500]]
    path = tmp_path / "model.json"
    path.write_text(json.dumps(artifact))
    model = DemandPredictor(path)
    assert not model.is_loaded
    assert model.load_error
    assert model.predict_demand(90, 1, 20000, .9, 100) is None


def test_cached_conditions_scale_with_headcount_and_return_fresh_intervals(tmp_path):
    path = tmp_path / "model.json"
    path.write_text(json.dumps(small_model()))
    model = DemandPredictor(path)
    model._predict_per_person.cache_clear()
    one = model.predict_demand(90, 1, 20000, .9, 100)
    two = model.predict_demand(90, 1, 20000, .9, 200)
    assert model._predict_per_person.cache_info().hits == 1
    for item in ITEMS:
        assert two[item] == 2 * one[item]
    one["prediction_intervals"]["water_litres"]["upper"] = -1
    assert model.predict_demand(90, 1, 20000, .9, 100)["prediction_intervals"]["water_litres"]["upper"] > 0
    assert all(model.predict_demand(90, 1, 20000, .9, 0)[item] == 0 for item in ITEMS)


def test_extreme_vulnerability_reaches_demand_model():
    class RecordingModel:
        is_loaded = True
        def predict_demand(self, **kwargs):
            self.inputs = kwargs
            return None
    road = RoadNetworkEngine()
    road.population_clusters = [{"location": [13., 80.2], "risk_level": "Extreme", "density_per_sqkm": 20000}]
    model = RecordingModel()
    solver = SupplyChainSolver(road, ml_predictor=model)
    point = next(iter(solver.point_demands))
    solver.update_demands_from_evacuees({point: 100}, SimpleNamespace(rainfall_intensity_mm_hr=90), [{"type": "circle", "center": [13., 80.2], "radius_meters": 2000, "depth_meters": 1.}])
    assert model.inputs["vulnerability"] == .99


def test_empty_shelter_does_not_consume_medical_stock():
    solver = SupplyChainSolver(RoadNetworkEngine())
    point = next(iter(solver.point_demands))
    solver.update_demands_from_evacuees({point: 0})
    assert all(solver.point_demands[point]["demand"][item] == 0 for item in ITEMS)
