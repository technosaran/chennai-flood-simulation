import type { Coordinates, RescueFleetPlan } from './types';

type Trip = RescueFleetPlan['trips'][number];
const distance = (a: number[], b: number[]) => Math.hypot((a[0]-b[0])*Math.cos((a[1]+b[1])*Math.PI/360), a[1]-b[1]);

export function positionAlongLine(points: number[][], fraction: number): Coordinates | null {
  if (!points.length) return null;
  const lengths = points.slice(1).map((point, i) => distance(points[i], point));
  const total = lengths.reduce((sum, n) => sum+n, 0);
  let remaining = Math.max(0, Math.min(1, fraction))*total;
  for (let i=0; i<lengths.length; i++) {
    if (lengths[i] > 0 && remaining <= lengths[i]) {
      const ratio = remaining/lengths[i];
      return [points[i][1]+(points[i+1][1]-points[i][1])*ratio, points[i][0]+(points[i+1][0]-points[i][0])*ratio];
    }
    remaining -= lengths[i];
  }
  const last = points[points.length-1];
  return [last[1], last[0]];
}

export function vehicleAtMinute(trips: Trip[], minute: number) {
  const ordered = [...trips].sort((a,b) => a.depart_minutes-b.depart_minutes);
  const active = ordered.find(trip => minute >= trip.depart_minutes && minute < trip.return_available_minutes);
  if (active?.phases?.length) {
    const phase = active.phases.find(item => minute >= item.start_minutes && minute < item.end_minutes);
    if (phase) return { trip: active, status: phase.status, position: positionAlongLine(phase.geometry.coordinates, (minute-phase.start_minutes)/(phase.end_minutes-phase.start_minutes)) };
  }
  const first = ordered[0];
  if (!first?.geometry?.coordinates.length) return null;
  // Old archived trips have no phases: keep their routes visible without
  // inventing a timed position.
  if (active && !active.phases?.length) return null;
  return { trip: first, status: minute < first.depart_minutes ? 'not_ready' : 'ready_at_base', position: positionAlongLine(first.geometry.coordinates, 0) };
}
