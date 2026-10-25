'use client';

import { useEffect, useState, useCallback } from 'react';
import { Droplets, AlertTriangle, Activity, X, RefreshCw, ArrowLeft } from 'lucide-react';

export interface ReservoirStatus {
  id: string;
  name: string;
  coordinates: [number, number];
  current_storage_mcft: number;
  total_capacity_mcft: number;
  capacity_mcft: number;
  storage_pct: number;
  water_level_ft: number;
  full_tank_level_ft: number;
  current_inflow_cusecs: number;
  current_discharge_cusecs: number;
  gates_open: number;
  sluice_gates_count: number;
  alert_level: string;
  surge_risk: string;
  primary_river: string;
  impact_corridor: string[];
}

export interface RiverSurge {
  governing_reservoir?: string;
  governing_reservoirs?: string[];
  total_discharge_cusecs: number;
  projected_stage_surge_m: number;
  status: string;
  advisory: string;
  vulnerable_gcc_zones: string[];
}

export interface ReservoirSummary {
  timestamp: string;
  highest_alert_level: string;
  overall_storage_pct: number;
  total_storage_mcft: number;
  total_capacity_mcft: number;
  total_inflow_cusecs: number;
  total_discharge_cusecs: number;
  reservoirs: ReservoirStatus[];
  river_surges: Record<string, RiverSurge>;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const alertColors: Record<string, string> = {
  NORMAL: 'text-emerald-700',
  ADVISORY: 'text-yellow-600',
  WARNING: 'text-orange-500',
  CRITICAL_DISCHARGE: 'text-red-700',
};

const surgeColors: Record<string, string> = {
  NORMAL_CHANNEL_FLOW: 'bg-emerald-50/40 border-emerald-200',
  MODERATE_CHANNEL_RISE: 'bg-yellow-50 border-yellow-300',
  WARNING_OVERFLOW: 'bg-orange-50 border-orange-300',
  EXTREME_OVERFLOW: 'bg-red-50/40 border-red-200',
};

export function StorageBar({ pct, alert }: { pct: number; alert: string }) {
  const barColor =
    alert === 'CRITICAL_DISCHARGE'
      ? 'bg-red-500'
      : alert === 'WARNING'
      ? 'bg-orange-400'
      : alert === 'ADVISORY'
      ? 'bg-yellow-400'
      : 'bg-cyan-500';
  return (
    <div className="w-full bg-slate-100 rounded-full h-2.5 mt-1 overflow-hidden">
      <div
        className={`${barColor} h-2.5 rounded-full transition-all duration-500`}
        style={{ width: `${Math.min(100, Math.max(0, pct))}%` }}
      />
    </div>
  );
}

interface ReservoirPanelProps {
  isOpen?: boolean;
  onClose?: () => void;
  inline?: boolean;
}

export default function ReservoirPanel({
  isOpen = true,
  onClose,
  inline = false,
}: ReservoirPanelProps) {
  const [data, setData] = useState<ReservoirSummary | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [tab, setTab] = useState<'reservoirs' | 'rivers' | 'historical'>('reservoirs');

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const res = await fetch(`${API_BASE}/api/reservoirs`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const json = await res.json();
      setData(json.data);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to fetch reservoir data');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (inline || isOpen) fetchData();
  }, [inline, isOpen, fetchData]);

  if (!inline && !isOpen) return null;

  const content = (
    <div className="space-y-5">
      {inline && onClose && (
        <div className="flex items-center justify-between pb-2 border-b border-slate-200">
          <button
            onClick={onClose}
            className="flex items-center gap-2 text-sm font-semibold text-teal-700 hover:text-teal-900 transition-colors"
          >
            <ArrowLeft size={16} /> Back to Dashboard
          </button>
          <span className="text-xs text-slate-500">Live Hydrology Telemetry</span>
        </div>
      )}

      <div>
        <span className="eyebrow">RESERVOIR HYDROLOGY & RIVER SURGE</span>
        <h2 id="reservoir-title" className="text-xl font-bold flex items-center gap-2 text-slate-900">
          <Droplets size={22} className="text-teal-600" />
          Chennai Dam Storage & River Discharge Telemetry
        </h2>
        <p className="text-sm text-slate-600 mt-1">
          Real-time water levels, inflow/outflow cusecs, sluice gate operations under WRD safety SOPs, and downstream river flood surge projections.
        </p>
      </div>

      {data && (
        <div className="flex flex-wrap items-center gap-3 p-3.5 bg-slate-50 border border-slate-200 rounded-xl">
          <span
            className={`text-xs font-bold px-2.5 py-1 rounded-full border ${
              alertColors[data.highest_alert_level] || 'text-slate-700'
            } bg-white shadow-sm`}
          >
            DAM ALERT: {data.highest_alert_level.replace(/_/g, ' ')}
          </span>
          <span className="text-sm font-medium text-slate-700">
            Combined Storage: <strong>{data.overall_storage_pct}%</strong> ({data.total_storage_mcft.toLocaleString()} / {data.total_capacity_mcft.toLocaleString()} Mcft)
          </span>
          <span className="text-xs text-slate-500 ml-auto">
            Total Inflow: {data.total_inflow_cusecs.toLocaleString()} cusecs · Total Discharge: {data.total_discharge_cusecs.toLocaleString()} cusecs
          </span>
        </div>
      )}

      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-200 pb-3" role="group" aria-label="Reservoir sections">
        <div className="flex gap-2">
          {(['reservoirs', 'rivers', 'historical'] as const).map((t) => (
            <button
              key={t}
              aria-pressed={tab === t}
              onClick={() => setTab(t)}
              className={`px-3.5 py-1.5 rounded-lg text-sm font-semibold transition-all ${
                tab === t
                  ? 'bg-teal-700 text-white shadow-sm'
                  : 'bg-white border border-slate-200 text-slate-700 hover:bg-slate-50'
              }`}
            >
              {t === 'reservoirs' ? 'Major Reservoirs' : t === 'rivers' ? 'Downstream River Surges' : 'Historical Benchmarks'}
            </button>
          ))}
        </div>
        <button
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-white border border-slate-200 text-slate-700 hover:bg-slate-50 transition-colors"
          disabled={loading}
          onClick={fetchData}
          aria-label="Refresh telemetry"
        >
          <RefreshCw size={13} className={loading ? 'animate-spin text-teal-600' : ''} />
          <span>Refresh</span>
        </button>
      </div>

      {error && (
        <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
          {error}
        </div>
      )}

      <div className="space-y-3">
        {tab === 'reservoirs' && data?.reservoirs.map((r) => (
          <article key={r.id} className="p-4 bg-white border border-slate-200 rounded-xl shadow-sm hover:border-teal-500 transition-colors">
            <div className="flex justify-between items-start">
              <div>
                <h3 className="font-bold text-base text-slate-900">{r.name}</h3>
                <span className="text-xs text-slate-500">Primary River: {r.primary_river} · Impact: {r.impact_corridor?.join(', ')}</span>
              </div>
              <span className={`text-xs font-bold px-2.5 py-1 rounded-full border ${alertColors[r.alert_level] || 'text-slate-700'} bg-slate-50`}>
                {r.alert_level.replace(/_/g, ' ')}
              </span>
            </div>
            <div className="mt-3">
              <div className="flex justify-between text-xs text-slate-600 mb-1">
                <span>Storage Utilization</span>
                <span className="font-semibold text-slate-800">{r.storage_pct}% ({r.current_storage_mcft.toLocaleString()} / {r.total_capacity_mcft.toLocaleString()} Mcft)</span>
              </div>
              <StorageBar pct={r.storage_pct} alert={r.alert_level} />
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 mt-3.5 pt-3 border-t border-slate-100 text-xs">
              <div className="bg-slate-50 p-2 rounded-lg">
                <span className="text-slate-500">Water Level</span>
                <p className="text-sm font-bold text-slate-800 mt-0.5">{r.water_level_ft} ft <span className="text-xs font-normal text-slate-500">/ {r.full_tank_level_ft} FTL</span></p>
              </div>
              <div className="bg-slate-50 p-2 rounded-lg">
                <span className="text-slate-500">Inflow</span>
                <p className="text-sm font-bold text-teal-700 mt-0.5">{r.current_inflow_cusecs.toLocaleString()} <span className="text-xs font-normal text-slate-500">cusecs</span></p>
              </div>
              <div className="bg-slate-50 p-2 rounded-lg">
                <span className="text-slate-500">Discharge</span>
                <p className="text-sm font-bold text-orange-600 mt-0.5">{r.current_discharge_cusecs.toLocaleString()} <span className="text-xs font-normal text-slate-500">cusecs</span></p>
              </div>
              <div className="bg-slate-50 p-2 rounded-lg">
                <span className="text-slate-500">Sluice Gates</span>
                <p className="text-sm font-bold text-slate-800 mt-0.5">{r.gates_open} <span className="text-xs font-normal text-slate-500">/ {r.sluice_gates_count} open</span></p>
              </div>
            </div>
          </article>
        ))}

        {tab === 'rivers' && data?.river_surges && Object.entries(data.river_surges).map(([key, surge]) => (
          <article key={key} className={`p-4 rounded-xl border bg-white shadow-sm ${surgeColors[surge.status] || 'border-slate-200'}`}>
            <div className="flex justify-between items-start">
              <div>
                <h3 className="font-bold text-base text-slate-900 capitalize">{key.replace(/_/g, ' ')} River Basin</h3>
                <span className="text-xs text-slate-500">Fed by: {surge.governing_reservoir || surge.governing_reservoirs?.join(', ')}</span>
              </div>
              <span className="text-xs font-bold px-2.5 py-1 rounded-full bg-white border border-slate-200 text-slate-800">
                {surge.status.replace(/_/g, ' ')}
              </span>
            </div>
            <div className="grid grid-cols-2 gap-3 mt-3 text-xs">
              <div className="p-2.5 bg-slate-50 rounded-lg">
                <span className="text-slate-500">Total Discharge Flow</span>
                <p className="text-sm font-bold text-slate-800 mt-0.5">{surge.total_discharge_cusecs.toLocaleString()} cusecs</p>
              </div>
              <div className="p-2.5 bg-slate-50 rounded-lg flex items-center justify-between">
                <div>
                  <span className="text-slate-500">Projected Flood Surge</span>
                  <p className="text-sm font-bold text-red-600 mt-0.5">+{surge.projected_stage_surge_m} meters</p>
                </div>
                <Activity size={18} className="text-red-500 opacity-60" />
              </div>
            </div>
            <p className="text-xs text-slate-700 mt-2.5 bg-slate-50/70 p-2.5 rounded-lg border border-slate-100">{surge.advisory}</p>
            <div className="mt-2.5 flex flex-wrap items-center gap-1.5">
              <span className="text-xs font-semibold text-slate-600">Vulnerable GCC Zones:</span>
              {surge.vulnerable_gcc_zones.map((z) => (
                <span key={z} className="text-xs bg-slate-100 text-slate-700 px-2 py-0.5 rounded border border-slate-200">
                  {z}
                </span>
              ))}
            </div>
          </article>
        ))}

        {tab === 'historical' && <HistoricalBenchmarks />}
      </div>
    </div>
  );

  if (inline) {
    return <div className="max-w-4xl mx-auto py-2">{content}</div>;
  }

  return (
    <div className="dialog-backdrop" onClick={onClose}>
      <section
        role="dialog"
        aria-modal="true"
        aria-labelledby="reservoir-title"
        className="simple-dialog advisor-dialog"
        onClick={(e) => e.stopPropagation()}
        style={{ maxWidth: '780px' }}
      >
        <button className="dialog-close" aria-label="Close reservoir panel" onClick={onClose}>
          <X size={20} />
        </button>
        {content}
      </section>
    </div>
  );
}

function HistoricalBenchmarks() {
  const [benchmarks, setBenchmarks] = useState<Array<Record<string, unknown>>>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${API_BASE}/api/reservoirs/historical`)
      .then((r) => r.json())
      .then((d) => setBenchmarks(d.benchmarks || []))
      .catch(() => setBenchmarks([]))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p className="text-sm text-slate-600">Loading historical benchmark records…</p>;

  return (
    <div className="space-y-3">
      {benchmarks.map((b, i) => (
        <article key={i} className="p-4 bg-white border border-slate-200 rounded-xl shadow-sm">
          <h3 className="font-bold text-sm flex items-center gap-2 text-slate-900">
            <AlertTriangle size={15} className="text-amber-600" />
            {b.event_name as string}
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">{b.date as string}</p>
          <div className="grid grid-cols-2 gap-2 mt-2.5 text-xs">
            <div className="p-2 bg-slate-50 rounded-lg">
              <span className="text-slate-500">Chembarambakkam Peak</span>
              <p className="font-bold text-slate-800">{(b.chembarambakkam_peak_discharge_cusecs as number).toLocaleString()} cusecs</p>
            </div>
            <div className="p-2 bg-slate-50 rounded-lg">
              <span className="text-slate-500">Poondi Peak</span>
              <p className="font-bold text-slate-800">{(b.poondi_peak_discharge_cusecs as number).toLocaleString()} cusecs</p>
            </div>
          </div>
          <p className="text-xs text-slate-700 mt-2">{b.adyar_river_overflow_severity as string}</p>
          <p className="text-xs text-teal-700 mt-1 font-medium bg-teal-50 p-2 rounded border border-teal-100">
            💡 Operational Lesson: {b.key_lesson as string}
          </p>
        </article>
      ))}
      <p className="text-xs text-slate-500 pt-2">
        Sources: Kaggle Chennai Water Management Dataset · Tamil Nadu WRD Dam Archives · IEEE Xplore
      </p>
    </div>
  );
}
