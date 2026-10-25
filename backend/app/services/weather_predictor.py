"""Offline next-day rainfall classifier; inference needs only the standard library.

This is a historical reanalysis experiment, not a validated operational forecast.
"""
import csv
import hashlib
import json
import math
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).parents[2] / 'ml_pipeline'
PARAMETERS = ('PRECTOTCORR', 'T2M', 'RH2M', 'WS10M', 'PS')
FEATURES = (*PARAMETERS, 'rain_lag_1', 'rain_lag_2', 'rain_lag_6',
            'rain_mean_3', 'rain_mean_7', 'rain_max_7', 'season_sin', 'season_cos')


def features(history):
    if len(history) != 7:
        raise ValueError('Exactly seven consecutive daily records are required')
    days = [date.fromisoformat(row['date']) for row in history]
    if any(b - a != timedelta(days=1) for a, b in zip(days, days[1:])):
        raise ValueError('History must be ordered and consecutive')
    for row in history:
        vals = [float(row[p]) for p in PARAMETERS]
        if not all(math.isfinite(v) for v in vals) or vals[0] < 0 or not 0 <= vals[2] <= 100 or vals[3] < 0 or vals[4] <= 0:
            raise ValueError('Invalid weather values')
    rain = [float(row['PRECTOTCORR']) for row in history]
    angle = 2 * math.pi * (days[-1] + timedelta(days=1)).timetuple().tm_yday / 365.25
    return [float(history[-1][p]) for p in PARAMETERS] + [rain[-2], rain[-3], rain[0],
            sum(rain[-3:]) / 3, sum(rain) / 7, max(rain), math.sin(angle), math.cos(angle)]


def leaf(tree, values):
    node = 0
    while tree['left'][node] != -1:
        node = tree['left'][node] if values[tree['feature'][node]] <= tree['threshold'][node] else tree['right'][node]
    return tree['value'][node]


class WeatherPredictor:
    def __init__(self, root=ROOT):
        self.root = Path(root)
        self.model = None
        self.report = None
        self.rows = {}
        self.load_error = None
        try:
            raw = (self.root / 'models/weather_classifier.json').read_bytes()
            model = json.loads(raw)
            dataset = (self.root / 'dataset/chennai_nasa_power_daily.csv').read_bytes()
            report = json.loads((self.root / 'models/weather_evaluation.json').read_text())
            if model['features'] != list(FEATURES) or model['schema_version'] != 1:
                raise ValueError('Unsupported weather model schema')
            if (model['dataset_sha256'] != hashlib.sha256(dataset).hexdigest()
                    or report['model_sha256'] != hashlib.sha256(raw).hexdigest()
                    or report['dataset_sha256'] != model['dataset_sha256']):
                raise ValueError('Weather model/dataset/evaluation fingerprints do not match')
            self.model, self.report = model, report
            with (self.root / 'dataset/chennai_nasa_power_daily.csv').open(newline='', encoding='utf-8') as handle:
                self.rows = {r['date']: r for r in csv.DictReader(handle)}
        except (OSError, ValueError, TypeError, KeyError) as exc:
            self.model, self.report = None, None
            self.load_error = str(exc)

    def probability(self, values):
        model = self.model
        if model is None:
            raise ValueError('Weather model unavailable')
        import struct
        values = [struct.unpack('f', struct.pack('f', v))[0] for v in values]
        if model['kind'] == 'gradient_boosting':
            score = model['initial_score'] + model['learning_rate'] * sum(leaf(t, values) for t in model['trees'])
            return 1 / (1 + math.exp(-max(-700, min(700, score))))
        if model['kind'] == 'random_forest':
            # sklearn forests cast their inputs to float32; round identically.
            return sum(leaf(t, values) for t in model['trees']) / len(model['trees'])
        raise ValueError('Unsupported weather model kind')

    def predict(self, history):
        vals = features(history)
        probability = self.probability(vals)
        target = date.fromisoformat(history[-1]['date']) + timedelta(days=1)
        ranges = self.model['feature_ranges']
        outside = [name for name, val, (lo, hi) in zip(FEATURES, vals, ranges) if not lo <= val <= hi]
        return dict(as_of=history[-1]['date'], target_date=target.isoformat(),
                    rain_threshold_mm_day=self.model['rain_threshold_mm_day'],
                    probability=probability, decision_threshold=self.model['decision_threshold'],
                    elevated_rainfall=probability >= self.model['decision_threshold'],
                    outside_training_ranges=outside, model_name=self.model['name'],
                    interpretation='Probability of next-day gridded rainfall >= 10 mm; not flood probability or a live warning.')

    def replay(self, as_of):
        day = date.fromisoformat(as_of)
        try:
            history = [self.rows[(day - timedelta(days=i)).isoformat()] for i in range(6, -1, -1)]
        except KeyError as exc:
            raise ValueError('Date needs seven days of history within 2001-01-01 to 2025-12-31') from exc
        result = self.predict(history)
        observed = self.rows.get(result['target_date'])
        result['actual_rainfall_mm_day'] = float(observed['PRECTOTCORR']) if observed else None
        result['split'] = ('test' if result['target_date'] >= '2022-01-01' else 'validation' if result['target_date'] >= '2019-01-01' else 'training')
        if result['target_date'] > '2025-12-31':
            result['split'] = 'outside_evaluation'
        result['mode'] = 'historical_replay'
        result['history'] = history
        return result
