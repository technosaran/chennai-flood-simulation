"""Opt-in recent weather/official RSS data; no downloads on startup or cache reads."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
import json
import math
from pathlib import Path
import os
import ssl
import tempfile
from threading import RLock
from urllib.parse import urlparse
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

WEATHER_URL = ('https://api.open-meteo.com/v1/forecast?latitude=13.0827&longitude=80.2707'
    '&current=temperature_2m,relative_humidity_2m,precipitation,rain,wind_speed_10m'
    '&hourly=precipitation&forecast_days=2&timezone=UTC')
ALERTS_URL = 'https://sachet.ndma.gov.in/cap_public_website/rss/rss_india.xml'
REFRESH_SECONDS = 300
MAX_BYTES = 3_000_000
UTC = timezone.utc


def timestamp(value):
    result = datetime.fromisoformat(value.replace('Z', '+00:00'))
    return result.replace(tzinfo=UTC) if result.tzinfo is None else result.astimezone(UTC)


class PlainText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
    def handle_data(self, data):
        self.parts.append(data)


def plain(value, limit=3000):
    parser = PlainText()
    parser.feed(value or '')
    return ' '.join(' '.join(parser.parts).split())[:limit]


def download(url):
    # Native system trust handles enterprise roots on Windows while preserving
    # hostname and certificate validation. Never use verify=False.
    try:
        import truststore
        context = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    except ImportError:
        context = ssl.create_default_context()
    request = Request(url, headers={'User-Agent': 'ChennaiFloodLab/1.0 (academic weather dashboard)'})
    with urlopen(request, context=context, timeout=12) as response:
        payload = response.read(MAX_BYTES+1)
    if len(payload) > MAX_BYTES:
        raise ValueError('Provider response exceeded the supported size')
    return payload


def number(value, low, high):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not low <= value <= high:
        raise ValueError('Invalid weather measurement')
    return float(value)


def parse_weather(payload, now):
    raw = json.loads(payload)
    current = raw['current']
    units = raw['current_units']
    if units.get('precipitation') != 'mm' or units.get('wind_speed_10m') != 'km/h' or raw['hourly_units'].get('precipitation') != 'mm':
        raise ValueError('Unexpected weather units')
    observed = timestamp(current['time'])
    if observed > now+timedelta(minutes=20):
        raise ValueError('Weather timestamp is in the future')
    times, amounts = raw['hourly']['time'], raw['hourly']['precipitation']
    if len(times) != len(amounts):
        raise ValueError('Incomplete hourly weather data')
    hourly = [(timestamp(t), number(p, 0, 2000)) for t, p in zip(times, amounts) if p is not None and timestamp(t) <= now]
    if not hourly:
        raise ValueError('No completed weather hour available')
    hour, rainfall = max(hourly, key=lambda item: item[0])
    return dict(location='Chennai', requested_location=[13.0827, 80.2707],
        grid_location=[number(raw['latitude'], -90, 90), number(raw['longitude'], -180, 180)],
        observed_at=observed.isoformat(), hourly_at=hour.isoformat(),
        temperature_c=number(current['temperature_2m'], -80, 70), humidity_pct=number(current['relative_humidity_2m'], 0, 100),
        wind_kmh=number(current['wind_speed_10m'], 0, 500),
        precipitation_mm=number(current['precipitation'], 0, 2000), interval_seconds=number(current['interval'], 60, 3600),
        hourly_precipitation_mm=rainfall, rainfall_mm_hr=rainfall,
        attribution='Open-Meteo weather model data (CC BY 4.0)', source_url='https://open-meteo.com/en/docs',
        interpretation='Current values are weather-model estimates, not a local rain-gauge observation. Hourly precipitation is the preceding-hour total; using it as a constant scenario intensity does not predict flood depth.')


def parse_alerts(payload, now):
    if b'<!DOCTYPE' in payload.upper() or b'<!ENTITY' in payload.upper():
        raise ValueError('Unsupported RSS declarations')
    root = ET.fromstring(payload)
    if root.tag.rsplit('}', 1)[-1] != 'rss' or root.find('channel') is None:
        raise ValueError('Expected the official RSS channel')
    items, seen = [], set()
    for item in root.findall('./channel/item'):
        title, description, author = (plain(item.findtext(key)) for key in ('title', 'description', 'author'))
        text = (title+' '+description+' '+author).casefold()
        if not any(word in text for word in ('chennai', 'tamil nadu', 'tamilnadu', 'tiruvallur', 'chengalpattu', 'kancheepuram', 'சென்னை', 'தமிழ்நாடு', 'தமிழ் நாடு')):
            continue
        try:
            published = parsedate_to_datetime(item.findtext('pubDate') or '')
            published = published.replace(tzinfo=UTC) if published.tzinfo is None else published.astimezone(UTC)
        except (ValueError, TypeError, OverflowError):
            continue
        if not now-timedelta(hours=24) <= published <= now+timedelta(minutes=5):
            continue
        identity = plain(item.findtext('guid') or title+published.isoformat(), 200)
        if identity in seen:
            continue
        seen.add(identity)
        link = item.findtext('link') or ''
        parsed = urlparse(link)
        if parsed.scheme != 'https' or parsed.hostname != 'sachet.ndma.gov.in':
            link = 'https://sachet.ndma.gov.in/'
        items.append(dict(id=identity, title=title, description=description, issuer=author,
                          issued_at=published.isoformat(), url=link))
    items.sort(key=lambda item: item['issued_at'], reverse=True)
    return dict(items=items[:20], matched_count=len(items), scope='Chennai / Tamil Nadu text matches, issued within the preceding 24 hours',
        source_url=ALERTS_URL, interpretation='Recent issued notices from the national NDMA SACHET RSS feed. RSS does not establish expiry or complete geographic coverage; these are not verified active Chennai warnings. Open the official notice for affected areas and validity.')


class RealtimeDataService:
    def __init__(self, path=None, fetcher=download, clock=None):
        self.path = Path(path) if path is not None else Path(__file__).parents[2]/'storage/realtime_cache.json'
        self.fetcher = fetcher
        self.clock = clock or (lambda: datetime.now(UTC))
        self.records, self.errors, self.attempted = {}, {}, {}
        self.lock = RLock()
        self.cache_warning = None
        try:
            saved = json.loads(self.path.read_text(encoding='utf-8'))
            # Revalidate cached provider payloads; corrupt local data never
            # becomes apparently fresh evidence after restart.
            now = self.clock()
            for key, parser in [('weather', parse_weather), ('alerts', parse_alerts)]:
                record = saved.get(key)
                if record and isinstance(record.get('payload'), str):
                    fetched = timestamp(record['fetched_at'])
                    if fetched <= now+timedelta(minutes=5):
                        data = parser(record['payload'].encode('utf-8'), now)
                        self.records[key] = dict(payload=record['payload'], fetched_at=fetched.isoformat(), data=data)
                        self.attempted[key] = fetched.isoformat()
        except (OSError, ValueError, KeyError, TypeError, ET.ParseError):
            pass

    def snapshot(self):
        with self.lock:
            now = self.clock()
            result = dict(checked_at=now.isoformat(), refresh_interval_seconds=REFRESH_SECONDS,
                          cache_warning=self.cache_warning, weather=None, alerts=None)
            for key in ('weather', 'alerts'):
                record = self.records.get(key)
                age = max(0, (now-timestamp(record['fetched_at'])).total_seconds()) if record else None
                stale = age is not None and age > 900
                data = record['data'] if record else None
                if key == 'weather' and data:
                    stale = stale or any((now-timestamp(data[field])).total_seconds() > 7200 for field in ('observed_at', 'hourly_at'))
                if key == 'alerts' and record:
                    data = parse_alerts(record['payload'].encode('utf-8'), now)
                result[key] = dict(status='unavailable' if not record else 'stale' if stale else 'fresh',
                    fetched_at=record['fetched_at'] if record else None, age_seconds=round(age) if age is not None else None,
                    error=self.errors.get(key), attempted_at=self.attempted.get(key), data=data)
            return result

    def refresh(self):
        with self.lock:
            now = self.clock()
            pending = [key for key in ('weather', 'alerts') if key not in self.attempted or (now-timestamp(self.attempted[key])).total_seconds() >= REFRESH_SECONDS]
            def load(key):
                url, parser = (WEATHER_URL, parse_weather) if key == 'weather' else (ALERTS_URL, parse_alerts)
                try:
                    raw = self.fetcher(url)
                    return key, dict(payload=raw.decode('utf-8-sig'), data=parser(raw, now), fetched_at=now.isoformat()), None
                except Exception as exc:
                    # Keep provider failures separate; a healthy weather source
                    # must remain usable if the official alert feed is down.
                    return key, None, 'Certificate validation failed' if 'CERTIFICATE_VERIFY_FAILED' in str(exc) else 'Provider unreachable or returned invalid data'
            if pending:
                with ThreadPoolExecutor(max_workers=2) as pool:
                    outcomes = list(pool.map(load, pending))
                for key, record, error in outcomes:
                    self.attempted[key] = now.isoformat()
                    if record:
                        self.records[key] = record
                    self.errors[key] = error
                self._save()
            return self.snapshot()

    def _save(self):
        temporary = None
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            fd, temporary = tempfile.mkstemp(dir=self.path.parent, suffix='.tmp')
            with os.fdopen(fd, 'w', encoding='utf-8') as stream:
                json.dump({key: dict(payload=value['payload'], fetched_at=value['fetched_at']) for key, value in self.records.items()}, stream, allow_nan=False)
            os.replace(temporary, self.path)
            self.cache_warning = None
        except OSError:
            self.cache_warning = 'Data is available in memory, but could not be cached on disk.'
        finally:
            if temporary and os.path.exists(temporary):
                os.unlink(temporary)
