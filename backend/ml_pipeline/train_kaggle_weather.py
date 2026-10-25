"""Download Chennai Kaggle data, validate, compare models, export verified inference.

python -m backend.ml_pipeline.train_kaggle_weather [--refresh]
Missing measurements are excluded, never replaced by dry-day labels.
"""
import argparse
import csv
import hashlib
import io
import json
import os
import tempfile
import urllib.request
import zipfile
from datetime import datetime, timedelta, date, timezone
from pathlib import Path

import numpy as np
from sklearn.ensemble import ExtraTreesClassifier, GradientBoostingClassifier, RandomForestClassifier
from backend.ml_pipeline.train_weather_model import metrics
from backend.app.services.kaggle_weather import FEATURES, ROOT, features, KaggleWeatherPredictor

SLUG = 'vanvalkenberg/historicalweatherdataforindiancities'
SOURCE = 'https://www.kaggle.com/datasets/' + SLUG


def atomic_write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(dir=path.parent, suffix='.tmp')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8', newline='') as stream:
            stream.write(content)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def download(refresh=False):
    path = ROOT / 'dataset/chennai_kaggle_daily.csv'
    if path.exists() and not refresh:
        return path
    request = urllib.request.Request('https://www.kaggle.com/api/v1/datasets/download/' + SLUG,
                                     headers={'User-Agent': 'ChennaiFloodLab/1.0'})
    with urllib.request.urlopen(request, timeout=90) as response:
        payload = response.read(20_000_001)
    if len(payload) > 20_000_000:
        raise ValueError('Unexpectedly large dataset download')
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        members = [entry for entry in archive.infolist() if entry.filename.endswith('/Chennai_1990_2022_Madras.csv')]
        if len(members) != 1 or members[0].file_size > 5_000_000:
            raise ValueError('Unexpected Kaggle archive layout')
        raw = archive.read(members[0]).decode('utf-8-sig')
    rows = list(csv.DictReader(io.StringIO(raw)))
    normalized, seen = [], set()
    for row in rows:
        day = datetime.strptime(row['time'], '%d-%m-%Y').date().isoformat()
        if day in seen:
            raise ValueError('Duplicate weather date: ' + day)
        seen.add(day)
        record = {'date': day}
        for key in ('tavg', 'prcp'):
            value = row[key].strip()
            if value and (not np.isfinite(float(value)) or (key == 'prcp' and float(value) < 0)):
                raise ValueError('Invalid ' + key + ' on ' + day)
            record[key] = value
        normalized.append(record)
    normalized.sort(key=lambda row: row['date'])
    output = io.StringIO(newline='')
    writer = csv.DictWriter(output, fieldnames=['date', 'tavg', 'prcp'])
    writer.writeheader()
    writer.writerows(normalized)
    atomic_write(path, output.getvalue())
    atomic_write(ROOT / 'dataset/kaggle_manifest.json', json.dumps(dict(
        source_url=SOURCE, dataset=SLUG, downloaded_at=datetime.now(timezone.utc).isoformat(),
        archive_sha256=hashlib.sha256(payload).hexdigest(),
        dataset_sha256=hashlib.sha256(path.read_bytes()).hexdigest(), rows=len(normalized),
        missing_temperature=sum(not r['tavg'] for r in normalized),
        missing_rainfall=sum(not r['prcp'] for r in normalized),
        provenance='Kaggle uploader weather archive; station provenance has not been independently audited.'), indent=2))
    return path


def samples(rows):
    x, y, days = [], [], []
    for i in range(6, len(rows) - 1):
        try:
            vector = features(rows[i-6:i+1])
            if date.fromisoformat(rows[i+1]['date']) - date.fromisoformat(rows[i]['date']) != timedelta(days=1):
                continue
            target = float(rows[i+1]['prcp'])
            if not np.isfinite(target) or target < 0:
                continue
        except (ValueError, KeyError):
            continue
        x.append(vector); y.append(int(target >= 10)); days.append(rows[i+1]['date'])
    return np.array(x), np.array(y), np.array(days)


def train(refresh=False, objective='accuracy'):
    path = download(refresh)
    with path.open(newline='', encoding='utf-8') as stream:
        rows = list(csv.DictReader(stream))
    x, y, days = samples(rows)
    # Eight-day embargo prevents raw history windows crossing split boundaries.
    fit = days < '2016-01-01'
    validation = (days >= '2016-01-09') & (days < '2021-01-01')
    test = days >= '2021-01-09'
    if any(mask.sum() < 100 or len(np.unique(y[mask])) != 2 for mask in (fit, validation, test)):
        raise ValueError('Insufficient complete records/classes in a chronological split')
    candidates = [
        ('Gradient boosting', GradientBoostingClassifier(n_estimators=220, max_depth=2, min_samples_leaf=25, learning_rate=.035, random_state=42)),
        ('Random forest', RandomForestClassifier(n_estimators=200, max_depth=10, min_samples_leaf=12, n_jobs=-1, random_state=42)),
        ('Extra Trees', ExtraTreesClassifier(n_estimators=250, max_depth=12, min_samples_leaf=10, n_jobs=-1, random_state=42)),
    ]
    results = []
    for name, estimator in candidates:
        estimator.fit(x[fit], y[fit])
        probabilities = estimator.predict_proba(x[validation])[:, 1]
        threshold = float(max(np.linspace(.05, .95, 181), key=lambda t: (metrics(y[validation], probabilities, t)[objective], metrics(y[validation], probabilities, t)['recall'])))
        score = metrics(y[validation], probabilities, threshold)
        results.append((name, estimator, threshold, score))
        print(name, json.dumps(score), flush=True)
    name, estimator, threshold, _ = max(results, key=lambda row: (row[3][objective], -row[3]['brier_score']))
    model = dict(schema_version=1, name=name, features=FEATURES, decision_threshold=threshold,
                 dataset_sha256=hashlib.sha256(path.read_bytes()).hexdigest(), trees=[])
    if isinstance(estimator, GradientBoostingClassifier):
        model.update(kind='gradient_boosting', initial_score=float(np.log(estimator.init_.class_prior_[1]/estimator.init_.class_prior_[0])), learning_rate=estimator.learning_rate)
        trees = [e[0] for e in estimator.estimators_]
    else:
        model['kind'] = 'random_forest'
        trees = estimator.estimators_
    for tree in trees:
        t = tree.tree_
        values = t.value[:, 0, 0] if model['kind'] == 'gradient_boosting' else t.value[:, 0, 1]/t.value[:, 0, :].sum(axis=1)
        model['trees'].append(dict(left=t.children_left.tolist(), right=t.children_right.tolist(), feature=t.feature.tolist(), threshold=t.threshold.tolist(), value=values.tolist()))
    # Verify portable inference BEFORE replacing the deployed bundle.
    portable = KaggleWeatherPredictor.__new__(KaggleWeatherPredictor)
    portable.model = model
    expected = estimator.predict_proba(x[test])[:, 1]
    actual = np.array([portable.probability(vector) for vector in x[test]])
    if np.max(np.abs(actual-expected)) > 1e-10:
        raise RuntimeError('Portable inference differs from trained model')
    report = dict(model_name=name, generated_at=datetime.now(timezone.utc).isoformat(), source_url=SOURCE,
                  model_sha256=hashlib.sha256(json.dumps(model, sort_keys=True).encode()).hexdigest(),
                  dataset_sha256=model['dataset_sha256'], total_rows=len(rows), usable_samples=len(y),
                  excluded_windows=len(rows)-7-len(y), training_rows=int(fit.sum()), validation_rows=int(validation.sum()),
                  split={'training': [str(days[fit][0]), str(days[fit][-1])], 'validation': [str(days[validation][0]), str(days[validation][-1])], 'test': [str(days[test][0]), str(days[test][-1])]},
                  selection=f'Validation {objective}, then Brier score; test excluded from selection. Eight-day split embargo.',
                  selection_objective=objective,
                  validation_candidates={n: dict(threshold=t, **s) for n, _, t, s in results},
                  test=metrics(y[test], expected, threshold),
                  baselines={'majority': metrics(y[test], np.zeros(test.sum()), .5), 'persistence': metrics(y[test], (x[test, 0] >= 10).astype(float), .5)},
                  limitations=['Uploader provenance not independently audited.', 'Missing measurement windows excluded; no zero-filled rainfall.', 'Historical next-day rainfall classification, not flood prediction or real relief-demand validation.', 'Fixed held-out years are an internal benchmark, not independent prospective validation.'])
    atomic_write(ROOT / 'models/kaggle_weather.json', json.dumps({'model': model, 'evaluation': report}, allow_nan=False, separators=(',', ':')))
    print(json.dumps(report, indent=2), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--refresh', action='store_true')
    parser.add_argument('--objective', choices=['accuracy', 'balanced_accuracy'], default='accuracy')
    args = parser.parse_args()
    train(args.refresh, args.objective)
