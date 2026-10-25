'use client';

import { useEffect, useState } from 'react';
import { Download, RefreshCw } from 'lucide-react';
import { SimulationResponse } from '@/lib/types';
import { demoSteps, vivaQuestions } from '@/lib/review-guide';

type Resource = 'water_litres' | 'food_rations' | 'medical_kits';
interface Evidence {
  model: { name: string; tree_count?: number; features?: string[] };
  evaluation_status: string;
  evaluation: null | {
    generated_at: string; holdout_event: string; rows: number; ml_rows: number; rule_fallback_rows: number;
    runtime_mae_units: Record<Resource, number>;
    runtime_baseline_mae_units: Record<Resource, number>;
    interval_coverage_ml_rows: Record<Resource, number | null>;
  };
  limitations: string[];
  reproduce_command: string;
}
const resources: [Resource, string][] = [['water_litres', 'Water (litres)'], ['food_rations', 'Food (rations)'], ['medical_kits', 'Medicine (kits)']];

export default function ProjectReview({ result, isDirty }: { result: SimulationResponse | null; isDirty: boolean }) {
  const [evidence, setEvidence] = useState<Evidence | null>(null);
  const [error, setError] = useState('');
  const [attempt, setAttempt] = useState(0);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  useEffect(() => {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 10000);
    let active = true;
    setLoading(true); setError('');
    fetch(`${process.env.NEXT_PUBLIC_API_URL || ''}/api/model/evaluation`, { signal: controller.signal })
      .then(async response => {
        if (!response.ok) throw new Error('Evaluation could not be loaded. Start the backend, then retry.');
        return response.json() as Promise<Evidence>;
      }).then(data => { if (active) setEvidence(data); })
      .catch(() => { if (active) { setEvidence(null); setError('Evaluation could not be loaded. Check the backend connection and retry.'); } })
      .finally(() => { clearTimeout(timer); if (active) setLoading(false); });
    return () => { active = false; clearTimeout(timer); controller.abort(); };
  }, [attempt]);
  const report = evidence?.evaluation;
  const diagnostics = !isDirty ? result?.diagnostics : null;
  const questions = vivaQuestions.filter(item => `${item.question} ${item.answer}`.toLowerCase().includes(search.toLowerCase()));
  const download = () => {
    const text = ['# Chennai Flood Lab — panel preparation', ...vivaQuestions.flatMap(q => [`\n## ${q.question}`, q.answer]),
      '\n## Demo sequence', ...demoSteps.map((s, i) => `${i + 1}. ${s}`),
      '\n## Verified model evaluation', evidence ? JSON.stringify(evidence, null, 2) : 'Evaluation unavailable.',
      '\n## Current run diagnostics', JSON.stringify(diagnostics || { status: 'Run the current scenario to collect diagnostics.' }, null, 2)].join('\n');
    const url = URL.createObjectURL(new Blob([text], { type: 'text/markdown;charset=utf-8' }));
    const link = document.createElement('a'); link.href = url; link.download = 'chennai-flood-lab-panel-guide.md'; link.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  };
  return <div className="space-y-6">
    <section className="rounded-2xl border border-slate-200 bg-slate-50/60 p-5 space-y-4" aria-labelledby="review-title">
      <div className="flex flex-wrap items-start justify-between gap-3"><div><h2 id="review-title" className="text-xl font-semibold">System Evaluation & Audit</h2><p className="text-sm text-slate-700 mt-2">Empirical model validation, runtime telemetry, and panel defense guide.</p></div><button className="notebook-button" onClick={download}><Download size={16} /> Download panel guide</button></div>
      <p className="text-sm text-slate-700">Chennai Flood Lab combines scenario geometry, flood-aware graph routing, capacity-constrained shelter assignment and conformal ML relief-demand estimation for comprehensive disaster response modeling.</p>
      <h3 className="font-semibold">Deployed model evaluation</h3>
      <button className="notebook-button" disabled={loading} onClick={() => setAttempt(n => n + 1)}><RefreshCw size={14} />{loading ? 'Loading evidence…' : 'Refresh evidence'}</button>
      {error && <p role="alert" className="text-sm text-amber-800">{error}</p>}
      {evidence && <><p className="text-sm text-slate-700">Active model: <strong>{evidence.model.name}</strong>{evidence.model.tree_count ? ` · ${evidence.model.tree_count} trees` : ''}</p>
        {report ? <><p className="text-sm text-slate-700">Verified model and dataset fingerprints · {report.rows.toLocaleString()} held-out synthetic rows ({report.holdout_event}). Evaluated {new Date(report.generated_at).toLocaleString()}. ML rows: {report.ml_rows.toLocaleString()}; fallback rows: {report.rule_fallback_rows.toLocaleString()}.</p>
          <div className="overflow-x-auto"><table className="w-full text-sm text-left"><caption className="sr-only">Deployed demand model compared with planning rules on synthetic labels</caption><thead><tr>{['Resource', 'Runtime MAE', 'Rule MAE', 'ML interval coverage'].map(label => <th key={label} scope="col" className="p-3 whitespace-nowrap">{label}</th>)}</tr></thead><tbody>{resources.map(([key, label]) => <tr key={key} className="border-t border-slate-200"><th scope="row" className="p-3 font-medium whitespace-nowrap">{label}</th><td className="p-3">{report.runtime_mae_units[key].toFixed(2)}</td><td className="p-3">{report.runtime_baseline_mae_units[key].toFixed(2)}</td><td className="p-3">{report.interval_coverage_ml_rows[key] === null ? 'Unavailable' : `${(report.interval_coverage_ml_rows[key]! * 100).toFixed(2)}%`}</td></tr>)}</tbody></table></div>
          <p className="text-sm text-slate-700">MAE is mean absolute error in the resource units. Lower is better. Coverage is the fraction of held-out ML targets inside their intervals.</p></> : <p className="text-sm text-amber-800">The evaluation is missing, stale, or belongs to another model. Reproduce it with the command below.</p>}
        <code className="block break-all text-sm text-cyan-700">{evidence.reproduce_command}</code>
        <ul className="list-disc pl-5 space-y-1 text-sm text-slate-700">{evidence.limitations.map(item => <li key={item}>{item}</li>)}</ul></>}
    </section>
    <section className="rounded-2xl border border-slate-200 bg-slate-50/60 p-5 space-y-3"><h3 className="font-semibold">Current run evidence</h3>{diagnostics ? <><p className="text-sm text-slate-700">Run {result?.simulation_id} · {diagnostics.time_steps} snapshots · {diagnostics.compute_time_ms} ms engine time · {diagnostics.ml_predictions} ML demand predictions · {diagnostics.rule_predictions} rule predictions.</p><p className="text-sm text-slate-700">{diagnostics.demand_model.name}. Counts describe calls in this run, not prediction accuracy. Engine time excludes browser rendering and network transfer.</p></> : <p className="text-sm text-slate-700">{isDirty ? 'Settings changed. Run the scenario again to collect current evidence.' : 'Run a simulation to collect model usage and engine timing.'}</p>}</section>
    <section className="rounded-2xl border border-slate-200 bg-slate-50/60 p-5 space-y-4"><h3 className="font-semibold">Likely panel questions</h3><label className="block text-sm text-slate-700">Search questions<input value={search} onChange={event => setSearch(event.target.value)} type="search" placeholder="Try dataset, routing, leakage…" className="block w-full mt-2 rounded-lg border border-slate-200 bg-slate-50 p-3 text-slate-900" /></label><p className="text-sm text-slate-700">{questions.length} questions</p>{questions.map(item => <details key={item.question} className="border-t border-slate-200 pt-3"><summary className="cursor-pointer text-sm font-medium">{item.question}</summary><p className="mt-3 text-sm leading-relaxed text-slate-700">{item.answer}</p></details>)}</section>
    <section className="rounded-2xl border border-slate-200 bg-slate-50/60 p-5 space-y-3"><h3 className="font-semibold">Suggested demo sequence</h3><ol className="list-decimal pl-5 space-y-3 text-sm text-slate-700">{demoSteps.map(step => <li key={step}>{step}</li>)}</ol></section>
  </div>;
}
