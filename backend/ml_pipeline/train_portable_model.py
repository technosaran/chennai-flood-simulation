"""Train a portable, uncertainty-aware ensemble on the existing SYNTHETIC CSV.

Hold out the entire 2023 event for evaluation; split other events into training
and calibration. Metrics measure synthetic generalization, not real accuracy.
Run: python -m backend.ml_pipeline.train_portable_model
"""
import csv
import hashlib
import json
from pathlib import Path
import numpy as np
from sklearn.ensemble import ExtraTreesRegressor
from sklearn.model_selection import train_test_split
from backend.app.services.demand_predictor import DemandPredictor, FEATURES, ITEMS


def train():
    root = Path(__file__).parent
    source = root / "dataset/chennai_historical_2015_2023.csv"
    with source.open(newline="", encoding="utf-8") as f:
        rows = [r for r in csv.DictReader(f) if float(r["Shelter_Occupancy"]) > 0]
    x = np.array([[float(r[k]) for k in FEATURES] for r in rows])
    pop = np.array([float(r["Shelter_Occupancy"]) for r in rows])
    totals = np.array([[float(r[k]) for k in ("Target_Water_L", "Target_Food_Rations", "Target_MedKits")] for r in rows])
    y = totals / pop[:, None]
    test = np.array([i for i, r in enumerate(rows) if r["Year"] == "2023_Michaung"])
    other = np.array([i for i, r in enumerate(rows) if r["Year"] != "2023_Michaung"])
    fitting, calibration = train_test_split(other, test_size=0.25, random_state=42)
    forest = ExtraTreesRegressor(n_estimators=48, max_depth=8, min_samples_leaf=12,
                                random_state=42, n_jobs=1)
    forest.fit(x[fitting], y[fitting])
    floors = np.array([3, 3, 0.02])
    cal_predictions = np.maximum(floors, forest.predict(x[calibration]))
    scores = np.abs(y[calibration] - cal_predictions)
    # Finite sample split-conformal quantile, independently for each resource.
    level = min(1, np.ceil((len(calibration) + 1) * 0.90) / len(calibration))
    radius = np.quantile(scores, level, axis=0, method="higher")
    predicted = np.maximum(floors, forest.predict(x[test]))
    baseline = np.tile(floors, (len(test), 1))
    evaluation = {
        "holdout_event": "2023_Michaung", "training_rows": len(fitting),
        "calibration_rows": len(calibration), "test_rows": len(test),
        "source": "synthetic generated labels; no observed ground truth",
        "mae_units": dict(zip(ITEMS, np.mean(np.abs(predicted * pop[test, None] - totals[test]), axis=0).tolist())),
        "baseline_mae_units": dict(zip(ITEMS, np.mean(np.abs(baseline * pop[test, None] - totals[test]), axis=0).tolist())),
        "interval_coverage": dict(zip(ITEMS, np.mean(np.abs(y[test] - predicted) <= radius, axis=0).tolist())),
    }
    artifact = {
        "schema_version": 1, "features": list(FEATURES), "training_data": "synthetic",
        "dataset_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "feature_ranges": np.stack([x[fitting].min(axis=0), x[fitting].max(axis=0)], axis=1).tolist(),
        "nominal_coverage": 0.90, "conformal_radius_per_person": radius.tolist(),
        "evaluation": evaluation, "trees": [],
    }
    for estimator in forest.estimators_:
        t = estimator.tree_
        artifact["trees"].append({"left": t.children_left.tolist(), "right": t.children_right.tolist(),
                                  "feature": t.feature.tolist(), "threshold": t.threshold.tolist(),
                                  "value": t.value[:, :, 0].tolist()})
    output = root / "models/demand_forest.json"
    output.write_text(json.dumps(artifact, separators=(",", ":")), encoding="utf-8")
    # Verify the exact portable implementation against sklearn before shipping.
    portable = DemandPredictor(output)
    for idx in test[:100]:
        result = portable.predict_demand(*x[idx], int(pop[idx]))
        if result:
            expected = np.ceil(np.maximum(floors, forest.predict(x[idx:idx+1])[0]) * int(pop[idx]))
            assert all(result[k] == expected[i] for i, k in enumerate(ITEMS))
    (root / "models/demand_model_report.json").write_text(json.dumps(evaluation, indent=2), encoding="utf-8")
    print(json.dumps(evaluation, indent=2))


if __name__ == "__main__":
    train()
