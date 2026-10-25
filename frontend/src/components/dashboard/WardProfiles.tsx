'use client';

import { useEffect, useState } from 'react';
type Ward = { ward_id: string; modeled_population: number | null; modeled_clusters: { id: string; name: string; risk_level: string }[]; nearby_shelters: { id: string; name: string; capacity: number; available_baseline_capacity: number; straight_line_km: number; amenities: string[] }[] };
type Evidence = { wards: Ward[]; outside_gcc_clusters: { id: string; name: string }[]; sources: { title: string; url: string }[]; historical_context: string; planning_checklist: string[]; limitations: string[] };

export default function WardProfiles() {
  const [data, setData] = useState<Evidence | null>(null);
  const [error, setError] = useState('');
  const [search, setSearch] = useState('');
  const [selected, setSelected] = useState('');
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    fetch('/data/ward_profiles.json', { signal: controller.signal })
      .then(async response => { if (!response.ok) throw new Error('Unavailable'); return response.json() as Promise<Evidence>; })
      .then(result => { if (!controller.signal.aborted) { setData(result); setSelected(result.wards.find(w => w.modeled_clusters.length)?.ward_id || '1'); setError(''); } })
      .catch(() => { if (!controller.signal.aborted) setError('Ward profiles could not be loaded.'); });
    return () => controller.abort();
  }, [attempt]);
  const wards = data?.wards.filter(w => `ward ${w.ward_id} ${w.modeled_clusters.map(c => c.name).join(' ')}`.toLowerCase().includes(search.toLowerCase())) || [];
  const current = data?.wards.find(w => w.ward_id === selected);
  return <div className="space-y-6">
    <section className="rounded-2xl border border-slate-200 bg-slate-50/60 p-5 space-y-3"><span className="eyebrow">CHENNAI REFERENCE ATLAS</span><h2 className="text-2xl font-semibold">Ward profiles & planning context</h2><p className="text-sm text-slate-700">Explore all 200 published GCC wards, the project’s modeled population clusters and nearby planning shelters. These profiles are bundled locally for offline use.</p><p className="text-sm text-amber-800">Official boundaries; modeled populations and facilities. An empty ward profile means missing project coverage, not zero residents or zero flood risk.</p></section>
    {error && <div role="alert">{error} <button className="notebook-button" onClick={() => setAttempt(n => n + 1)}>Retry</button></div>}
    {!data && !error && <p role="status">Loading local ward profiles…</p>}
    {data && <div className="grid gap-5 lg:grid-cols-[280px_1fr]">
      <section className="rounded-xl border border-slate-200 bg-slate-50/60 p-4"><label className="block text-sm">Find a ward or modeled locality<input type="search" value={search} onChange={event => setSearch(event.target.value)} placeholder="Try 177, Velachery, Adyar…" className="mt-2 w-full rounded-lg bg-slate-50 border border-slate-200 p-2" /></label><p className="my-3 text-sm text-slate-700">{wards.length} wards match</p><div className="max-h-[480px] overflow-y-auto space-y-1" aria-label="Ward directory">{wards.map(w => <button key={w.ward_id} aria-pressed={w.ward_id === selected} className={`block w-full text-left rounded-lg p-3 border ${w.ward_id === selected ? 'border-cyan-200 bg-cyan-50' : 'border-transparent hover:bg-slate-50'}`} onClick={() => setSelected(w.ward_id)}><strong>Ward {w.ward_id}</strong><span className="block text-sm text-slate-700">{w.modeled_clusters.map(c => c.name).join(', ') || 'No modeled population cluster'}</span></button>)}</div>{wards.length === 0 && <p className="text-sm">No matching wards. Try a ward number.</p>}</section>
      {current && <section className="rounded-xl border border-slate-200 bg-slate-50/60 p-5 space-y-5" aria-live="polite"><h3 className="text-xl font-semibold">Ward {current.ward_id}</h3><div className="grid sm:grid-cols-2 gap-3"><div className="rounded-lg bg-slate-50 p-4"><p className="text-sm text-slate-700">Modeled population at included cluster points</p><strong className="text-2xl">{current.modeled_population?.toLocaleString() ?? 'Not supplied'}</strong></div><div className="rounded-lg bg-slate-50 p-4"><p className="text-sm text-slate-700">Official population / vulnerable-group counts</p><strong>Not supplied by this dataset</strong></div></div>
        {current.modeled_clusters.map(c => <p key={c.id} className="text-sm">{c.name} · modeled risk category: <strong>{c.risk_level}</strong></p>)}
        <h4 className="font-semibold">Nearby modeled shelters</h4><p className="text-sm text-slate-700">Straight-line proximity from the ward’s reference point. Run a scenario to assess flood-aware access and available capacity.</p><div className="space-y-3">{current.nearby_shelters.map(s => <article key={s.id} className="rounded-lg border border-slate-200 p-3"><h5 className="font-semibold text-sm">{s.name}</h5><p className="text-sm text-cyan-700">{s.straight_line_km.toFixed(2)} km straight line · {s.available_baseline_capacity.toLocaleString()} baseline spaces / {s.capacity.toLocaleString()} capacity</p><p className="text-sm text-slate-700 mt-1">{s.amenities.join(' · ')}</p></article>)}</div>
        <h4 className="font-semibold">Inclusive planning checklist</h4><ul className="list-disc pl-5 text-sm text-slate-700 space-y-2">{data.planning_checklist.map(item => <li key={item}>{item}</li>)}</ul>
      </section>}
    </div>}
    {data && <section className="rounded-xl border border-slate-200 p-5 space-y-3"><h3 className="font-semibold">Historical context, coverage & sources</h3><p className="text-sm text-slate-700">{data.historical_context}</p>{data.outside_gcc_clusters.length > 0 && <p className="text-sm text-amber-800">Modeled locations outside the published GCC polygons: {data.outside_gcc_clusters.map(c => c.name).join(', ')}. They remain part of simulation coverage.</p>}<ul className="list-disc pl-5 text-sm text-slate-700 space-y-2">{data.limitations.map(item => <li key={item}>{item}</li>)}</ul><div className="flex flex-wrap gap-4">{data.sources.map(s => <a key={s.url} href={s.url} target="_blank" rel="noreferrer" className="text-sm underline text-cyan-700">{s.title}</a>)}</div></section>}
  </div>;
}
