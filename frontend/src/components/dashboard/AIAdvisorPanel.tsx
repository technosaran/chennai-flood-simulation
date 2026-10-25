'use client';

import { useEffect, useState } from 'react';
import { Check, Copy, Download, RefreshCw, X, Target, ArrowLeft, Sparkles } from 'lucide-react';
import { AIAdvisorData } from '@/lib/types';

interface Props {
  isOpen?: boolean;
  onClose?: () => void;
  advisorData: AIAdvisorData | null;
  onRefresh?: () => void | Promise<void>;
  inline?: boolean;
}

export default function AIAdvisorPanel({
  isOpen = true,
  onClose,
  advisorData,
  onRefresh,
  inline = false,
}: Props) {
  const [tab, setTab] = useState<'priorities' | 'bulletin' | 'roads' | 'wards' | 'topsis'>('priorities');
  const [language, setLanguage] = useState<'english' | 'tamil'>('english');
  const [message, setMessage] = useState('');
  const [refreshing, setRefreshing] = useState(false);
  const [reviewed, setReviewed] = useState<string[]>([]);

  useEffect(() => {
    setReviewed([]);
    setMessage('');
  }, [advisorData]);

  if (!inline && !isOpen) return null;

  const text = advisorData?.broadcast[language] || '';

  const download = () => {
    const url = URL.createObjectURL(new Blob([text], { type: 'text/plain;charset=utf-8' }));
    const a = document.createElement('a');
    a.href = url;
    a.download = `scenario-bulletin-${language}.txt`;
    a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  };

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(text);
      setMessage('Copied bulletin to clipboard.');
    } catch {
      setMessage('Clipboard unavailable. Use Download text.');
    }
  };

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
          <span className="text-xs text-slate-500">Autonomous Incident Command Decision Support</span>
        </div>
      )}

      <div>
        <span className="eyebrow">AI TACTICAL ADVISORY & INCIDENT COMMAND</span>
        <h2 id="advisor-title" className="text-xl font-bold flex items-center gap-2 text-slate-900">
          <Sparkles size={22} className="text-teal-600" />
          Autonomous Response Guidance & Public Warning System
        </h2>
        <p className="text-sm text-slate-600 mt-1">
          Synthesizes hydrodynamic simulations, road isolation graphs, and demographic density into tactical directives and emergency broadcasts.
        </p>
      </div>

      {!advisorData ? (
        <div className="p-8 text-center bg-white border border-dashed border-slate-300 rounded-xl">
          <Sparkles size={32} className="mx-auto text-slate-400 mb-2" />
          <p className="text-sm font-semibold text-slate-800">No Advisory Available</p>
          <p className="text-xs text-slate-500 mt-1">Run a flood simulation scenario first to generate tactical response recommendations.</p>
        </div>
      ) : (
        <>
          <div className="p-4 bg-teal-50/70 border border-teal-200 rounded-xl">
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs font-bold px-2 py-0.5 rounded bg-teal-700 text-white">
                TACTICAL SITUATION
              </span>
              <span className="text-xs font-semibold text-teal-800">
                Threat Level: {advisorData.risk_radar_level} (Score {advisorData.radar_score}/100)
              </span>
            </div>
            <p className="text-sm font-medium text-slate-800">{advisorData.tactical_summary}</p>
            {advisorData.snapshot_hour !== undefined && (
              <p className="text-xs text-slate-500 mt-1.5">
                Advice describes the final snapshot at hour T+{advisorData.snapshot_hour}h. Use Impact Analytics to inspect other time steps.
              </p>
            )}
          </div>

          <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-200 pb-3" role="group" aria-label="Advice sections">
            <div className="flex flex-wrap gap-2">
              {(['priorities', 'bulletin', 'roads', 'wards', 'topsis'] as const).map((t) => (
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
                  {t === 'priorities'
                    ? 'Evacuation Priorities'
                    : t === 'bulletin'
                    ? 'Emergency Broadcast'
                    : t === 'roads'
                    ? 'Severed Corridors'
                    : t === 'wards'
                    ? 'Ward Vulnerability'
                    : 'IEEE TOPSIS Matrix'}
                </button>
              ))}
            </div>
            {onRefresh && (
              <button
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-white border border-slate-200 text-slate-700 hover:bg-slate-50 transition-colors"
                disabled={refreshing}
                aria-label="Refresh recommendations"
                onClick={async () => {
                  setRefreshing(true);
                  try {
                    await onRefresh();
                  } catch {
                    setMessage('Refresh failed. Try again.');
                  } finally {
                    setRefreshing(false);
                  }
                }}
              >
                <RefreshCw size={13} className={refreshing ? 'animate-spin text-teal-600' : ''} />
                <span>Recompute</span>
              </button>
            )}
          </div>

          <div className="space-y-3">
            {tab === 'priorities' && (
              <div className="space-y-3">
                {advisorData.evacuation_advice.length ? (
                  advisorData.evacuation_advice.map((item) => (
                    <article key={item.id} className="p-4 bg-white border border-slate-200 rounded-xl shadow-sm">
                      <div className="flex justify-between items-start">
                        <span className="text-xs font-bold px-2 py-0.5 rounded bg-red-100 text-red-800 border border-red-200">
                          {item.priority}
                        </span>
                        <span className="text-xs text-slate-500 font-medium">Mode: {item.mode_suggested}</span>
                      </div>
                      <h3 className="font-bold text-base text-slate-900 mt-2">{item.title}</h3>
                      <p className="text-sm text-slate-700 my-2">{item.details}</p>
                      <button
                        className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold border transition-colors ${
                          reviewed.includes(item.id)
                            ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
                            : 'bg-slate-50 text-slate-700 border-slate-200 hover:bg-slate-100'
                        }`}
                        disabled={reviewed.includes(item.id)}
                        onClick={() => setReviewed((ids) => [...ids, item.id])}
                      >
                        <Check size={14} />
                        {reviewed.includes(item.id) ? 'Acknowledged in this session' : 'Acknowledge Priority'}
                      </button>
                    </article>
                  ))
                ) : (
                  <p className="text-sm text-slate-600 p-4 bg-white rounded-xl border border-slate-200">
                    No critical stranded population traps detected in this scenario.
                  </p>
                )}
              </div>
            )}

            {tab === 'bulletin' && (
              <div className="space-y-3 bg-white border border-slate-200 p-4 rounded-xl shadow-sm">
                <div className="flex gap-2">
                  {(['english', 'tamil'] as const).map((l) => (
                    <button
                      className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
                        language === l
                          ? 'bg-teal-700 text-white'
                          : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
                      }`}
                      key={l}
                      aria-pressed={language === l}
                      onClick={() => {
                        setLanguage(l);
                        setMessage('');
                      }}
                    >
                      {l === 'tamil' ? 'தமிழ் (Tamil)' : 'English'}
                    </button>
                  ))}
                </div>
                <div className="p-4 bg-slate-50 rounded-xl border border-slate-200">
                  <p className="text-sm leading-relaxed text-slate-800 whitespace-pre-line font-serif" lang={language === 'tamil' ? 'ta' : 'en'}>
                    {text}
                  </p>
                </div>
                <div className="flex flex-wrap gap-2 pt-1">
                  <button className="flex items-center gap-1.5 px-3.5 py-1.5 bg-white border border-slate-200 rounded-lg text-xs font-semibold text-slate-700 hover:bg-slate-50 shadow-sm" onClick={copy}>
                    <Copy size={13} /> Copy Broadcast Text
                  </button>
                  <button className="flex items-center gap-1.5 px-3.5 py-1.5 bg-white border border-slate-200 rounded-lg text-xs font-semibold text-slate-700 hover:bg-slate-50 shadow-sm" onClick={download}>
                    <Download size={13} /> Export Text File
                  </button>
                </div>
                <p className="text-xs text-slate-500">
                  Civil defense emergency broadcast text calibrated for public sirens, SMS alerts, and media distribution.
                </p>
              </div>
            )}

            {tab === 'roads' && (
              <div className="space-y-3">
                {advisorData.bottlenecks.length ? (
                  advisorData.bottlenecks.map((b) => (
                    <article className="p-4 bg-white border border-slate-200 rounded-xl shadow-sm" key={b.id}>
                      <div className="flex justify-between items-start">
                        <h3 className="font-bold text-sm text-slate-900">{b.corridor_name}</h3>
                        <span className="text-xs font-bold px-2 py-0.5 rounded bg-amber-100 text-amber-800 border border-amber-200">
                          {b.traffic_choke_status}
                        </span>
                      </div>
                      <p className="text-xs text-slate-600 mt-1">Water Depth: <strong>{b.water_depth_m} m</strong> · Network: {b.zone}</p>
                      <p className="text-xs text-teal-800 mt-2 bg-teal-50 p-2 rounded border border-teal-100">
                        Suggested Detour: {b.suggested_detour}
                      </p>
                    </article>
                  ))
                ) : (
                  <p className="text-sm text-slate-600 p-4 bg-white rounded-xl border border-slate-200">
                    All major road corridors remain traversable without severe choke points.
                  </p>
                )}
              </div>
            )}

            {tab === 'wards' && (
              <div className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-sm">
                <div className="overflow-x-auto">
                  <table className="w-full text-xs text-left">
                    <thead className="bg-slate-50 border-b border-slate-200">
                      <tr>
                        <th className="p-3 font-bold text-slate-700">GCC Ward / Zone</th>
                        <th className="p-3 font-bold text-slate-700">Vulnerability Score</th>
                        <th className="p-3 font-bold text-slate-700">Peak Flood Depth</th>
                        <th className="p-3 font-bold text-slate-700">Status Trend</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {advisorData.ward_rankings.map((w) => (
                        <tr key={w.ward_id} className="hover:bg-slate-50">
                          <td className="p-3 font-semibold text-slate-800">{w.ward_name}</td>
                          <td className="p-3">
                            <span className="font-bold text-slate-900">{w.risk_index}</span>/100
                          </td>
                          <td className="p-3 font-medium text-slate-800">{w.water_depth_m} m</td>
                          <td className="p-3">
                            <span
                              className={`px-2 py-0.5 rounded-full font-bold text-[10px] ${
                                w.trend === 'rising'
                                  ? 'bg-red-100 text-red-800'
                                  : w.trend === 'peaking'
                                  ? 'bg-amber-100 text-amber-800'
                                  : 'bg-emerald-100 text-emerald-800'
                              }`}
                            >
                              {w.trend.toUpperCase()}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {tab === 'topsis' && (
              <div className="space-y-3">
                <div className="flex justify-between items-center text-xs text-slate-600 p-2 bg-slate-50 rounded-lg border border-slate-200">
                  <span className="flex items-center gap-1.5 font-bold text-slate-800">
                    <Target size={14} className="text-teal-700" /> IEEE TOPSIS Multi-Criteria Relief Dispatch Matrix
                  </span>
                  <span>{advisorData.mcdm_topsis_rankings?.methodology || 'IEEE MCDM Algorithm'}</span>
                </div>
                {advisorData.mcdm_topsis_rankings?.rankings?.length ? (
                  <div className="space-y-2.5 max-h-[55vh] overflow-y-auto pr-1">
                    {advisorData.mcdm_topsis_rankings.rankings.map((zone) => (
                      <article
                        key={zone.zone_id}
                        className={`p-3.5 bg-white border rounded-xl shadow-sm ${
                          zone.priority_tier === 'P1_IMMEDIATE_DISPATCH'
                            ? 'border-red-300 bg-red-50/20'
                            : zone.priority_tier === 'P2_HIGH_PRIORITY'
                            ? 'border-orange-300 bg-orange-50/20'
                            : 'border-slate-200'
                        }`}
                      >
                        <div className="flex justify-between items-start">
                          <div className="flex items-center gap-2">
                            <span className="w-6 h-6 rounded bg-slate-900 text-white font-bold text-xs flex items-center justify-center">
                              #{zone.dispatch_rank}
                            </span>
                            <div>
                              <h4 className="font-bold text-sm text-slate-900">{zone.zone_name}</h4>
                              <p className="text-xs text-slate-500">{zone.key_localities.join(', ')}</p>
                            </div>
                          </div>
                          <div className="text-right">
                            <span
                              className={`text-xs font-bold px-2 py-0.5 rounded-full ${
                                zone.priority_tier === 'P1_IMMEDIATE_DISPATCH'
                                  ? 'bg-red-100 text-red-800'
                                  : zone.priority_tier === 'P2_HIGH_PRIORITY'
                                  ? 'bg-orange-100 text-orange-800'
                                  : 'bg-yellow-100 text-yellow-800'
                              }`}
                            >
                              {zone.priority_tier.replace(/_/g, ' ')}
                            </span>
                            <p className="text-xs font-bold text-slate-800 mt-1">{zone.relative_closeness_pct}%</p>
                          </div>
                        </div>
                        <div className="grid grid-cols-4 gap-2 mt-2 pt-2 border-t border-slate-100 text-xs text-slate-600">
                          <div>Flood: <strong>{zone.raw_metrics.flood_depth_m}m</strong></div>
                          <div>Affected: <strong>{zone.raw_metrics.affected_population.toLocaleString()}</strong></div>
                          <div>Elevation: <strong>{zone.raw_metrics.elevation_m}m</strong></div>
                          <div>Isolation: <strong>{(zone.raw_metrics.isolation_factor * 100).toFixed(0)}%</strong></div>
                        </div>
                        <p className="text-xs text-teal-800 mt-2 font-medium">→ Directive: {zone.recommended_action}</p>
                      </article>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-slate-600 p-4 bg-white rounded-xl border border-slate-200">
                    Run a scenario to calculate IEEE TOPSIS priority dispatch rankings.
                  </p>
                )}
              </div>
            )}
          </div>
          {message && <p role="status" className="text-xs text-teal-700 mt-2 font-medium">{message}</p>}
        </>
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
        aria-labelledby="advisor-title"
        className="simple-dialog advisor-dialog"
        onClick={(e) => e.stopPropagation()}
        style={{ maxWidth: '780px' }}
      >
        <button className="dialog-close" aria-label="Close scenario advice" onClick={onClose}>
          <X size={20} />
        </button>
        {content}
      </section>
    </div>
  );
}
