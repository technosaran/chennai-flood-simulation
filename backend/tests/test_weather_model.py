import shutil
from backend.app.services.weather_predictor import WeatherPredictor, features, ROOT


def test_real_dataset_and_chronological_holdout_integrity():
    model = WeatherPredictor()
    assert model.model is not None, model.load_error
    assert len(model.rows) == 9131
    report = model.report
    assert report['test']['rows'] == 1461
    assert report['split']['training'][1] < report['split']['validation'][0]
    assert report['split']['validation'][1] < report['split']['test'][0]
    assert report['test']['balanced_accuracy'] > report['baselines']['persistence']['balanced_accuracy']


def test_features_do_not_use_next_day_measurements():
    model = WeatherPredictor()
    result = model.replay('2023-12-03')
    before = features(result['history'])
    model.rows['2023-12-04']['PRECTOTCORR'] = '1999'
    assert features(result['history']) == before
    assert model.replay('2023-12-03')['probability'] == result['probability']


def test_stale_weather_evidence_is_rejected(tmp_path):
    for folder in ('models', 'dataset'):
        (tmp_path / folder).mkdir()
    for name in ('models/weather_classifier.json', 'models/weather_evaluation.json', 'dataset/chennai_nasa_power_daily.csv'):
        shutil.copyfile(ROOT / name, tmp_path / name)
    with (tmp_path / 'dataset/chennai_nasa_power_daily.csv').open('a') as handle:
        handle.write('\n')
    assert WeatherPredictor(tmp_path).model is None


def test_weather_endpoints_and_invalid_history(client):
    response = client.get('/api/weather/evaluation')
    assert response.status_code == 200
    assert response.json()['evaluation_status'] == 'verified'
    replay = client.get('/api/weather/prediction', params={'as_of': '2023-12-03'})
    assert replay.status_code == 200
    result = replay.json()
    assert result['split'] == 'test'
    assert result['target_date'] == '2023-12-04'
    assert 0 <= result['probability'] <= 1
    assert result['actual_rainfall_mm_day'] is not None
    custom = client.post('/api/weather/predict', json={'history': result['history']})
    assert custom.status_code == 200
    assert custom.json()['probability'] == result['probability']
    history = result['history']
    history[1]['date'] = history[0]['date']
    assert client.post('/api/weather/predict', json={'history': history}).status_code == 422
    assert client.post('/api/weather/predict', json={'history': []}).status_code == 422
    assert client.get('/api/weather/prediction?as_of=2030-01-01').status_code == 422


def test_replay_split_uses_target_date():
    # Splits are assigned by target, not feature date, at year boundaries.
    assert WeatherPredictor().replay('2021-12-31')['split'] == 'test'


def test_portable_test_confusion_matches_saved_report():
    model = WeatherPredictor()
    matrix = [[0, 0], [0, 0]]
    for target in model.rows:
        if '2022-01-01' <= target <= '2025-12-31':
            from datetime import date, timedelta
            previous = (date.fromisoformat(target) - timedelta(days=1)).isoformat()
            result = model.replay(previous)
            actual = int(result['actual_rainfall_mm_day'] >= 10)
            matrix[actual][int(result['elevated_rainfall'])] += 1
    assert matrix == model.report['test']['confusion_matrix']
