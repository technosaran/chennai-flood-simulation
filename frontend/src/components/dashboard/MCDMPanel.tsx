'use client';

import { useEffect, useState, useCallback } from 'react';
import { Target, X, RefreshCw, ArrowDown, Shield, ArrowLeft } from 'lucide-react';

export interface MCDMZoneRanking {
  zone_number: number;
  zone_id: string;
  zone_name: string;
  key_localities: string[];
  drainage_basin: string;
  centroid: [number, number];
  raw_metrics: {
    flood_depth_m: number;
    affected_population: number;
    isolation_factor: number;
    elevation_m: number;
    baseline_vulnerability: number;
  };
  topsis_score: number;
  relative_closeness_pct: number;
  priority_tier: string;
  recommended_action: string;
  dispatch_rank: number;
}

export interface MCDMData {
  methodology: string;
  criteria_weights: Record<string, number>;
  total_ranked_zones: number;
  p1_critical_count: number;
  p2_high_count: number;
  rankings: MCDMZoneRanking[];
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const tierColors: Record<string, string> = {
  P1_IMMEDIATE_DISPATCH: 'bg-red-50/70 border-red-200 text-red-800',
  P2_HIGH_PRIORITY: 'bg-orange-50/70 border-orange-200 text-orange-800',
  P3_MODERATE_STANDBY: 'bg-yellow-50/70 border-yellow-200 text-yellow-800',
  P4_ROUTINE_MONITORING: 'bg-slate-50 border-slate-200 text-slate-700',
};

const tierLabels: Record<string, string> = {
  P1_IMMEDIATE_DISPATCH: '🔴 P1 Immediate Dispatch',
  P2_HIGH_PRIORITY: '🟠 P2 High Priority',
  P3_MODERATE_STANDBY: '🟡 P3 Moderate Standby',
  P4_ROUTINE_MONITORING: '🟢 P4 Routine Monitoring',
};

interface MCDMPanelProps {
  isOpen?: boolean;
  onClose?: () => void;
  inline?: boolean;
}

export default function MCDMPanel({
  isOpen = true,
  onClose,
  inline = false,
}: MCDMPanelProps) {
  const [data, setData] = useState<MCDMData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const res = await fetch(`${API_BASE}/api/advisory/mcdm`);
      if (res.status === 409) {
        setError('Run a simulation first to generate TOPSIS multi-criteria rankings.');
        return;
      }
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const json = await res.json();
      setData(json.mcdm_topsis_rankings);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to fetch MCDM data');
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
          <span className="text-xs text-slate-500">IEEE Multi-Criteria Decision Analysis</span>
        </div>
      )}

      <div>
        <span className="eyebrow">IEEE DECISION SUPPORT ENGINE</span>
        <h2 id="mcdm-title" className="text-xl font-bold flex items-center gap-2 text-slate-900">
          <Target size={22} className="text-teal-600" />
          TOPSIS Multi-Criteria Relief Dispatch Matrix
        </h2>
        <p className="text-sm text-slate-600 mt-1">
          Objective multi-criteria ranking of vulnerable zones using Euclidean distance to ideal disaster solutions (flood depth, affected population, isolation, elevation).
        </p>
      </div>

      {data && (
        <div className="flex flex-wrap items-center gap-3 p-3.5 bg-slate-50 border border-slate-200 rounded-xl">
          <span className="text-xs bg-red-100 text-red-800 px-2.5 py-1 rounded-full font-bold border border-red-200">
            {data.p1_critical_count} zones P1 Critical
          </span>
          <span className="text-xs bg-orange-100 text-orange-800 px-2.5 py-1 rounded-full font-bold border border-orange-200">
            {data.p2_high_count} zones P2 High
          </span>
          <span className="text-sm text-slate-700">
            <strong>{data.total_ranked_zones}</strong> zones evaluated
          </span>
          <button
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-white border border-slate-200 text-slate-700 hover:bg-slate-50 ml-auto transition-colors"
            disabled={loading}
            onClick={fetchData}
            aria-label="Refresh MCDM"
          >
            <RefreshCw size={13} className={loading ? 'animate-spin text-teal-600' : ''} />
            <span>Refresh</span>
          </button>
        </div>
      )}

      {!data && !error && !loading && (
        <div className="p-8 text-center bg-white border border-dashed border-slate-300 rounded-xl">
          <Target size={32} className="mx-auto text-slate-400 mb-2" />
          <p className="text-sm font-semibold text-slate-800">No MCDM Rankings Available</p>
          <p className="text-xs text-slate-500 mt-1">Run a flood simulation scenario first to calculate TOPSIS dispatch priorities.</p>
        </div>
      )}

      {error && (
        <div className="p-3.5 bg-amber-50 border border-amber-200 rounded-xl text-sm text-amber-900">
          {error}
        </div>
      )}

      {loading && (
        <div className="p-6 text-center text-sm text-slate-600 flex items-center justify-center gap-2">
          <RefreshCw size={16} className="animate-spin text-teal-600" />
          <span>Computing IEEE TOPSIS geometric closeness scores…</span>
        </div>
      )}

      {data && (
        <div className="space-y-3">
          {/* Criteria Weights Summary */}
          <details className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm" open>
            <summary className="cursor-pointer text-sm font-bold text-slate-800 flex items-center justify-between">
              <span className="flex items-center gap-2">
                <Shield size={16} className="text-teal-600" />
                TOPSIS Criteria Normalized Weights
              </span>
              <span className="text-xs text-teal-700 font-normal">Click to toggle</span>
            </summary>
            <div className="grid grid-cols-2 sm:grid-cols-5 gap-2 mt-3 pt-3 border-t border-slate-100 text-xs">
              {Object.entries(data.criteria_weights).map(([key, val]) => (
                <div key={key} className="bg-slate-50 p-2.5 rounded-lg border border-slate-100">
                  <span className="text-slate-500 capitalize">{key.replace(/_/g, ' ')}</span>
                  <p className="text-sm font-bold text-slate-800 mt-0.5">{(val * 100).toFixed(0)}%</p>
                </div>
              ))}
            </div>
            <p className="text-xs text-slate-500 mt-2.5">
              Algorithm: {data.methodology}
            </p>
          </details>

          {/* Zone Rankings */}
          <div className="space-y-3">
            {data.rankings.map((zone) => (
              <article
                key={zone.zone_id}
                className={`p-4 bg-white border rounded-xl shadow-sm ${
                  tierColors[zone.priority_tier] || 'border-slate-200'
                }`}
              >
                <div className="flex justify-between items-start">
                  <div className="flex items-center gap-2.5">
                    <span className="w-8 h-8 rounded-lg bg-slate-900 text-white font-bold text-sm flex items-center justify-center shadow-sm">
                      #{zone.dispatch_rank}
                    </span>
                    <div>
                      <h3 className="font-bold text-base text-slate-900">{zone.zone_name}</h3>
                      <p className="text-xs text-slate-600">Localities: {zone.key_localities.join(', ')}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <span className="text-xs font-bold px-2 py-0.5 rounded-full bg-white border border-slate-200">
                      {tierLabels[zone.priority_tier] || zone.priority_tier}
                    </span>
                    <p className="text-base font-bold text-slate-900 mt-1">
                      {zone.relative_closeness_pct}% Closeness
                    </p>
                  </div>
                </div>

                <div className="w-full bg-slate-100 rounded-full h-2 mt-2.5 overflow-hidden">
                  <div
                    className={`h-2 rounded-full transition-all ${
                      zone.priority_tier === 'P1_IMMEDIATE_DISPATCH'
                        ? 'bg-red-500'
                        : zone.priority_tier === 'P2_HIGH_PRIORITY'
                        ? 'bg-orange-500'
                        : zone.priority_tier === 'P3_MODERATE_STANDBY'
                        ? 'bg-yellow-400'
                        : 'bg-slate-300'
                    }`}
                    style={{ width: `${Math.min(100, Math.max(0, zone.relative_closeness_pct))}%` }}
                  />
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-5 gap-2 mt-3 pt-2.5 border-t border-slate-100 text-xs">
                  <div className="bg-slate-50 p-2 rounded-lg">
                    <span className="text-slate-500">Flood Depth</span>
                    <p className="font-bold text-slate-800">{zone.raw_metrics.flood_depth_m} m</p>
                  </div>
                  <div className="bg-slate-50 p-2 rounded-lg">
                    <span className="text-slate-500">Affected People</span>
                    <p className="font-bold text-slate-800">{zone.raw_metrics.affected_population.toLocaleString()}</p>
                  </div>
                  <div className="bg-slate-50 p-2 rounded-lg">
                    <span className="text-slate-500">Road Isolation</span>
                    <p className="font-bold text-slate-800">{(zone.raw_metrics.isolation_factor * 100).toFixed(0)}%</p>
                  </div>
                  <div className="bg-slate-50 p-2 rounded-lg">
                    <span className="text-slate-500">Avg Elevation</span>
                    <p className="font-bold text-slate-800">{zone.raw_metrics.elevation_m} m MSL</p>
                  </div>
                  <div className="bg-slate-50 p-2 rounded-lg">
                    <span className="text-slate-500">Drainage Basin</span>
                    <p className="font-bold text-slate-800 truncate" title={zone.drainage_basin}>
                      {zone.drainage_basin}
                    </p>
                  </div>
                </div>

                <p className="text-xs text-teal-800 mt-2.5 bg-teal-50/70 p-2.5 rounded-lg border border-teal-100 flex items-start gap-1.5 font-medium">
                  <ArrowDown size={14} className="mt-0.5 shrink-0 text-teal-700" />
                  <span><strong>Recommended Protocol:</strong> {zone.recommended_action}</span>
                </p>
              </article>
            ))}
          </div>
        </div>
      )}
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
        aria-labelledby="mcdm-title"
        className="simple-dialog advisor-dialog"
        onClick={(e) => e.stopPropagation()}
        style={{ maxWidth: '780px' }}
      >
        <button className="dialog-close" aria-label="Close MCDM panel" onClick={onClose}>
          <X size={20} />
        </button>
        {content}
      </section>
    </div>
  );
}
