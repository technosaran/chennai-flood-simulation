'use client';
import type { RescueFleetConfig, RescueVehiclePool } from '@/lib/types';

export const DEFAULT_RESCUE_FLEET: RescueFleetConfig = {
  enable_intermodal_transfers: true,
  continue_across_hours: true,
  planning_window_minutes: 60, base_location: [13.0838, 80.2764],
  trucks: { count: 6, seats: 24, speed_kmh: 30, handling_minutes: 10, ready_after_minutes: 0 },
  boats: { count: 4, seats: 12, speed_kmh: 15, handling_minutes: 10, ready_after_minutes: 0 },
  helicopters: { count: 1, seats: 6, speed_kmh: 120, handling_minutes: 10, ready_after_minutes: 0 },
};
const modes = ['trucks', 'boats', 'helicopters'] as const;
const fields: [keyof RescueVehiclePool, string, number, number][] = [
  ['count', 'Vehicles', 0, 20], ['seats', 'Seats per vehicle', 1, 100], ['speed_kmh', 'Planning speed km/h', 1, 180],
  ['handling_minutes', 'Loading / unloading minutes each', 5, 60], ['ready_after_minutes', 'Ready after minutes', 0, 240],
];

export default function RescueFleetControls({ value, onChange, disabled, shelters = [] }: { shelters?: { id: string; name: string }[]; value: RescueFleetConfig; onChange: (value: RescueFleetConfig) => void; disabled: boolean }) {
  const count = modes.reduce((n, mode) => n + value[mode].count, 0);
  return <fieldset disabled={disabled} className="rounded-xl border border-slate-200 bg-slate-50/70 p-4 space-y-4 mt-4">
    <legend className="font-semibold text-cyan-700 px-1">Limited rescue fleet</legend>
    <p className="text-sm text-slate-700">Dedicated rescue pool, separate from supply transport. Choose a continuing rescue schedule or independent snapshot plans below. Vehicles return to the base before reuse. Boats/air transfers remain provisional access estimates.</p>
    <label className="flex items-start gap-2 text-sm"><input type="checkbox" checked={value.continue_across_hours ?? false} onChange={e => onChange({ ...value, continue_across_hours: e.target.checked })} /><span>Continue rescues across hours: preserve busy vehicles, passenger commitments and shelter reservations. Turn off for independent snapshot comparisons.</span></label>
    <label className="flex items-start gap-2 text-sm"><input type="checkbox" checked={value.enable_intermodal_transfers ?? true} onChange={e => onChange({ ...value, enable_intermodal_transfers: e.target.checked })} /><span>Enable boat → truck transfers at modeled dry roadside points. Landing access is unverified; both vehicles must fit the planning window.</span></label>
    <label className="block text-sm">Rescue destination<select className="block w-full mt-1 rounded-lg border border-slate-200 bg-white p-2" value={value.destination_shelter_id ?? ''} onChange={e => onChange({ ...value, destination_shelter_id: e.target.value || null })}><option value="">Any dry shelter with spare capacity</option>{shelters.map(shelter => <option key={shelter.id} value={shelter.id}>{shelter.name}</option>)}</select><span className="text-xs text-slate-600">Limits rescue destinations only. Compromised or full shelters remain unavailable.</span></label>
    <label className="block text-sm">Planning window (minutes)<input type="number" min={15} max={240} value={value.planning_window_minutes} onChange={e => { if (Number.isFinite(e.target.valueAsNumber)) onChange({ ...value, planning_window_minutes: Math.max(15, Math.min(240, e.target.valueAsNumber)) }); }} className="block w-full mt-1 rounded-lg border border-slate-200 bg-slate-50 p-2" /></label>
    <div className="grid grid-cols-2 gap-2">{(['Latitude', 'Longitude'] as const).map((label, i) => <label key={label} className="text-sm">Base {label.toLowerCase()}<input type="number" step="0.0001" min={i ? 80 : 12.8} max={i ? 80.4 : 13.35} value={value.base_location[i]} onChange={e => { if (Number.isFinite(e.target.valueAsNumber)) { const base: [number, number] = [...value.base_location]; base[i] = e.target.valueAsNumber; onChange({ ...value, base_location: base }); } }} className="block w-full mt-1 rounded-lg border border-slate-200 bg-slate-50 p-2" /></label>)}</div>
    {modes.map(mode => <details key={mode}><summary className="cursor-pointer capitalize text-sm font-semibold">{mode} · {value[mode].count} vehicles × {value[mode].seats} seats</summary><div className="grid grid-cols-2 gap-3 mt-3">{fields.map(([field, label, min, max]) => <label key={field} className="text-sm">{mode} {label.toLowerCase()}<input type="number" min={min} max={max} step={1} value={value[mode][field]} onChange={e => { if (Number.isFinite(e.target.valueAsNumber)) onChange({ ...value, [mode]: { ...value[mode], [field]: Math.max(min, Math.min(max, e.target.valueAsNumber)) } }); }} className="block w-full mt-1 rounded-lg border border-slate-200 bg-slate-50 p-2" /></label>)}</div></details>)}
    <p className={`text-sm ${count > 30 ? 'text-amber-800' : 'text-slate-700'}`} role="status">{count} vehicles configured. Maximum 30 in total. Setting all counts to zero models no rescue fleet.</p>
  </fieldset>;
}
