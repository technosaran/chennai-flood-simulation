"""Reproduce the advanced portable demand ensemble. Labels remain synthetic.

Select convex blend weights using leave-event-out predictions on fitting rows.
Calibration and the entire 2023 group are excluded from model selection.
"""
import csv
import hashlib
import json
from pathlib import Path
import numpy as np
from sklearn.ensemble import ExtraTreesRegressor, RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.model_selection import GroupKFold, train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, r2_score
from backend.app.services.demand_predictor import DemandPredictor, FEATURES, ITEMS

ROOT = Path(__file__).parent
FLOORS = np.array([3., 3., .02])


def estimators():
    return [
        ExtraTreesRegressor(n_estimators=80, max_depth=11, min_samples_leaf=8, random_state=42, n_jobs=-1),
        RandomForestRegressor(n_estimators=80, max_depth=11, min_samples_leaf=8, random_state=42, n_jobs=-1),
        make_pipeline(StandardScaler(), Ridge(alpha=0.5))
    ]


def train():
    source = ROOT / 'dataset/chennai_historical_2015_2023.csv'
    with source.open(newline='', encoding='utf-8') as handle:
        rows = [r for r in csv.DictReader(handle) if float(r['Shelter_Occupancy']) > 0]
    x = np.array([[float(r[k]) for k in FEATURES] for r in rows])
    pop = np.array([float(r['Shelter_Occupancy']) for r in rows])
    totals = np.array([[float(r[k]) for k in ('Target_Water_L', 'Target_Food_Rations', 'Target_MedKits')] for r in rows])
    y = totals / pop[:, None]
    groups = np.array([r['Year'] for r in rows])
    test = np.flatnonzero(groups == '2023_Michaung')
    fitting, calibration = train_test_split(np.flatnonzero(groups != '2023_Michaung'), test_size=.25, random_state=42)
    print(f"[*] Dataset: {len(rows):,} total rows | Fitting: {len(fitting):,} | Calibration: {len(calibration):,} | Test (2023_Michaung): {len(test):,}")

    out_of_fold = np.zeros((len(fitting), 3, 3))
    folds = []
    n_splits = len(set(groups[fitting]))
    print(f"[*] Running leave-event-out GroupKFold with {n_splits} event splits...")
    for train_ids, val_ids in GroupKFold(n_splits=n_splits).split(x[fitting], groups=groups[fitting]):
        fold = {'held_out_events': sorted(set(groups[fitting[val_ids]])), 'rows': len(val_ids)}
        for k, estimator in enumerate(estimators()):
            estimator.fit(x[fitting[train_ids]], y[fitting[train_ids]])
            out_of_fold[val_ids, k] = estimator.predict(x[fitting[val_ids]])
        folds.append(fold)
        print('    Completed event fold:', fold, flush=True)

    # High-resolution convex simplex grid (step=0.025, 861 candidate blends per resource)
    candidates = np.array([[a/40, b/40, (40-a-b)/40] for a in range(41) for b in range(41-a)])
    weights = []
    for item in range(3):
        # Vectorized candidate evaluation across all 861 combinations
        # shape: (N_fitting, 861)
        matrix = out_of_fold[:, :, item] @ candidates.T
        clipped = np.maximum(FLOORS[item], matrix)
        candidate_errors = np.mean(np.abs(clipped - y[fitting, item, None]) * pop[fitting, None], axis=0)
        best_w = candidates[np.argmin(candidate_errors)]
        weights.append(best_w)
        print(f"    Optimized blend for {ITEMS[item]}: ExtraTrees={best_w[0]:.3f}, RF={best_w[1]:.3f}, Ridge={best_w[2]:.3f}")

    weights = np.array(weights)
    models = estimators()
    print("[*] Fitting final models on complete fitting partition...")
    for model in models:
        model.fit(x[fitting], y[fitting])

    def predict(ids):
        components = np.stack([m.predict(x[ids]) for m in models], axis=1)
        return np.maximum(FLOORS, np.einsum('nki,ik->ni', components, weights))

    scores = np.abs(y[calibration] - predict(calibration))
    quantile = min(1, np.ceil((len(calibration)+1)*.9) / len(calibration))
    radius = np.quantile(scores, quantile, axis=0, method='higher')
    scaler, ridge = models[2].steps[0][1], models[2].steps[1][1]
    coef = ridge.coef_ / scaler.scale_
    intercept = ridge.intercept_ - coef @ scaler.mean_
    predicted = predict(test)
    report = dict(holdout_event='2023_Michaung', training_rows=len(fitting), calibration_rows=len(calibration), test_rows=len(test),
                  source='synthetic labels; no observed flood or relief ground truth',
                  selection='Convex weights selected using GroupKFold out-of-event predictions on fitting rows only.',
                  cross_validation=folds, component_weights=weights.tolist(),
                  mae_units=dict(zip(ITEMS, mean_absolute_error(totals[test], predicted * pop[test, None], multioutput='raw_values').tolist())),
                  r2=dict(zip(ITEMS, r2_score(totals[test], predicted * pop[test, None], multioutput='raw_values').tolist())),
                  baseline_mae_units=dict(zip(ITEMS, np.mean(np.abs(totals[test] - FLOORS * pop[test, None]), axis=0).tolist())),
                  interval_coverage=dict(zip(ITEMS, np.mean(np.abs(y[test] - predicted) <= radius, axis=0).tolist())))
    artifact = dict(schema_version=2, name='Event-CV blend: Extra Trees + Random Forest + Ridge / conformal',
                    features=list(FEATURES), components=['Extra Trees', 'Random Forest', 'Ridge'],
                    component_weights=weights.tolist(), linear=dict(coef=coef.tolist(), intercept=intercept.tolist()),
                    training_data='synthetic', dataset_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                    feature_ranges=np.stack([x[fitting].min(axis=0), x[fitting].max(axis=0)], axis=1).tolist(),
                    reference=np.median(x[fitting], axis=0).tolist(), nominal_coverage=.9,
                    conformal_radius_per_person=radius.tolist(), evaluation=report, trees=[])
    for component, forest in enumerate(models[:2]):
        for estimator in forest.estimators_:
            t = estimator.tree_
            artifact['trees'].append(dict(component=component, left=t.children_left.tolist(), right=t.children_right.tolist(),
                                          feature=t.feature.tolist(), threshold=t.threshold.tolist(), value=t.value[:, :, 0].tolist()))
    path = ROOT / 'models/demand_ensemble_v2.json'
    path.write_text(json.dumps(artifact, separators=(',', ':'), allow_nan=False), encoding='utf-8')
    runtime = DemandPredictor(path)
    assert runtime.is_loaded, runtime.load_error
    for idx in test[:200]:
        result = runtime.predict_demand(*x[idx], int(pop[idx]))
        if result:
            expected = np.ceil(predict([idx])[0] * int(pop[idx]))
            assert all(result[key] == expected[i] for i, key in enumerate(ITEMS))
    (ROOT / 'models/demand_model_report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print("[+] Evaluation report:")
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    train()
