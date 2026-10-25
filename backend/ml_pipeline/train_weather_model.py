"""Train/select on past years, evaluate once on 2022–2025, export portable trees.

Run: python -m backend.ml_pipeline.train_weather_model
Targets are real gridded reanalysis rainfall, never synthetic flood labels.
"""
import csv
import argparse
import hashlib
import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
import numpy as np
import sklearn
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.metrics import (accuracy_score, balanced_accuracy_score, precision_score,
                             recall_score, f1_score, roc_auc_score, average_precision_score,
                             brier_score_loss, confusion_matrix)
from backend.app.services.weather_predictor import FEATURES, features, WeatherPredictor

ROOT = Path(__file__).parent


def samples(rows):
    x, y, dates = [], [], []
    for i in range(6, len(rows) - 1):
        if date.fromisoformat(rows[i+1]['date']) - date.fromisoformat(rows[i]['date']) != timedelta(days=1):
            raise ValueError('Nonconsecutive target')
        x.append(features(rows[i-6:i+1]))
        y.append(float(rows[i+1]['PRECTOTCORR']) >= 10)
        dates.append(rows[i+1]['date'])
    return np.array(x), np.array(y, dtype=int), np.array(dates)


def metrics(y, probabilities, threshold):
    predicted = probabilities >= threshold
    return dict(rows=len(y), positive_days=int(y.sum()), accuracy=accuracy_score(y, predicted),
                balanced_accuracy=balanced_accuracy_score(y, predicted),
                precision=precision_score(y, predicted, zero_division=0), recall=recall_score(y, predicted, zero_division=0),
                f1=f1_score(y, predicted, zero_division=0), roc_auc=roc_auc_score(y, probabilities),
                average_precision=average_precision_score(y, probabilities), brier_score=brier_score_loss(y, probabilities),
                confusion_matrix=confusion_matrix(y, predicted, labels=[0, 1]).tolist())


def train(objective='balanced_accuracy'):
    source = ROOT / 'dataset/chennai_nasa_power_daily.csv'
    with source.open(newline='', encoding='utf-8') as handle:
        rows = list(csv.DictReader(handle))
    x, y, dates = samples(rows)
    fitting = dates < '2019-01-01'
    validation = (dates >= '2019-01-01') & (dates < '2022-01-01')
    test = dates >= '2022-01-01'
    candidates = [
        ('Gradient boosting depth 2', GradientBoostingClassifier(n_estimators=180, max_depth=2, min_samples_leaf=25, learning_rate=.04, random_state=42)),
        ('Gradient boosting depth 3', GradientBoostingClassifier(n_estimators=200, max_depth=3, min_samples_leaf=25, learning_rate=.03, subsample=0.85, random_state=42)),
        ('Regularized gradient boosting', GradientBoostingClassifier(n_estimators=250, max_depth=3, min_samples_leaf=20, learning_rate=.025, subsample=0.80, random_state=42)),
        ('Random forest ensemble', RandomForestClassifier(n_estimators=200, max_depth=10, min_samples_leaf=12, n_jobs=-1, random_state=42)),
    ]
    results = []
    for name, estimator in candidates:
        estimator.fit(x[fitting], y[fitting])
        probs = estimator.predict_proba(x[validation])[:, 1]
        scorer = accuracy_score if objective == 'accuracy' else balanced_accuracy_score
        threshold = max(np.linspace(.05, .95, 181), key=lambda t: (scorer(y[validation], probs >= t), recall_score(y[validation], probs >= t, zero_division=0)))
        score = metrics(y[validation], probs, threshold)
        results.append((score[objective], -score['brier_score'], name, estimator, float(threshold), score))
        print(name, json.dumps(score), flush=True)
    _, _, name, estimator, threshold, _ = max(results, key=lambda row: row[:2])
    print(f"[*] Winning model selected on validation set: {name} with decision threshold {threshold:.4f}")
    # No refit on validation: its decision threshold remains tied to this model.
    artifact = dict(schema_version=1, name=name, features=list(FEATURES), rain_threshold_mm_day=10,
                    decision_threshold=threshold, dataset_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                    feature_ranges=np.stack([x[fitting].min(axis=0), x[fitting].max(axis=0)], axis=1).tolist(), trees=[])
    if isinstance(estimator, GradientBoostingClassifier):
        artifact.update(kind='gradient_boosting', initial_score=float(np.log(estimator.init_.class_prior_[1] / estimator.init_.class_prior_[0])), learning_rate=estimator.learning_rate)
        trees = [e[0] for e in estimator.estimators_]
    else:
        artifact['kind'] = 'random_forest'
        trees = estimator.estimators_
    for e in trees:
        t = e.tree_
        vals = t.value[:, 0, 0] if artifact['kind'] == 'gradient_boosting' else t.value[:, 0, 1] / t.value[:, 0, :].sum(axis=1)
        artifact['trees'].append(dict(left=t.children_left.tolist(), right=t.children_right.tolist(),
                                      feature=t.feature.tolist(), threshold=t.threshold.tolist(), value=vals.tolist()))
    model_path = ROOT / 'models/weather_classifier.json'
    model_path.write_text(json.dumps(artifact, separators=(',', ':'), allow_nan=False), encoding='utf-8')
    report = dict(generated_at=datetime.now(timezone.utc).isoformat(), model_name=name,
                  model_sha256=hashlib.sha256(model_path.read_bytes()).hexdigest(), dataset_sha256=artifact['dataset_sha256'],
                  sklearn_version=sklearn.__version__, seed=42, source='NASA POWER MERRA-2 gridded reanalysis',
                  target='Next-day rainfall >= 10 mm/day (project threshold, not an official flood threshold)',
                  features=list(FEATURES), tree_count=len(trees), decision_threshold=threshold,
                  split=dict(training=['2001-01-08', '2018-12-31'], validation=['2019-01-01', '2021-12-31'], test=['2022-01-01', '2025-12-31']),
                  training_rows=int(fitting.sum()), validation_rows=int(validation.sum()),
                  selection=f'Maximum validation {objective}; threshold selected on validation only. No test-driven selection/refit.',
                  selection_objective=objective,
                  validation_candidates={row[2]: dict(threshold=row[4], **row[5]) for row in results},
                  test=metrics(y[test], estimator.predict_proba(x[test])[:, 1], threshold),
                  baselines=dict(majority=metrics(y[test], np.zeros(test.sum()), .5),
                                 persistence=metrics(y[test], (x[test, 0] >= 10).astype(float), .5)),
                  limitations=['Reanalysis contains modeled and assimilated weather; not station ground truth.',
                               'Historical hindcast assumes completed prior-day data; publication latency is not modeled.',
                               'Rainfall classification is not flood occurrence, depth, extent, or relief-demand accuracy.',
                               'One grid point; severe events are rare. Probabilities are not independently calibrated.',
                               'Chronological holdout is used once; later project revisions must not tune against it.'])
    report_path = ROOT / 'models/weather_evaluation.json'
    report_path.write_text(json.dumps(report, indent=2, allow_nan=False), encoding='utf-8')
    portable = WeatherPredictor()
    if portable.model is None:
        raise RuntimeError(portable.load_error)
    actual = np.array([portable.probability(vals) for vals in x[test]])
    expected = estimator.predict_proba(x[test])[:, 1]
    assert np.max(np.abs(actual - expected)) < 1e-10, 'Portable runtime differs from training implementation'
    print(json.dumps({k: report[k] for k in ('model_name', 'training_rows', 'validation_rows', 'test', 'baselines')}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--objective', choices=['accuracy', 'balanced_accuracy'], default='balanced_accuracy')
    train(parser.parse_args().objective)
