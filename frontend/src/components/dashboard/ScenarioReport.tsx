'use client';

import { useState } from 'react';
import { Download } from 'lucide-react';
import type { FeatureCollection } from 'geojson';
import type { DisasterParameters, SimulationResponse } from '@/lib/types';
import { toSimulationParameters } from '@/lib/api';
import { createScenarioReport } from '@/lib/scenario-report';

export default function ScenarioReport({ result, parameters, isDirty, isSimulating, compact = false }: { result: SimulationResponse | null; parameters: DisasterParameters; isDirty: boolean; isSimulating: boolean; compact?: boolean }) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const download = async () => {
    if (!result || isDirty || isSimulating) return;
    setBusy(true); setError('');
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 8000);
    const get = async (url: string) => {
      try { const response = await fetch(url, { signal: controller.signal }); return response.ok ? await response.json() : undefined; }
      catch { return undefined; }
    };
    try {
      const base = process.env.NEXT_PUBLIC_API_URL || '';
      const [wards, roads, rivers, demand, weather] = await Promise.all([
        get('/data/gcc_wards.json'), get('/data/offline_roads.json'), get('/data/offline_rivers.json'),
        result.archived_evidence ? Promise.resolve(result.archived_evidence.demand) : get(`${base}/api/model/evaluation`),
        result.archived_evidence ? Promise.resolve(result.archived_evidence.weather) : get(`${base}/api/weather/evaluation`),
      ]);
      const html = createScenarioReport(result, result.archived_parameters || toSimulationParameters(parameters), { wards: wards as FeatureCollection, roads: roads as FeatureCollection, rivers: rivers as FeatureCollection }, { demand, weather });
      const url = URL.createObjectURL(new Blob([html], { type: 'text/html;charset=utf-8' }));
      const link = document.createElement('a'); link.href = url; link.download = `chennai-scenario-${result.simulation_id}.html`; link.click();
      setTimeout(() => URL.revokeObjectURL(url), 5000);
    } catch { setError('Report generation failed. Keep the scenario JSON and retry.'); }
    finally { clearTimeout(timeout); setBusy(false); }
  };
  if (compact) return <div><button className="planner-secondary" disabled={!result || isDirty || isSimulating || busy} onClick={download}><Download size={17} />{busy ? 'Preparing report…' : 'Download report'}</button>{error && <p role="alert">{error}</p>}</div>;
  return <section className="rounded-2xl border border-slate-200 bg-slate-50/60 p-5 space-y-3"><h2 className="text-xl font-semibold">Download a scenario report</h2><p className="text-sm text-slate-700">A self-contained HTML report with the peak-exposure map, hourly outcomes, final resource shortages, model evidence and sources. Open it offline; use Print → Save as PDF for submission.</p><button className="notebook-button" disabled={!result || isDirty || isSimulating || busy} onClick={download}><Download size={16} />{busy ? 'Preparing report…' : 'Download scenario report'}</button>{(!result || isDirty) && <p className="text-sm text-slate-700">Run the current scenario to enable its report.</p>}{error && <p role="alert" className="text-sm text-amber-800">{error}</p>}</section>;
}
