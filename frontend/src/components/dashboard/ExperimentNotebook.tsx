'use client';

import { useEffect, useRef, useState } from 'react';
import { BookOpen, Download, FlaskConical, RotateCcw, Trash2 } from 'lucide-react';
import { DisasterParameters, FloodZoneInput, SimulationResponse, RescueFleetConfig } from '@/lib/types';
import { toSimulationParameters } from '@/lib/api';

interface Experiment {
  id: string;
  name: string;
  date: string;
  parameters: DisasterParameters;
  zones: FloodZoneInput[];
  peakAffected: number;
  peakAssigned: number;
  peakStranded: number;
  area: number;
  fleet?: RescueFleetConfig;
  peakFleetServed?: number;
  peakFleetRemaining?: number;
}
const STORAGE_KEY = 'chennai-flood-lab.experiments.v1';
function isExperiment(value: unknown): value is Experiment {
  if (!value || typeof value !== 'object') return false;
  const e = value as Experiment;
  if (e.fleet && (!Array.isArray(e.fleet.base_location) || e.fleet.base_location.length !== 2 || !e.fleet.base_location.every(Number.isFinite)
      || !Number.isFinite(e.fleet.planning_window_minutes) || !['trucks', 'boats', 'helicopters'].every(mode => {
        const pool = e.fleet![mode as 'trucks' | 'boats' | 'helicopters'];
        return pool && ['count', 'seats', 'speed_kmh', 'handling_minutes', 'ready_after_minutes'].every(key => Number.isFinite(pool[key as keyof typeof pool]));
      }))) return false;
  if ([e.peakFleetServed, e.peakFleetRemaining].some(n => n !== undefined && (!Number.isFinite(n) || n < 0))) return false;
  return typeof e.id === 'string' && typeof e.name === 'string' && typeof e.date === 'string'
    && [e.peakAffected, e.peakAssigned, e.peakStranded, e.area].every(n => typeof n === 'number' && Number.isFinite(n) && n >= 0)
    && !!e.parameters && [e.parameters.rainfall_intensity_mm_hr, e.parameters.flood_depth_meters,
      e.parameters.spread_rate_meters_hr, e.parameters.duration_hours].every(Number.isFinite)
    && Array.isArray(e.zones) && e.zones.length > 0 && e.zones.every(z =>
      z && typeof z.id === 'string' && ['circle', 'polygon'].includes(z.type)
      && Array.isArray(z.coordinates) && z.coordinates.length > 0
      && z.coordinates.every(p => Array.isArray(p) && p.length === 2 && p.every(Number.isFinite)));
}

export default function ExperimentNotebook({ result, parameters, zones, disabled, onRestore }: {
  result: SimulationResponse | null;
  parameters: DisasterParameters;
  zones: FloodZoneInput[];
  disabled: boolean;
  onRestore: (parameters: DisasterParameters, zones: FloodZoneInput[], fleet?: RescueFleetConfig) => void;
}) {
  const [experiments, setExperiments] = useState<Experiment[]>([]);
  const [ready, setReady] = useState(false);
  const [storageError, setStorageError] = useState('');
  const [baselineId, setBaselineId] = useState('');
  const [comparisonId, setComparisonId] = useState('');
  const recorded = useRef<string | null>(null);
  useEffect(() => {
    try {
      const saved: unknown = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]');
      if (Array.isArray(saved)) setExperiments(saved.filter(isExperiment).slice(0, 8));
    } catch { setStorageError('Saved experiments could not be read. New comparisons remain available in this session.'); }
    setReady(true);
  }, []);
  useEffect(() => {
    if (!ready || !result || disabled || recorded.current === result.simulation_id) return;
    recorded.current = result.simulation_id;
    const entry: Experiment = {
      id: result.simulation_id, name: zones[0]?.name || 'Custom scenario', date: result.computed_at,
      parameters: { ...parameters }, zones: structuredClone(zones),
      peakAffected: Math.max(...result.timeline.map(s => s.metrics.total_affected_population)),
      peakAssigned: Math.max(...result.timeline.map(s => s.metrics.total_evacuated_population)),
      peakStranded: Math.max(...result.timeline.map(s => s.metrics.unassigned_stranded_population)),
      area: Math.max(...result.timeline.map(s => s.metrics.total_flooded_area_sq_km)),
      fleet: result.scenario?.rescue_fleet || undefined,
      peakFleetServed: result.timeline.some(s => s.rescue_fleet_plan) ? Math.max(...result.timeline.map(s => s.rescue_fleet_plan?.provisionally_served || 0)) : undefined,
      peakFleetRemaining: result.timeline.some(s => s.rescue_fleet_plan) ? Math.max(...result.timeline.map(s => s.rescue_fleet_plan?.still_needing_support || 0)) : undefined,
    };
    setExperiments(old => [entry, ...old.filter(e => e.id !== entry.id)].slice(0, 8));
  }, [result, parameters, zones, disabled, ready]);
  useEffect(() => {
    if (!ready) return;
    try { localStorage.setItem(STORAGE_KEY, JSON.stringify(experiments)); }
    catch { setStorageError('Browser storage is unavailable. Export the comparison to keep your results.'); }
  }, [experiments, ready]);

  const baseline = experiments.find(e => e.id === baselineId) || experiments[experiments.length - 1];
  const comparison = experiments.find(e => e.id === comparisonId && e.id !== baseline?.id) || experiments.find(e => e.id !== baseline?.id);
  const exportComparison = () => {
    const quote = (value: string | number) => `"${String(value).replace(/"/g, '""')}"`;
    const rows = [['Scenario', 'Computed UTC', 'Rainfall mm/hr', 'Depth m', 'Duration hours', 'Peak affected', 'Peak assigned', 'Peak requiring rescue', 'Max area km2', 'Peak provisional fleet service', 'Peak remaining support need'],
      ...experiments.map(e => [e.name, e.date, toSimulationParameters(e.parameters).rainfall_intensity_mm_hr,
        e.parameters.flood_depth_meters, e.parameters.duration_hours, e.peakAffected, e.peakAssigned, e.peakStranded, e.area, e.peakFleetServed ?? '', e.peakFleetRemaining ?? ''])];
    const url = URL.createObjectURL(new Blob([rows.map(row => row.map(quote).join(',')).join('\r\n')], { type: 'text/csv;charset=utf-8;' }));
    const link = document.createElement('a');
    link.href = url; link.download = 'chennai-scenario-comparison.csv'; link.click();
    setTimeout(() => URL.revokeObjectURL(url), 5000);
  };
  return <section className="experiment-notebook" aria-labelledby="notebook-title">
    <div className="notebook-heading">
      <div><span className="eyebrow">EXPERIMENT NOTEBOOK</span><h3 id="notebook-title"><FlaskConical size={20} /> Compare your scenarios</h3>
        <p>The last eight completed runs are saved in this browser. Restore settings to run an experiment again.</p></div>
      <button className="notebook-button" disabled={!experiments.length} onClick={exportComparison}><Download size={14} /> Export comparison</button>
    </div>
    {storageError && <p className="notebook-note" role="status">{storageError}</p>}
    {experiments.length ? <>
      {experiments.length >= 2 && baseline && comparison && <div className="rounded-xl border border-cyan-200 bg-slate-50 p-4 space-y-4">
        <h4 className="font-semibold">Baseline → comparison</h4>
        <div className="grid sm:grid-cols-2 gap-3"><label className="text-sm">Baseline run<select className="block w-full bg-slate-50 border border-slate-200 rounded-lg p-2 mt-2" value={baseline.id} onChange={event => setBaselineId(event.target.value)}>{experiments.map(e => <option key={e.id} value={e.id}>{e.name} · {toSimulationParameters(e.parameters).rainfall_intensity_mm_hr} mm/h · {new Date(e.date).toLocaleTimeString()}</option>)}</select></label><label className="text-sm">Comparison run<select className="block w-full bg-slate-50 border border-slate-200 rounded-lg p-2 mt-2" value={comparison.id} onChange={event => setComparisonId(event.target.value)}>{experiments.filter(e => e.id !== baseline.id).map(e => <option key={e.id} value={e.id}>{e.name} · {toSimulationParameters(e.parameters).rainfall_intensity_mm_hr} mm/h · {new Date(e.date).toLocaleTimeString()}</option>)}</select></label></div>
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-3">{([
          ['Peak affected', baseline.peakAffected, comparison.peakAffected, 'people'],
          ['Peak assigned', baseline.peakAssigned, comparison.peakAssigned, 'people'],
          ['Peak rescue need', baseline.peakStranded, comparison.peakStranded, 'people'],
          ['Maximum flood area', baseline.area, comparison.area, 'km²'],
        ] as [string, number, number, string][]).map(([label, a, b, unit]) => <article key={label} className="rounded-lg border border-slate-200 p-3"><p className="text-sm text-slate-700">{label}</p><p className="font-semibold mt-1">{a.toLocaleString()} → {b.toLocaleString()} {unit}</p><p className="text-sm text-cyan-700 mt-1">{b-a > 0 ? '+' : ''}{(b-a).toLocaleString(undefined, { maximumFractionDigits: 2 })} {unit} · {a === 0 ? 'percentage change unavailable from zero' : `${((b-a)/a*100).toFixed(1)}% change`}</p></article>)}</div>
        <p className="text-sm text-slate-700">Differences compare independent modeled outcomes, not measured intervention effects. Peak columns can refer to different hours. Keep zones and duration consistent when testing a single parameter.</p>
        {baseline.peakFleetServed !== undefined && comparison.peakFleetServed !== undefined && <p className="text-sm text-cyan-700">Fleet comparison: peak provisional service {baseline.peakFleetServed.toLocaleString()} → {comparison.peakFleetServed.toLocaleString()} people; peak remaining support need {baseline.peakFleetRemaining?.toLocaleString()} → {comparison.peakFleetRemaining?.toLocaleString()} people. These are maxima of newly planned passengers per step, not cumulative arrivals. Compare matching fleet modes.</p>}
      </div>}
      <div className="comparison-scroll"><table className="comparison-table">
        <caption className="sr-only">Independent peak values for saved flood scenarios</caption>
        <thead><tr><th scope="col">Scenario / conditions</th><th scope="col">Peak affected</th><th scope="col">Peak assigned</th><th scope="col">Peak rescue need</th><th scope="col">Max area</th><th scope="col">Actions</th></tr></thead>
        <tbody>{experiments.map(e => <tr key={e.id} className={e.id === result?.simulation_id ? 'current-experiment' : ''}>
          <th scope="row"><strong>{e.name}</strong><small>{toSimulationParameters(e.parameters).rainfall_intensity_mm_hr} mm/h · {e.parameters.flood_depth_meters} m · {e.parameters.duration_hours} h</small></th>
          <td>{e.peakAffected.toLocaleString()}</td><td>{e.peakAssigned.toLocaleString()}</td><td className={e.peakStranded ? 'rescue-number' : ''}>{e.peakStranded.toLocaleString()}</td><td>{e.area.toFixed(2)} km²</td>
          <td><div className="experiment-actions"><button disabled={disabled} onClick={() => onRestore(e.parameters, structuredClone(e.zones), e.fleet ? structuredClone(e.fleet) : undefined)} aria-label={`Restore ${e.name}`} title="Restore scenario settings"><RotateCcw size={15} /></button><button disabled={disabled} onClick={() => setExperiments(old => old.filter(item => item.id !== e.id))} aria-label={`Delete saved ${e.name}`} title="Remove saved comparison"><Trash2 size={15} /></button></div></td>
        </tr>)}</tbody>
      </table></div>
      <p className="notebook-note">Each column is a separate maximum over the timeline; peaks can occur at different hours. Assigned people are hourly plans, not cumulative evacuations.</p>
    </> : <div className="notebook-empty"><FlaskConical size={25} /><div><strong>Turn a simulation into an experiment</strong><p>Run a preset, change rainfall or depth, then run again. Compare exposure, shelter assignments, and rescue needs here.</p></div></div>}
    <details className="research-details"><summary><BookOpen size={16} /> Research basis & model boundaries</summary>
      <div className="research-grid">
        <article><h4>Flood progression</h4><p>Scenario geometry estimates spread and depth. Observed forecasting requires rainfall, terrain, drainage and hydrological calibration.</p><a href="https://nhess.copernicus.org/articles/26/3749/2026/" target="_blank" rel="noreferrer">Chennai forecasting study · Paul et al., 2026 ↗</a></article>
        <article><h4>Network accessibility</h4><p>Depth thresholds close modeled roads. Capacity and congestion affect assignments. Routes depend on a simplified offline road graph.</p><a href="https://arxiv.org/abs/2109.11712" target="_blank" rel="noreferrer">Flood mapping for route optimization · 2021 ↗</a></article>
        <article><h4>Demand uncertainty</h4><p>The demand ensemble learns synthetic labels. Its held-out scores measure synthetic performance; rescue vehicle availability and actual delivery are not simulated.</p><a href="https://link.springer.com/article/10.1007/s00291-020-00613-w" target="_blank" rel="noreferrer">Disrupted road network exploration · 2020 ↗</a></article>
      </div>
    </details>
  </section>;
}
