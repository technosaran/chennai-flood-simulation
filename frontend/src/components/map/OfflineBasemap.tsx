'use client';

import { useEffect, useState } from 'react';
import { GeoJSON, TileLayer, CircleMarker, Tooltip, Pane } from 'react-leaflet';
import type { FeatureCollection } from 'geojson';
import type { PopulationClusterEntity } from '@/lib/types';

type Layers = { wards: FeatureCollection; roads: FeatureCollection; rivers: FeatureCollection };

export default function OfflineBasemap({ places }: { places: PopulationClusterEntity[] }) {
  const [layers, setLayers] = useState<Layers | null>(null);
  const [online, setOnline] = useState(false);
  const [error, setError] = useState('');
  useEffect(() => {
    const controller = new AbortController();
    Promise.all(['gcc_wards', 'offline_roads', 'offline_rivers'].map(async name => {
      const response = await fetch(`/data/${name}.json`, { signal: controller.signal });
      if (!response.ok) throw new Error('Reference layers could not be loaded');
      return response.json() as Promise<FeatureCollection>;
    })).then(([wards, roads, rivers]) => setLayers({ wards, roads, rivers }))
      .catch(() => { if (!controller.signal.aborted) setError('Offline reference layers unavailable. Refresh the page to retry.'); });
    return () => controller.abort();
  }, []);
  return <>
    {online && <TileLayer url="https://tile.openstreetmap.org/{z}/{x}/{y}.png" attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors' eventHandlers={{ tileerror: () => { setOnline(false); setError('Online tiles unavailable. Using bundled offline vectors.'); } }} />}
    {layers && <Pane name="offline-reference" style={{ zIndex: 250 }}>
      <GeoJSON data={layers.wards} interactive={false} style={{ color: '#64748b', weight: .7, fillColor: '#e8f0eb', fillOpacity: online ? .08 : .55 }} attribution='Ward boundaries: Greater Chennai Corporation' />
      <GeoJSON data={layers.roads} interactive={false} style={feature => ({ color: ['primary','trunk','motorway'].includes(feature?.properties?.highway) ? '#e2bc75' : '#94a3b8', weight: ['primary','trunk','motorway'].includes(feature?.properties?.highway) ? 2 : 1, opacity: online ? .2 : .7 })} attribution='Streets: &copy; OpenStreetMap contributors (ODbL)' />
      <GeoJSON data={layers.rivers} interactive={false} style={{ color: '#38bdf8', weight: 3, opacity: .85 }} attribution='Rivers: &copy; OpenStreetMap contributors (ODbL)' />
      {!online && places.map(place => <CircleMarker key={place.id} center={place.location} radius={2} pathOptions={{ color: '#475569', fillOpacity: 1 }} interactive={false}><Tooltip permanent direction="top" className="offline-place-label">{place.name.split(' / ')[0]}</Tooltip></CircleMarker>)}
    </Pane>}
    <div className="leaflet-bottom leaflet-left" style={{ pointerEvents: 'auto' }}><div className="leaflet-control rounded-lg border border-slate-200 bg-slate-50/95 p-2 text-sm text-slate-900 max-w-[180px]">
      <button type="button" onClick={() => { setOnline(v => !v); setError(''); }} className="underline text-cyan-700" aria-pressed={online}>{online ? 'Use offline map' : 'Load online street tiles'}</button>
      <p className="mt-1 hidden sm:block text-[11px]">{online ? 'Online streets + local reference vectors' : 'Offline: GCC wards · OSM main streets · OSM rivers'}</p>
      {!layers && !error && <p>Loading local reference…</p>}{error && <p role="status" className="text-amber-800 mt-1">{error}</p>}
    </div></div>
  </>;
}
