'use client';

import { useEffect, useState } from 'react';

type Metrics = { accuracy: number; balanced_accuracy: number; precision: number; recall: number; f1: number; roc_auc: number; rows: number };
type Report = {
  selection: string; selection_objective?: string; model_name: string; source_url: string; total_rows: number; usable_samples: number; excluded_windows: number;
  training_rows: number; validation_rows: number; split: Record<string, string[]>; test: Metrics;
  validation_candidates: Record<string, Metrics>; limitations: string[];
  baselines: Record<string, Metrics>;
};
type Prediction = { target_date: string; probability: number; elevated_rainfall: boolean; actual_rainfall_mm_day: number | null; interpretation: string };
const percent = (value: number) => `${(value * 100).toFixed(1)}%`;

export default function KaggleModelPanel() {
  const [report, setReport] = useState<Report | null>(null);
  const [prediction, setPrediction] = useState<Prediction | null>(null);
  const [day, setDay] = useState('2021-11-06');
  const [request, setRequest] = useState({ day, attempt: 0 });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 15000);
    let active = true;
    const get = async (path: string) => {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || ''}${path}`, { signal: controller.signal });
      const body = await response.json();
      if (!response.ok) throw new Error(typeof body.detail === 'string' ? body.detail : 'Kaggle evidence unavailable');
      return body;
    };
    setLoading(true); setError(''); setPrediction(null);
    // Evidence stays visible if a requested replay has incomplete measurements.
    Promise.allSettled([get('/api/weather/kaggle/evaluation'), get(`/api/weather/kaggle/prediction?as_of=${request.day}`)])
      .then(([evidence, forecast]) => {
        if (!active) return;
        setReport(evidence.status === 'fulfilled' ? evidence.value.evaluation : null);
        if (forecast.status === 'fulfilled') setPrediction(forecast.value);
        const failure = evidence.status === 'rejected' ? evidence.reason : forecast.status === 'rejected' ? forecast.reason : null;
        if (failure) setError(failure instanceof Error ? failure.message : 'Check the backend connection and retry.');
      }).finally(() => { clearTimeout(timeout); if (active) setLoading(false); });
    return () => { active = false; controller.abort(); clearTimeout(timeout); };
  }, [request]);
  return <section aria-labelledby="kaggle-title" className="rounded-2xl border border-cyan-200 bg-slate-50 p-5 space-y-4">
    <div><h2 id="kaggle-title" className="text-xl font-semibold text-cyan-700">Kaggle Chennai · trained rainfall model</h2>
      <p className="text-sm text-slate-700 mt-2">Real weather archive, automatic model comparison, and next-day rainfall replay. Target: rainfall ≥ 10 mm/day.</p></div>
    {loading && <p role="status">Loading verified evidence…</p>}
    {error && <p role="alert" className="text-sm text-amber-800">{error}</p>}
    {report && <>
      <p className="text-sm">Selected model: <strong>{report.model_name}</strong> · {report.total_rows.toLocaleString()} source records · {report.usable_samples.toLocaleString()} complete windows · {report.excluded_windows.toLocaleString()} excluded windows.</p>
      <p className="text-sm text-slate-700">Training: {report.split.training.join(' to ')} · Validation: {report.split.validation.join(' to ')} · Test: {report.split.test.join(' to ')}. Eight-day gaps separate splits. Dataset and model fingerprints verified.</p>
      <div className="overflow-x-auto"><table className="w-full text-sm text-left"><caption className="text-left pb-2 text-slate-700">Model comparison on validation years (used for automatic selection)</caption>
        <thead><tr>{['Candidate', 'Accuracy', 'Balanced accuracy', 'Precision', 'Recall', 'F1'].map(label => <th scope="col" className="p-2" key={label}>{label}</th>)}</tr></thead>
        <tbody>{Object.entries(report.validation_candidates).map(([name, metrics]) => <tr key={name} className="border-t border-slate-200"><th scope="row" className="p-2">{name}{name === report.model_name ? ' · selected' : ''}</th>{[metrics.accuracy, metrics.balanced_accuracy, metrics.precision, metrics.recall, metrics.f1].map((value, i) => <td className="p-2" key={i}>{percent(value)}</td>)}</tr>)}</tbody>
      </table></div>
      <p className="text-sm text-cyan-700">Held-out test: {report.test.rows.toLocaleString()} days · accuracy {percent(report.test.accuracy)} · balanced accuracy {percent(report.test.balanced_accuracy)} · precision {percent(report.test.precision)} · recall {percent(report.test.recall)} · ROC AUC {report.test.roc_auc.toFixed(3)}.</p>
      <p className="text-sm text-slate-700">Test baselines: always low rainfall has {percent(report.baselines.majority.accuracy)} accuracy and {percent(report.baselines.majority.balanced_accuracy)} balanced accuracy. Previous-day persistence has {percent(report.baselines.persistence.balanced_accuracy)} balanced accuracy, {percent(report.baselines.persistence.precision)} precision and {percent(report.baselines.persistence.recall)} recall. Selection: {report.selection} Accuracy includes dry days; check recall for missed rainy days.</p>
      <a className="text-cyan-700 underline text-sm" href={report.source_url} target="_blank" rel="noreferrer">Open Kaggle dataset</a>
    </>}
    <form className="flex flex-wrap items-end gap-3" onSubmit={event => { event.preventDefault(); setRequest(previous => ({ day, attempt: previous.attempt + 1 })); }}>
      <label className="text-sm">Historical conditions through<input className="block mt-2 rounded border border-slate-200 bg-slate-50 p-2" type="date" min="1990-01-07" max="2022-07-24" required value={day} onChange={event => setDay(event.target.value)} /></label>
      <button className="notebook-button" disabled={loading}>{loading ? 'Loading…' : 'Replay / refresh evidence'}</button>
    </form>
    {prediction && <div aria-live="polite" className="rounded-lg bg-slate-50 p-4 text-sm space-y-2"><p>{prediction.target_date}: <strong>{percent(prediction.probability)}</strong> estimated probability · {prediction.elevated_rainfall ? 'Elevated rainfall predicted' : 'Lower rainfall predicted'} · actual rainfall: {prediction.actual_rainfall_mm_day ?? 'missing'} mm/day.</p><p className="text-slate-700">{prediction.interpretation}</p></div>}
    <details className="text-sm text-slate-700"><summary>Reproduce training and understand scope</summary><p className="mt-2">Run <code>train_kaggle_weather.bat</code> in the project folder. It downloads and validates the dataset, compares three model families, selects for validation accuracy by default (use --objective balanced_accuracy for the recall-oriented setting), evaluates on held-out years, and checks portable inference before saving. Restart the backend after training. Add <code>--refresh</code> to download again.</p><ul className="list-disc pl-5 mt-2 space-y-1">{(report?.limitations ?? ['The rainfall model is available after training. Relief demand uses the existing synthetic ensemble; flood depth and spread use scenario settings.']).map(item => <li key={item}>{item}</li>)}</ul></details>
  </section>;
}
