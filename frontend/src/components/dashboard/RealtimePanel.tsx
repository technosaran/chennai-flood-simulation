'use client';
import { useEffect, useState } from 'react';
import { canApplyWeather, type RealtimeSnapshot } from '@/lib/realtime';

const time = (value: string | null) => value ? new Date(value).toLocaleString('en-IN', { timeZone: 'Asia/Kolkata', dateStyle: 'medium', timeStyle: 'short' })+' IST' : 'Never downloaded';
export default function RealtimePanel({ enabled, snapshot, loading, error, onRefresh, onApplyRainfall, busy, savedView }: {
  enabled: boolean; snapshot: RealtimeSnapshot | null; loading: boolean; error: string; onRefresh: () => void;
  onApplyRainfall: (rate: number) => void; busy: boolean; savedView: boolean;
}) {
  const [now, setNow] = useState(Date.now());
  useEffect(() => { const timer = window.setInterval(() => setNow(Date.now()), 30000); return () => window.clearInterval(timer); }, []);
  const weather = snapshot?.weather;
  const alerts = snapshot?.alerts;
  const canApply = enabled && !error && canApplyWeather(weather, now) && !busy && !savedView;
  const status = (kind: 'weather' | 'alerts') => {
    const source = snapshot?.[kind];
    if (!source?.data) return 'Unavailable';
    if (!enabled) return 'Saved snapshot · offline mode';
    if (error || source.error) return 'Connection failed · saved snapshot';
    if (source.status === 'stale' || !source.fetched_at || now-Date.parse(source.fetched_at) > 900000) return 'Stale snapshot';
    return 'Recent download';
  };
  return <section className="rounded-xl border border-cyan-200 bg-white p-4 space-y-3" aria-labelledby="recent-data-title">
    <div className="flex flex-wrap items-start justify-between gap-3"><div><h2 id="recent-data-title" className="text-lg font-semibold">{enabled ? 'Real-time data: ON' : 'Local / offline mode'}</h2><p className="text-sm text-slate-600">{enabled ? 'Weather and official RSS refresh every 5 minutes. Results remain a scenario simulation.' : 'Online refresh is off. Run the local simulation with your chosen settings; internet is not required.'}</p></div>{enabled && <button type="button" className="planner-secondary" onClick={onRefresh} disabled={loading}>{loading ? 'Updating…' : 'Refresh recent data'}</button>}</div>
    {loading && <p className="text-sm" role="status">{enabled ? 'Fetching recent weather and official notices…' : 'Reading saved data from this computer…'}</p>}
    {error && <p className="text-sm text-amber-800" role="status">{error}</p>}
    {snapshot?.cache_warning && <p className="text-sm text-amber-800">{snapshot.cache_warning}</p>}
    {(enabled || weather?.data || alerts?.data) && <details open={enabled}><summary className="cursor-pointer text-sm font-medium">Weather &amp; recent official notices {enabled ? '' : '(saved data)'}</summary><div className="grid lg:grid-cols-2 gap-4 mt-3">
      <article className="rounded-lg border border-slate-200 p-3 space-y-2 text-sm"><h3 className="font-semibold">Chennai weather · {status('weather')}</h3><p className="text-xs text-slate-600">Downloaded: {time(weather?.fetched_at ?? null)}</p>{weather?.error && <p className="text-amber-800">{weather.error}. Retained data is cached.</p>}
        {weather?.data ? <><p>Temperature <strong>{weather.data.temperature_c.toFixed(1)} °C</strong> · humidity {weather.data.humidity_pct.toFixed(0)}% · wind {weather.data.wind_kmh.toFixed(1)} km/h</p><p>Precipitation: {weather.data.precipitation_mm.toFixed(2)} mm per {weather.data.interval_seconds/60} min · modeled at {time(weather.data.observed_at)}</p><p>Latest hourly precipitation: <strong>{weather.data.hourly_precipitation_mm.toFixed(2)} mm</strong>, for the hour ending {time(weather.data.hourly_at)}.</p><p className="text-xs text-slate-600">{weather.data.interpretation}</p><button type="button" className="planner-secondary" disabled={!canApply} onClick={() => onApplyRainfall(weather.data!.rainfall_mm_hr)}>Use hourly rainfall in scenario ({weather.data.rainfall_mm_hr.toFixed(2)} mm/hour)</button><p className="text-xs text-slate-600">Apply only changes the rainfall setting. Review and rerun to update results. Flood depth and spread stay as configured.</p><a href={weather.data.source_url} className="underline text-cyan-800" target="_blank" rel="noreferrer">{weather.data.attribution}</a></> : <p>No downloaded weather available. Enable real-time data with an internet connection; local scenarios remain available.</p>}
      </article>
      <article className="rounded-lg border border-slate-200 p-3 space-y-2 text-sm"><h3 className="font-semibold">NDMA SACHET · {status('alerts')}</h3><p className="text-xs text-slate-600">Downloaded: {time(alerts?.fetched_at ?? null)}</p>{alerts?.error && <p className="text-amber-800">{alerts.error}. Alert coverage cannot be confirmed.</p>}
        {alerts?.data ? <><p className="text-xs text-slate-600">{alerts.data.scope}. {alerts.data.interpretation}</p>{alerts.data.items.length ? <ul className="max-h-56 overflow-auto space-y-3">{alerts.data.items.map(item => <li key={item.id}><a href={item.url} target="_blank" rel="noreferrer" className="font-medium underline text-cyan-800">{item.title}</a><p className="text-xs text-slate-600">Issued {time(item.issued_at)} · {item.issuer}</p></li>)}</ul> : <p>No recent matching notices in this downloaded feed. This does not establish that no hazard exists.</p>}</> : <p>No official notices downloaded. This is unavailable coverage, not an all-clear.</p>}
        <a href="https://sachet.ndma.gov.in/" target="_blank" rel="noreferrer" className="underline text-cyan-800">Open official SACHET portal</a>
      </article>
    </div></details>}
  </section>;
}
