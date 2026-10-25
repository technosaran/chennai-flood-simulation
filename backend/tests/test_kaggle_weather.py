import csv
import shutil
from datetime import date, timedelta

import pytest
from backend.app.services.kaggle_weather import KaggleWeatherPredictor, ROOT, features


def test_kaggle_bundle_has_chronological_evidence():
    model = KaggleWeatherPredictor()
    assert model.model is not None, model.load_error
    report = model.report
    assert report['training_rows'] > 1000
    assert report['split']['training'][1] < report['split']['validation'][0]
    assert report['split']['validation'][1] < report['split']['test'][0]
    assert len(report['validation_candidates']) == 3
    assert report['excluded_windows'] > 0


def test_missing_measurements_are_not_dry_days():
    history = [{'date': (date(2020, 1, 1) + timedelta(days=i)).isoformat(), 'tavg': '27', 'prcp': '0'} for i in range(7)]
    assert features(history)[0] == 0
    history[-1]['prcp'] = ''
    with pytest.raises(ValueError):
        features(history)


def test_kaggle_features_reject_gaps():
    history = [{'date': '2020-01-01', 'tavg': '27', 'prcp': '0'} for _ in range(7)]
    with pytest.raises(ValueError, match='consecutive'):
        features(history)


def test_stale_kaggle_bundle_is_rejected(tmp_path):
    for folder, filename in [('dataset', 'chennai_kaggle_daily.csv'), ('models', 'kaggle_weather.json')]:
        (tmp_path / folder).mkdir()
        shutil.copyfile(ROOT / folder / filename, tmp_path / folder / filename)
    with (tmp_path / 'dataset/chennai_kaggle_daily.csv').open('a') as stream:
        stream.write('\n')
    assert KaggleWeatherPredictor(tmp_path).model is None


def test_kaggle_api_and_missing_date(client):
    evidence = client.get('/api/weather/kaggle/evaluation')
    assert evidence.status_code == 200
    assert evidence.json()['evaluation_status'] == 'verified'
    result = client.get('/api/weather/kaggle/prediction?as_of=2021-11-06')
    assert result.status_code == 200, result.text
    assert 0 <= result.json()['probability'] <= 1
    assert result.json()['target_date'] == '2021-11-07'
    assert client.get('/api/weather/kaggle/prediction?as_of=2030-01-01').status_code == 422


def test_kaggle_runtime_matches_report():
    model = KaggleWeatherPredictor()
    matrix = [[0, 0], [0, 0]]
    start, end = model.report['split']['test']
    for target, row in model.rows.items():
        if not start <= target <= end or not row['prcp']:
            continue
        try:
            result = model.replay((date.fromisoformat(target) - timedelta(days=1)).isoformat())
        except ValueError:
            continue
        matrix[int(float(row['prcp']) >= 10)][int(result['elevated_rainfall'])] += 1
    assert matrix == model.report['test']['confusion_matrix']
