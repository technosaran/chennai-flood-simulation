"""Kaggle Chennai rainfall replay with fingerprint-verified portable inference."""
import csv
import hashlib
import json
import math
from datetime import date, timedelta
from pathlib import Path

from backend.app.services.weather_predictor import WeatherPredictor

ROOT = Path(__file__).parents[2] / 'ml_pipeline'
FEATURES = ['rain_today', 'rain_lag_1', 'rain_mean_3', 'rain_mean_7',
            'rain_max_7', 'temperature', 'season_sin', 'season_cos']


def features(history):
    if len(history) != 7:
        raise ValueError('Seven consecutive complete records are required')
    days = [date.fromisoformat(row['date']) for row in history]
    if any(b - a != timedelta(days=1) for a, b in zip(days, days[1:])):
        raise ValueError('History must be consecutive')
    rain = [float(row['prcp']) for row in history]
    temperatures = [float(row['tavg']) for row in history]
    if not all(math.isfinite(v) for v in rain + temperatures) or min(rain) < 0:
        raise ValueError('Invalid weather measurements')
    angle = 2 * math.pi * (days[-1] + timedelta(days=1)).timetuple().tm_yday / 365.25
    return [rain[-1], rain[-2], sum(rain[-3:])/3, sum(rain)/7,
            max(rain), temperatures[-1], math.sin(angle), math.cos(angle)]


class KaggleWeatherPredictor(WeatherPredictor):
    def __init__(self, root=ROOT):
        self.root, self.model, self.report, self.rows, self.load_error = Path(root), None, None, {}, None
        try:
            dataset = (self.root / 'dataset/chennai_kaggle_daily.csv').read_bytes()
            bundle = json.loads((self.root / 'models/kaggle_weather.json').read_text(encoding='utf-8'))
            model, report = bundle['model'], bundle['evaluation']
            digest = hashlib.sha256(dataset).hexdigest()
            model_digest = hashlib.sha256(json.dumps(model, sort_keys=True).encode()).hexdigest()
            if (model['features'] != FEATURES or model['schema_version'] != 1
                    or model['dataset_sha256'] != digest or report['model_sha256'] != model_digest
                    or report['dataset_sha256'] != digest):
                raise ValueError('Kaggle model, evaluation and dataset fingerprints do not match')
            with (self.root / 'dataset/chennai_kaggle_daily.csv').open(newline='', encoding='utf-8') as stream:
                self.rows = {row['date']: row for row in csv.DictReader(stream)}
            self.model, self.report = model, report
        except (OSError, KeyError, ValueError, TypeError) as exc:
            self.load_error = str(exc)

    def replay(self, as_of):
        day = date.fromisoformat(as_of)
        try:
            history = [self.rows[(day - timedelta(days=i)).isoformat()] for i in range(6, -1, -1)]
            probability = self.probability(features(history))
        except (KeyError, ValueError) as exc:
            raise ValueError('This date has missing measurements; choose another historical date') from exc
        target = (day + timedelta(days=1)).isoformat()
        observed = self.rows.get(target, {}).get('prcp')
        return dict(as_of=as_of, target_date=target, probability=probability,
                    decision_threshold=self.model['decision_threshold'],
                    elevated_rainfall=probability >= self.model['decision_threshold'],
                    actual_rainfall_mm_day=float(observed) if observed else None,
                    mode='historical_replay', model_name=self.model['name'],
                    interpretation='Next-day rainfall >= 10 mm/day; this is not flood probability.')
