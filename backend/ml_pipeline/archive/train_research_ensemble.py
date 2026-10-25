"""Event-grouped model selection, portable blending, calibration and ablations.

Does not regenerate data. The 2023 event is never used to choose blend weights.
Run python -m backend.ml_pipeline.train_research_ensemble
"""
import csv
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
import numpy as np
from sklearn.ensemble import ExtraTreesRegressor, RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import GroupKFold, train_test_split
from sklearn.metrics import r2_score
from backend.app.services.demand_predictor import DemandPredictor, FEATURES, ITEMS

FLOORS = np.array([3., 3., .02])
NAMES = ['Extra Trees', 'Random Forest', 'Ridge']


def models():
    return [ExtraTreesRegressor(n_estimators=64, max_depth=10, min_samples_leaf=10, random_state=42, n_jobs=2),
            RandomForestRegressor(n_estimators=64, max_depth=10, min_samples_leaf=10, random_state=42, n_jobs=2),
            make_pipeline(StandardScaler(), Ridge(alpha=10.))]


def metrics(prediction, actual, population):
    totals = np.ceil(np.maximum(FLOORS, prediction) * population[:, None])
    targets = actual * population[:, None]
    return {'mae_units': dict(zip(ITEMS, np.mean(abs(totals - targets), axis=0).tolist())),
            'rmse_units': dict(zip(ITEMS, np.sqrt(np.mean((totals - targets) ** 2, axis=0)).tolist())),
            'r2': dict(zip(ITEMS, r2_score(targets, totals, multioutput='raw_values').tolist()))}


def train():
    started = perf_counter()
    root = Path(__file__).parent
    source = root / 'dataset/chennai_historical_2015_2023.csv'
    with source.open(newline='', encoding='utf-8') as f:
        rows = [r for r in csv.DictReader(f) if float(r['Shelter_Occupancy']) > 0]
    x = np.array([[float(r[k]) for k in FEATURES] for r in rows])
    pop = np.array([int(float(r['Shelter_Occupancy'])) for r in rows])
    y = np.array([[float(r[k]) for k in ['Target_Water_L', 'Target_Food_Rations', 'Target_MedKits']] for r in rows]) / pop[:, None]
    events = np.array([r['Year'] for r in rows])
    test = np.flatnonzero(events == '2023_Michaung')
    other = np.flatnonzero(events != '2023_Michaung')
    fit, cal = train_test_split(other, test_size=.25, random_state=42, stratify=events[other])
    oof = np.zeros((len(fit), 3, 3))
    fold_reports = []
    cv = GroupKFold(n_splits=len(set(events[fit])))
    for fold, (training, validation) in enumerate(cv.split(x[fit], y[fit], events[fit])):
        fold_metrics = {}
        for i, model in enumerate(models()):
            model.fit(x[fit[training]], y[fit[training]])
            prediction = model.predict(x[fit[validation]])
            oof[validation, i, :] = prediction
            fold_metrics[NAMES[i]] = metrics(prediction, y[fit[validation]], pop[fit[validation]])
        fold_reports.append({'held_out_events': sorted(set(events[fit[validation]])), 'rows': len(validation), 'models': fold_metrics})
        print('Completed event fold', fold + 1, flush=True)
    # Per-resource convex simplex search on out-of-event predictions only.
    grid = [np.array([a, b, 10-a-b]) / 10 for a in range(11) for b in range(11-a)]
    weights = []
    for resource in range(3):
        best = min(grid, key=lambda w: np.mean(abs(np.maximum(FLOORS[resource], oof[:, :, resource] @ w) - y[fit, resource])))
        weights.append(best)
    weights = np.array(weights)
    trained = models()
    for model in trained:
        model.fit(x[fit], y[fit])
    def blended(values):
        predictions = np.stack([model.predict(values) for model in trained], axis=1)
        return np.einsum('nmo,om->no', predictions, weights)
    cal_scores = abs(y[cal] - np.maximum(FLOORS, blended(x[cal])))
    level = min(1, math.ceil((len(cal) + 1) * .9) / len(cal))
    radius = np.quantile(cal_scores, level, axis=0, method='higher')
    prediction = blended(x[test])
    report = {'holdout_event': '2023_Michaung', 'training_rows': len(fit), 'calibration_rows': len(cal), 'test_rows': len(test),
              'total_dataset_rows': len(rows), 'source': 'synthetic labels; no observed ground truth',
              'selection': 'Per-resource convex weights selected on GroupKFold out-of-event predictions; calibration and final holdout excluded.',
              'cross_validation': fold_reports,
              'component_weights': {item: dict(zip(NAMES, row.tolist())) for item, row in zip(ITEMS, weights)},
              'candidate_holdout': {name: metrics(model.predict(x[test]), y[test], pop[test]) for name, model in zip(NAMES, trained)},
              'blend_holdout': metrics(prediction, y[test], pop[test]),
              'baseline_mae_units': metrics(np.tile(FLOORS, (len(test), 1)), y[test], pop[test])['mae_units'],
              'mae_units': metrics(prediction, y[test], pop[test])['mae_units'],
              'interval_coverage': dict(zip(ITEMS, np.mean(abs(y[test] - np.maximum(FLOORS, prediction)) <= radius, axis=0).tolist()))}
    old = DemandPredictor(root / 'models/demand_forest.json')
    old_pred = np.array([old._predict_per_person(tuple(values)) for values in x[test]])
    report['previous_model_holdout'] = metrics(old_pred, y[test], pop[test])
    # Post-selection importance analysis on holdout, not used to tune weights.
    rng = np.random.default_rng(42)
    original_mae = np.mean(abs(np.maximum(FLOORS, prediction) - y[test]), axis=0)
    importance = {}
    for j, feature in enumerate(FEATURES):
        changed = x[test].copy()
        changed[:, j] = rng.permutation(changed[:, j])
        importance[feature] = dict(zip(ITEMS, (np.mean(abs(np.maximum(FLOORS, blended(changed)) - y[test]), axis=0) - original_mae).tolist()))
    report['permutation_mae_increase_per_person'] = importance
    scaler, ridge = trained[2].steps[0][1], trained[2].steps[1][1]
    coefficients = ridge.coef_ / scaler.scale_[None, :]
    artifact = {'schema_version': 2, 'name': 'Event-CV blend: Extra Trees + Random Forest + Ridge / conformal',
                'features': list(FEATURES), 'components': NAMES, 'component_weights': weights.tolist(),
                'linear': {'coef': coefficients.tolist(), 'intercept': (ridge.intercept_ - coefficients @ scaler.mean_).tolist()},
                'training_data': 'synthetic', 'dataset_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
                'feature_ranges': np.stack([x[fit].min(axis=0), x[fit].max(axis=0)], axis=1).tolist(),
                'reference': np.median(x[fit], axis=0).tolist(), 'nominal_coverage': .9,
                'conformal_radius_per_person': radius.tolist(), 'evaluation': report, 'trees': []}
    for component, model in enumerate(trained[:2]):
        for estimator in model.estimators_:
            t = estimator.tree_
            artifact['trees'].append({'component': component, 'left': t.children_left.tolist(), 'right': t.children_right.tolist(),
                                      'feature': t.feature.tolist(), 'threshold': t.threshold.tolist(), 'value': t.value[:, :, 0].tolist()})
    path = root / 'models/demand_ensemble_v2.json'
    path.write_text(json.dumps(artifact, separators=(',', ':')), encoding='utf-8')
    portable = DemandPredictor(path)
    if not portable.is_loaded:
        raise RuntimeError(portable.load_error)
    indices = np.linspace(0, len(test) - 1, 250, dtype=int)
    for index in indices:
        actual = portable._predict_per_person(tuple(x[test[index]]))
        assert np.allclose(actual, prediction[index], atol=1e-9), (actual, prediction[index])
    report['portable_parity_rows'] = len(indices)
    report['training_seconds'] = round(perf_counter() - started, 2)
    report['generated_at'] = datetime.now(timezone.utc).isoformat()
    (root / 'models/research_benchmark.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({k: report[k] for k in ['component_weights', 'mae_units', 'previous_model_holdout', 'training_seconds']}, indent=2))


if __name__ == '__main__':
    train()
