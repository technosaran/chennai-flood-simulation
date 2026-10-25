'use client';

import { X } from 'lucide-react';
import { RouteInspectionData } from '@/lib/types';

interface Props { route: RouteInspectionData | null; isOpen: boolean; onClose: () => void; }

export default function RouteInspectorModal({ route, isOpen, onClose }: Props) {
  if (!isOpen || !route) return null;
  const mode = { truck: 'Truck', foot: 'On foot', amphibious: 'Amphibious craft', helicopter: 'Helicopter' }[route.transport_mode];
  return <div className="dialog-backdrop" onClick={onClose}>
    <section role="dialog" aria-modal="true" aria-labelledby="route-title" className="simple-dialog" onClick={e => e.stopPropagation()}>
      <button className="dialog-close" onClick={onClose} aria-label="Close route details"><X size={20} /></button>
      <span className="eyebrow">{route.route_category.toUpperCase()} ROUTE</span>
      <h2 id="route-title">{route.source_name || 'Origin'} → {route.destination_name || 'Destination'}</h2>
      <dl className="grid grid-cols-2 gap-4 my-5 text-sm">
        <div><dt className="text-slate-700">Transport</dt><dd className="mt-1 font-semibold">{mode}</dd></div>
        <div><dt className="text-slate-700">Status</dt><dd className="mt-1 capitalize">{route.status.replaceAll('_', ' ')}</dd></div>
        <div><dt className="text-slate-700">Distance</dt><dd className="mt-1">{route.distance_km.toFixed(2)} km</dd></div>
        <div><dt className="text-slate-700">Estimated time</dt><dd className="mt-1">{route.transit_time_min.toFixed(1)} min</dd></div>
      </dl>
      {route.route_category === 'evacuation' ? <p className="advice-card text-sm">{route.evacuee_or_capacity_count.toLocaleString()} people assigned to this route.</p> : <div className="advice-card">
        <h3 className="text-sm font-semibold mb-3">Supply manifest</h3>
        <dl className="grid grid-cols-3 gap-2 text-sm"><div><dt className="text-slate-700">Water</dt><dd>{route.manifest.water_litres.toLocaleString()} L</dd></div><div><dt className="text-slate-700">Food</dt><dd>{route.manifest.food_rations.toLocaleString()} rations</dd></div><div><dt className="text-slate-700">Medicine</dt><dd>{route.manifest.medical_kits.toLocaleString()} kits</dd></div></dl>
        {route.manifest.water_litres + route.manifest.food_rations + route.manifest.medical_kits === 0 && <p className="mt-3 text-sm text-amber-800">This route has no allocated cargo at this hour. The route shows a modeled connection; it is not a completed delivery. Inspect Relief & supplies for remaining stock and unmet demand.</p>}
      </div>}
      {route.network_source && <p className="text-sm text-slate-700 mt-4">Streets: {route.network_source}{route.network_timestamp ? ` · Snapshot ${route.network_timestamp.slice(0,10)}` : ''}</p>}
      {!!route.access_connectors_m?.length && <p className="text-sm text-amber-800 mt-3">Unverified access approaches: {route.access_connectors_m.map(x => `${Math.round(x)} m`).join(' + ')}. Distance includes these approaches.</p>}
      {route.transport_mode === 'amphibious' && <p className="text-sm text-amber-800 mt-3">Amphibious route uses road corridors as a planning proxy. Waterway navigability is unverified.</p>}
      {route.access_note && <p className="text-sm text-slate-700 mt-3">{route.access_note}</p>}
      {route.recommendation && <p className="mt-4 text-sm text-slate-700 leading-relaxed">{route.recommendation}</p>}
      <p className="text-sm text-slate-700 mt-4">Routes use the selected hour’s modeled road conditions. Change the scenario and run again to recalculate.</p>
    </section>
  </div>;
}
