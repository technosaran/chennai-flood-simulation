'use client';
import { useEffect, useMemo, useState } from 'react';
import { CircleMarker, Popup, Tooltip } from 'react-leaflet';
import type { RescueFleetPlan } from '@/lib/types';
import { vehicleAtMinute } from '@/lib/fleet-playback';

export function useRescuePlayback(plan?: RescueFleetPlan | null) {
  const start = plan?.playback_start_minutes ?? 0;
  const end = Math.max(plan?.playback_end_minutes ?? plan?.planning_window_minutes ?? 0, ...((plan?.trips ?? []).map(t => t.return_available_minutes)));
  const [playback, setPlayback] = useState({ minute: 0, playing: false, speed: 1 });
  useEffect(() => { setPlayback({ minute: start, playing: false, speed: 1 }); }, [plan, start]);
  useEffect(() => {
    if (!playback.playing || end <= 0) return;
    let last = performance.now();
    const timer = window.setInterval(() => {
      const now = performance.now();
      const elapsed = (now-last)/1000;
      last = now;
      setPlayback(previous => {
        const minute = Math.min(end, previous.minute+elapsed*previous.speed);
        return { ...previous, minute, playing: minute < end };
      });
    }, 100);
    return () => window.clearInterval(timer);
  }, [playback.playing, end]);
  return { ...playback, start, end, setPlayback };
}

type Playback = ReturnType<typeof useRescuePlayback>;
export function RescuePlaybackControls({ plan, playback }: { plan?: RescueFleetPlan | null; playback: Playback }) {
  const supported = plan?.trips.some(trip => trip.phases?.length);
  if (!plan || !supported) return null;
  const completed = plan.journeys?.filter(j => j.completed_minutes <= playback.minute).reduce((n,j) => n+j.people, 0) ?? 0;
  return <div className="relative shrink-0 border-t border-cyan-200 bg-white p-3 text-slate-900" aria-label="Rescue vehicle playback">
    <div className="flex flex-wrap items-center gap-2 text-xs mb-2"><strong>Rescue replay</strong><span>{plan.mode === 'continuous' ? 'T+' : ''}{playback.minute.toFixed(1)} / {playback.end.toFixed(1)} min</span><span>{completed.toLocaleString()} {plan.mode === 'continuous' ? 'cumulative simulated arrivals' : 'planned arrivals'}</span></div>
    <div className="flex items-center gap-2"><button type="button" className="rounded border px-2 py-1 text-xs" disabled={playback.end <= playback.start} onClick={() => playback.setPlayback(p => ({ ...p, playing: !p.playing, minute: p.minute >= playback.end ? playback.start : p.minute }))}>{playback.playing ? 'Pause rescue replay' : 'Play rescue replay'}</button><label className="text-xs">Speed<select aria-label="Rescue replay speed" className="ml-1 rounded border" value={playback.speed} onChange={e => playback.setPlayback(p => ({ ...p, speed: Number(e.target.value) }))}>{[1,5,15,30].map(speed => <option key={speed} value={speed}>{speed}×</option>)}</select></label></div>
    <label className="block text-xs mt-2">Rescue time<input aria-label="Rescue playback minute" className="w-full" type="range" min={playback.start} max={playback.end} step={.1} value={playback.minute} onChange={e => playback.setPlayback(p => ({ ...p, minute: Number(e.target.value), playing: false }))} /></label>
    <p className="text-[10px]">Scheduled simulation · blue trucks · cyan boats · purple air · includes return trips</p>
  </div>;
}

export function FleetVehicleMarkers({ plan, minute }: { plan?: RescueFleetPlan | null; minute: number }) {
  const grouped = useMemo(() => {
    const result = new Map<string, RescueFleetPlan['trips']>();
    for (const trip of plan?.trips ?? []) result.set(trip.vehicle_id, [...(result.get(trip.vehicle_id) ?? []), trip]);
    return Array.from(result.entries());
  }, [plan]);
  return <>{grouped.map(([vid, trips]) => {
    const state = vehicleAtMinute(trips, minute);
    if (!state?.position) return null;
    const color = state.trip.mode === 'trucks' ? '#2563eb' : state.trip.mode === 'boats' ? '#0891b2' : '#9333ea';
    return <CircleMarker key={vid} center={state.position} radius={8} pathOptions={{ color: '#ffffff', weight: 2, fillColor: color, fillOpacity: 1 }}>
      <Tooltip direction="top">{vid} · {state.status.replaceAll('_', ' ')}</Tooltip>
      <Popup><strong>{vid}</strong><p>{state.status.replaceAll('_', ' ')} · {minute.toFixed(1)} min</p><p>{state.trip.people} passengers scheduled · {state.trip.destination_name}</p><p>{state.trip.feasibility}</p></Popup>
    </CircleMarker>;
  })}</>;
}
