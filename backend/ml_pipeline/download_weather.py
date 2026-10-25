"""Download and validate a reproducible Chennai NASA POWER daily dataset."""
import csv
import hashlib
import json
import math
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen

ROOT = Path(__file__).parent
PARAMETERS = ('PRECTOTCORR', 'T2M', 'RH2M', 'WS10M', 'PS')
DATASET = ROOT / 'dataset/chennai_nasa_power_daily.csv'


def download():
    params = dict(parameters=','.join(PARAMETERS), community='AG', longitude=80.2707,
                  latitude=13.0827, start='20010101', end='20251231', format='JSON',
                  **{'time-standard': 'UTC'})
    url = 'https://power.larc.nasa.gov/api/temporal/daily/point?' + urlencode(params)
    raw_path = ROOT / 'dataset/chennai_nasa_power_raw.json'
    if raw_path.exists():
        raw = raw_path.read_bytes()
    else:
        with urlopen(url, timeout=180) as response:
            raw = response.read()
    payload = json.loads(raw)
    values = payload['properties']['parameter']
    missing = payload['header'].get('fill_value', -999)
    rows = []
    day = date(2001, 1, 1)
    while day <= date(2025, 12, 31):
        key = day.strftime('%Y%m%d')
        row = [float(values[p][key]) for p in PARAMETERS]
        if any(not math.isfinite(v) or v == missing for v in row):
            raise ValueError(f'Missing data at {day}; refusing to invent measurements')
        if row[0] < 0 or not 0 <= row[2] <= 100 or row[3] < 0 or row[4] <= 0:
            raise ValueError(f'Invalid weather values at {day}')
        rows.append([day.isoformat(), *row])
        day += timedelta(days=1)
    raw_path.write_bytes(raw)
    with DATASET.open('w', newline='', encoding='utf-8') as handle:
        writer = csv.writer(handle)
        writer.writerow(['date', *PARAMETERS])
        writer.writerows(rows)
    manifest = dict(source='NASA POWER daily point API; CERES/MERRA-2 gridded reanalysis',
                    source_url=url, documentation='https://power.larc.nasa.gov/docs/services/api/temporal/daily/',
                    downloaded_at=datetime.now(timezone.utc).isoformat(), requested_coordinates=[13.0827, 80.2707],
                    returned_geometry=payload.get('geometry'), header=payload['header'],
                    parameters=payload['parameters'], rows=len(rows), start=rows[0][0], end=rows[-1][0],
                    time_standard='UTC', dataset_sha256=hashlib.sha256(DATASET.read_bytes()).hexdigest(),
                    raw_sha256=hashlib.sha256(raw).hexdigest(),
                    limitations='Gridded weather reanalysis, not a local rain gauge or observed flood/demand labels.')
    (ROOT / 'dataset/weather_manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print(json.dumps({k: manifest[k] for k in ('rows', 'start', 'end', 'dataset_sha256')}))


if __name__ == '__main__':
    download()
