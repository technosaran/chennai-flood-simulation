'use client';
import { useEffect, useRef, useState } from 'react';
import type { SavedSimulation, SimulationResponse } from '@/lib/types';

type Entry = { id: string; name: string; saved_at: string; computed_at: string; timeline_steps: number; peak_affected: number; fleet_included: boolean; stored_bytes: number; imported?: boolean };
const base = process.env.NEXT_PUBLIC_API_URL || '';

export default function SavedSimulationLibrary({ result, disabled, running, archived, onOpen }: { result: SimulationResponse | null; disabled: boolean; running: boolean; archived: boolean; onOpen: (snapshot: SavedSimulation) => void }) {
  const [entries, setEntries] = useState<Entry[]>([]);
  const [name, setName] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [attempt, setAttempt] = useState(0);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(0);
  const [loading, setLoading] = useState(true);
  const [importFile, setImportFile] = useState<File | null>(null);
  const fileInput = useRef<HTMLInputElement>(null);
  useEffect(() => {
    const controller = new AbortController();
    let active = true;
    const timeout = setTimeout(() => controller.abort(), 10000);
    setLoading(true);
    fetch(`${base}/api/simulations/saved?offset=${page*20}`, { signal: controller.signal })
      .then(async response => { if (!response.ok) throw new Error('Local saved simulations could not be loaded. Check the backend connection.'); return response.json() as Promise<{ items: Entry[]; total: number }>; })
      .then(data => { if (active) { setEntries(data.items); setTotal(data.total); setError(''); } })
      .catch(() => { if (active) setError('Local saved simulations could not be loaded. Check the backend and refresh.'); })
      .finally(() => { clearTimeout(timeout); if (active) setLoading(false); });
    return () => { active = false; controller.abort(); clearTimeout(timeout); };
  }, [attempt, page]);
  const action = async (url: string, init?: RequestInit) => {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 20000);
    try {
      const response = await fetch(`${base}${url}`, { ...init, signal: controller.signal });
      const data = await response.json();
      if (!response.ok) throw new Error(typeof data.detail === 'string' ? data.detail : 'The archive request failed.');
      return data;
    } finally { clearTimeout(timeout); }
  };
  const save = async () => {
    if (!result || disabled || archived) return;
    setBusy(true); setError(''); setNotice('');
    try {
      await action('/api/simulations/saved', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ simulation_id: result.simulation_id, name: name.trim() }) });
      setNotice('Complete snapshot saved locally, including current allocations and fleet plans.'); setName(''); setPage(0); setAttempt(n => n+1);
    } catch (e) { setError(e instanceof Error ? e.message : 'Saving failed.'); }
    finally { setBusy(false); }
  };
  const open = async (id: string, download = false) => {
    setBusy(true); setError(''); setNotice('');
    try {
      const snapshot = await action(`/api/simulations/saved/${encodeURIComponent(id)}`) as SavedSimulation;
      if (download) {
        const url = URL.createObjectURL(new Blob([JSON.stringify(snapshot, null, 2)], { type: 'application/json' }));
        const link = document.createElement('a'); link.href = url; link.download = `${snapshot.id}.json`; link.click();
        setTimeout(() => URL.revokeObjectURL(url), 5000);
      } else onOpen(snapshot);
    } catch (e) { setError(e instanceof Error ? e.message : 'Opening failed.'); }
    finally { setBusy(false); }
  };
  const importSnapshot = async () => {
    if (!importFile || busy || running) return;
    setBusy(true); setError(''); setNotice('');
    try {
      if (importFile.size > 10 * 1024 * 1024) throw new Error('Snapshot files must be 10 MB or smaller.');
      await action('/api/simulations/saved/import', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: importFile });
      setNotice('Snapshot imported as a new read-only copy. Open it from the saved list. The active simulation was not changed.');
      setImportFile(null); if (fileInput.current) fileInput.current.value = '';
      setPage(0); setAttempt(n => n+1);
    } catch (e) { setError(e instanceof Error ? e.message : 'Import failed.'); }
    finally { setBusy(false); }
  };
  return <section className="rounded-2xl border border-cyan-200 bg-slate-50/60 p-5 space-y-4" aria-labelledby="saved-simulations-title">
    <h2 id="saved-simulations-title" className="text-xl font-semibold">Saved simulations</h2>
    <p className="text-sm text-slate-700">Save complete simulations locally and reopen them anytime. Saved views are read-only.</p>
    <form onSubmit={event => { event.preventDefault(); void save(); }} className="flex flex-wrap gap-3 items-end"><label className="text-sm">Snapshot name<input required maxLength={80} value={name} onChange={e => setName(e.target.value)} className="block rounded-lg border border-slate-200 bg-slate-50 p-2 mt-1" placeholder="Example: T. Nagar baseline" /></label><button className="notebook-button" disabled={!result || disabled || archived || busy || !name.trim()} type="submit">Save complete simulation</button><button type="button" className="notebook-button" disabled={busy || loading} onClick={() => setAttempt(n => n+1)}>Refresh saved list</button></form>
    <details className="clean-disclosure"><summary>Restore a backup</summary><form onSubmit={event => { event.preventDefault(); void importSnapshot(); }} className="rounded-xl border border-slate-200 p-3 space-y-2">
      <p id="snapshot-import-help" className="text-sm text-slate-700">Restore a file created by Download snapshot JSON (up to 10 MB). Each import creates a new copy. Imported results and evidence are supplied by the file and are not independently verified.</p>
      <div className="flex flex-wrap gap-3 items-end"><label className="text-sm">Snapshot JSON file<input ref={fileInput} type="file" accept=".json,application/json" aria-describedby="snapshot-import-help" disabled={busy || running} onChange={event => setImportFile(event.target.files?.[0] || null)} className="block mt-1 max-w-full text-sm" /></label><button className="notebook-button" type="submit" disabled={!importFile || busy || running}>Import snapshot JSON</button></div>
    </form></details>
    {error && <p role="alert" className="text-sm text-amber-800">{error}</p>}{notice && <p role="status" className="text-sm text-emerald-700">{notice}</p>}
    {loading ? <p role="status" className="text-sm text-slate-700">Loading local archive…</p> : entries.length === 0 ? <p className="text-sm text-slate-700">No saved snapshots on this page. Run a scenario, give it a name and save it here, or import a snapshot JSON file.</p> : <div className="space-y-3">{entries.map(entry => <article key={entry.id} className="rounded-xl border border-slate-200 p-3 flex flex-wrap justify-between gap-3"><div><h3 className="font-semibold">{entry.name}</h3>{entry.imported && <p className="text-sm text-amber-800">Imported file · evidence not independently verified</p>}<p className="text-sm text-slate-700 mt-1">Saved {new Date(entry.saved_at).toLocaleString()} · {entry.timeline_steps} snapshots · peak affected {entry.peak_affected.toLocaleString()} · {entry.fleet_included ? 'Fleet included' : 'No fleet plan'} · {(entry.stored_bytes/1024).toFixed(0)} KB compressed</p></div><div className="flex gap-2"><button className="notebook-button" disabled={running || busy} onClick={() => void open(entry.id)}>Open saved view</button><button className="notebook-button" disabled={busy} onClick={() => void open(entry.id, true)}>Download snapshot JSON</button></div></article>)}</div>}
    <div className="flex gap-3 items-center text-sm text-slate-700"><button className="notebook-button" disabled={page === 0 || loading || busy} onClick={() => setPage(n => n-1)}>Previous page</button><span>{total} saved · page {page+1}</span><button className="notebook-button" disabled={(page+1)*20 >= total || loading || busy} onClick={() => setPage(n => n+1)}>Next page</button></div>
  </section>;
}
