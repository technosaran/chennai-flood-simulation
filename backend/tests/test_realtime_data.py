from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
import json
import pytest
from backend.app.services.realtime_data import RealtimeDataService, parse_weather, parse_alerts, WEATHER_URL

NOW = datetime(2026, 10, 25, 6, tzinfo=timezone.utc)

def weather(now=NOW, rainfall=2):
    return json.dumps({'latitude':13.08,'longitude':80.27,'current_units':{'precipitation':'mm','wind_speed_10m':'km/h'},'hourly_units':{'precipitation':'mm'},'current':{'time':now.isoformat(),'temperature_2m':27,'relative_humidity_2m':80,'wind_speed_10m':10,'precipitation':.5,'interval':900},'hourly':{'time':[now.isoformat()], 'precipitation':[rainfall]}}).encode()

def alerts(now=NOW):
    date=format_datetime(now-timedelta(hours=1))
    return f'<rss><channel><item><title>Rain in Chennai</title><guid>one</guid><pubDate>{date}</pubDate><link>https://evil.example/</link></item><item><title>Rain in Delhi</title><pubDate>{date}</pubDate></item></channel></rss>'.encode()

def test_cache_read_and_startup_never_fetch(tmp_path):
    calls=[]
    service=RealtimeDataService(tmp_path/'cache.json',fetcher=lambda url:calls.append(url),clock=lambda:NOW)
    assert service.snapshot()['weather']['status']=='unavailable'
    assert calls==[]

def test_refresh_persists_and_throttles_independent_sources(tmp_path):
    calls=[]
    def fetch(url):
        calls.append(url)
        return weather() if url==WEATHER_URL else alerts()
    service=RealtimeDataService(tmp_path/'cache.json',fetcher=fetch,clock=lambda:NOW)
    result=service.refresh()
    assert result['weather']['data']['rainfall_mm_hr']==2
    assert result['alerts']['data']['matched_count']==1
    assert result['alerts']['data']['items'][0]['url']=='https://sachet.ndma.gov.in/'
    service.refresh()
    assert len(calls)==2
    restored=RealtimeDataService(tmp_path/'cache.json',fetcher=fetch,clock=lambda:NOW)
    assert restored.snapshot()['weather']['data']['rainfall_mm_hr']==2
    restored.refresh()
    assert len(calls)==2

def test_failed_refresh_retains_cache_and_marks_stale(tmp_path):
    clock=[NOW]
    def fetch(url):return weather() if url==WEATHER_URL else alerts()
    service=RealtimeDataService(tmp_path/'cache.json',fetcher=fetch,clock=lambda:clock[0])
    service.refresh()
    clock[0]+=timedelta(hours=2)
    def offline(url):raise OSError('offline')
    service.fetcher=offline
    result=service.refresh()
    assert result['weather']['status']=='stale'
    assert result['weather']['data']['rainfall_mm_hr']==2
    assert result['weather']['error']
    assert result['alerts']['error']

def test_alert_failure_does_not_discard_weather(tmp_path):
    def fetch(url):
        if url!=WEATHER_URL:raise OSError('offline')
        return weather()
    result=RealtimeDataService(tmp_path/'cache.json',fetcher=fetch,clock=lambda:NOW).refresh()
    assert result['weather']['status']=='fresh'
    assert result['alerts']['status']=='unavailable'
    assert result['alerts']['error']

def test_old_alerts_are_removed_and_invalid_weather_is_rejected():
    assert parse_alerts(alerts(NOW-timedelta(days=2)),NOW)['items']==[]
    with pytest.raises(ValueError):parse_weather(weather(rainfall=float('nan')),NOW)
    with pytest.raises(ValueError):parse_alerts(b'<!DOCTYPE rss [<!ENTITY x "bad">]><rss><channel/></rss>',NOW)

def test_offline_and_opt_in_api(client,tmp_path,monkeypatch):
    from backend.app.main import app
    calls=[]
    def fetch(url):
        calls.append(url)
        return weather() if url==WEATHER_URL else alerts()
    service=RealtimeDataService(tmp_path/'cache.json',fetcher=fetch,clock=lambda:NOW)
    monkeypatch.setattr(app.state,'realtime_data',service)
    assert client.get('/api/realtime/cache').status_code==200
    assert calls==[]
    assert client.post('/api/realtime/refresh').json()['weather']['status']=='fresh'
    assert len(calls)==2
