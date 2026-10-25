"""Evaluate the shipped runtime, including rule fallbacks, on held-out rows.

Run from the repository root. Requires only the Python standard library.
Synthetic label errors are not observed flood forecasting accuracy.
"""
import csv
import hashlib
import json
import math
import statistics
import time
from datetime import datetime, timezone
from pathlib import Path

from backend.app.services.demand_predictor import DemandPredictor, FEATURES, ITEMS


def evaluate():
    root = Path(__file__).parent
    source = root / "dataset/chennai_historical_2015_2023.csv"
    model = DemandPredictor()
    if not model.is_loaded:
        raise RuntimeError(model.load_error)
    if hashlib.sha256(source.read_bytes()).hexdigest() != model.model.get("dataset_sha256"):
        raise RuntimeError("Dataset does not match the shipped model provenance")
    with source.open(newline="", encoding="utf-8") as handle:
        rows = [r for r in csv.DictReader(handle) if r["Year"] == "2023_Michaung" and float(r["Shelter_Occupancy"]) > 0]
    errors, baseline_errors, covered = [0.] * 3, [0.] * 3, [0] * 3
    ml_count = 0
    started = time.perf_counter()
    for row in rows:
        pop = int(float(row["Shelter_Occupancy"]))
        features = [float(row[key]) for key in FEATURES]
        prediction = model.predict_demand(*features, pop)
        baseline = dict(zip(ITEMS, [pop * 3, pop * 3, max(10, math.ceil(pop * .02))]))
        if prediction:
            ml_count += 1
        actual = [float(row[k]) for k in ("Target_Water_L", "Target_Food_Rations", "Target_MedKits")]
        for i, key in enumerate(ITEMS):
            errors[i] += abs((prediction or baseline)[key] - actual[i])
            baseline_errors[i] += abs(baseline[key] - actual[i])
            if prediction:
                bounds = prediction["prediction_intervals"][key]
                covered[i] += bounds["lower"] <= actual[i] <= bounds["upper"]
    elapsed = time.perf_counter() - started
    # Compare repeated conditions at changing occupancy with and without cache.
    conditions = [90., 1., 20000., .85]
    timing = {}
    for cached in (False, True):
        samples = []
        for n in range(1000):
            if not cached:
                model._predict_per_person.cache_clear()
            start = time.perf_counter()
            model.predict_demand(*conditions, 100 + n)
            samples.append((time.perf_counter() - start) * 1000)
        timing["cached" if cached else "uncached"] = {
            "median_ms": statistics.median(samples), "p95_ms": sorted(samples)[949],
        }
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "model_sha256": model.model_sha256,
        "artifact_name": model.path.name,
        "dataset_sha256": model.model["dataset_sha256"],
        "source": "synthetic held-out labels; not real-world accuracy",
        "holdout_event": "2023_Michaung", "rows": len(rows), "tree_count": len(model.model["trees"]),
        "ml_rows": ml_count, "rule_fallback_rows": len(rows) - ml_count,
        "runtime_mae_units": dict(zip(ITEMS, [v / len(rows) for v in errors])),
        "runtime_baseline_mae_units": dict(zip(ITEMS, [v / len(rows) for v in baseline_errors])),
        "interval_coverage_ml_rows": dict(zip(ITEMS, [v / ml_count if ml_count else None for v in covered])),
        "evaluation_seconds": elapsed, "repeated_conditions_inference": timing,
    }


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--save", action="store_true", help="Save verified runtime metrics for the review dashboard")
    args = parser.parse_args()
    report = evaluate()
    if args.save:
        (Path(__file__).parent / "models/runtime_evaluation.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
