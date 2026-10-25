'use client';

import { useEffect, useState } from 'react';

type Metrics = { rows: number; positive_days: number; accuracy: number; balanced_accuracy: number; precision: number; recall: number; f1: number; roc_auc: number; confusion_matrix: number[][] };
type Evidence = { evaluation: { model_name: string; training_rows: number; validation_rows: number; test: Metrics; baselines: Record<string, Metrics>; limitations: string[] }; dataset: { rows: number; source_url: string } };
type Prediction = { target_date: string; probability: number; decision_threshold: number; elevated_rainfall: boolean; actual_rainfall_mm_day: number | null; split: string; interpretation: string; outside_training_ranges: string[] };
const percent = (value: number) => `${(value * 100).toFixed(2)}%`;

export default function WeatherModelPanel() {
  const [evidence, setEvidence] = useState<Evidence | null>(null);
  const [prediction, setPrediction] = useState<Prediction | null>(null);
  const [day, setDay] = useState('2023-12-03');
  const [requestedDay, setRequestedDay] = useState(day);
  const [attempt, setAttempt] = useState(0);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 15000);
    let active = true;
    const base = process.env.NEXT_PUBLIC_API_URL || '';
    setLoading(true); setError(''); setPrediction(null);
    const get = async (url: string) => {
      const response = await fetch(`${base}${url}`, { signal: controller.signal });
      if (!response.ok) throw new Error('Weather evidence unavailable');
      return response.json();
    };
    Promise.all([get('/api/weather/evaluation'), get(`/api/weather/prediction?as_of=${requestedDay}`)])
      .then(([report, forecast]) => { if (active) { setEvidence(report); setPrediction(forecast); } })
      .catch(() => { if (active) { setEvidence(null); setError('Weather evidence unavailable. Check the backend and retry.'); } })
      .finally(() => { clearTimeout(timeout); if (active) setLoading(false); });
    return () => { active = false; controller.abort(); clearTimeout(timeout); };
  }, [requestedDay, attempt]);
  const report = evidence?.evaluation;
  const comparisons: [string, Metrics][] = report ? [['Trained model', report.test], ['Always low rainfall', report.baselines.majority], ['Previous-day persistence', report.baselines.persistence]] : [];
  return <section className="rounded-2xl border border-cyan-200 bg-slate-50/60 p-5 space-y-4" aria-labelledby="weather-model-title">
    <h3 id="weather-model-title" className="font-semibold text-cyan-700">Real-data rainfall model</h3>
    <p className="text-sm text-slate-700">Next-day rainfall ≥ 10 mm/day at the Chennai NASA POWER grid point. Historical reanalysis experiment; flood geometry remains a scenario calculation.</p>
    {error && <p role="alert" className="text-sm text-amber-800">{error}</p>}
    {report && <>
      <p className="text-sm text-slate-700">{report.model_name} · {evidence?.dataset.rows.toLocaleString()} daily records (2001–2025) · {report.training_rows.toLocaleString()} training days · {report.validation_rows.toLocaleString()} validation days · {report.test.rows.toLocaleString()} test days (2022–2025). Verified model and dataset fingerprints.</p>
      <div className="overflow-x-auto"><table className="w-full text-sm text-left"><caption className="sr-only">Rainfall classification on chronological test years</caption><thead><tr>{['Model', 'Accuracy', 'Balanced accuracy', 'Precision', 'Recall', 'F1'].map(label => <th key={label} scope="col" className="p-2 whitespace-nowrap">{label}</th>)}</tr></thead><tbody>{comparisons.map(([label, m]) => <tr key={label} className="border-t border-slate-200"><th scope="row" className="p-2 whitespace-nowrap">{label}</th>{[m.accuracy, m.balanced_accuracy, m.precision, m.recall, m.f1].map((v, i) => <td key={i} className="p-2">{percent(v)}</td>)}</tr>)}</tbody></table></div>
      <p className="text-sm text-slate-700">ROC AUC: {report.test.roc_auc.toFixed(3)}. Only {report.test.positive_days} test days meet the rainfall threshold. The selected threshold favors balanced accuracy and recall, with more false alarms. Confusion counts: {report.test.confusion_matrix[0][0]} true negatives, {report.test.confusion_matrix[0][1]} false positives, {report.test.confusion_matrix[1][0]} false negatives, {report.test.confusion_matrix[1][1]} true positives.</p>
      <a href={evidence?.dataset.source_url} target="_blank" rel="noreferrer" className="text-sm text-cyan-700 underline">NASA POWER data documentation</a>
    </>}
    <form className="flex flex-wrap gap-3 items-end" onSubmit={event => { event.preventDefault(); setRequestedDay(day); setAttempt(n => n + 1); }}>
      <label className="text-sm text-slate-700">Historical conditions through (UTC)<input required type="date" min="2022-01-01" max="2025-12-30" value={day} onChange={event => setDay(event.target.value)} className="block mt-2 rounded-lg border border-slate-200 bg-slate-50 p-2 text-slate-900" /></label>
      <button className="notebook-button" disabled={loading} type="submit">{loading ? 'Loading…' : 'Replay prediction'}</button>
    </form>
    {prediction && <div aria-live="polite" className="rounded-lg bg-slate-50 p-4 space-y-2"><p className="text-sm">For {prediction.target_date}: <strong>{percent(prediction.probability)}</strong> estimated probability of rainfall ≥ 10 mm/day · {prediction.elevated_rainfall ? 'Elevated rainfall predicted' : 'Lower rainfall predicted'}.</p><p className="text-sm text-slate-700">Decision cutoff: {percent(prediction.decision_threshold)} (selected on validation balanced accuracy). Actual next-day reanalysis: {prediction.actual_rainfall_mm_day ?? 'Unavailable'} mm/day · {prediction.split} split. {prediction.interpretation}</p>{prediction.outside_training_ranges.length > 0 && <p className="text-sm text-amber-800">Outside training ranges: {prediction.outside_training_ranges.join(', ')}. Treat this replay with additional caution.</p>}</div>}
    {report && <details className="text-sm text-slate-700"><summary className="cursor-pointer">Dataset and evaluation limitations</summary><ul className="list-disc pl-5 mt-3 space-y-2">{report.limitations.map(item => <li key={item}>{item}</li>)}</ul></details>}
  </section>;
}
