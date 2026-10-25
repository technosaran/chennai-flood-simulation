'use client';

import React, { useEffect } from 'react';
import {
  MapContainer as LeafletMap,
  Circle,
  Polygon,
  Polyline,
  Marker,
  Popup,
  Tooltip,
  useMapEvents,
  useMap,
  CircleMarker,
} from 'react-leaflet';
import L from 'leaflet';
import OfflineBasemap from './OfflineBasemap';
import { FleetVehicleMarkers, RescuePlaybackControls, useRescuePlayback } from './RescueFleetPlayback';
import { ChennaiMapProps } from './MapContainer';
import {
  Coordinates,
  RouteInspectionData,
  StagingBaseEntity,
} from '@/lib/types';
import { CHENNAI_STAGING_BASES } from '@/lib/constants';

// Helper to create Leaflet DivIcons
function createDivIcon(
  html: string,
  className: string = 'custom-leaflet-icon',
  iconSize: [number, number] = [36, 36],
  iconAnchor: [number, number] = [18, 18],
) {
  return L.divIcon({
    html,
    className,
    iconSize,
    iconAnchor,
    popupAnchor: [0, -18],
  });
}

// 1. Custom SVG Animated Marker for Flood Epicenter with Concentric Shockwave Ripples
function createEpicenterIcon(depthM: number, label: string) {
  const html = `
    <div class="relative flex items-center justify-center cursor-pointer group" style="width: 52px; height: 52px;">
      <!-- Outer shockwave ripples -->
      <div class="absolute inset-0 rounded-full border-2 border-red-200/70 animate-shockwave"></div>
      <div class="absolute inset-2 rounded-full border border-amber-400/80 animate-[shockwaveRipple_2.2s_cubic-bezier(0,0.2,0.8,1)_infinite_0.6s]"></div>
      
      <!-- Center pulsing epicenter badge -->
      <div class="relative z-10 w-9 h-9 rounded-xl bg-gradient-to-br from-red-600 via-red-700 to-slate-950 border-2 border-red-400 shadow-glow-red flex flex-col items-center justify-center text-slate-900 transform group-hover:scale-110 transition-transform">
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
          <circle cx="12" cy="12" r="10"/>
          <line x1="12" y1="8" x2="12" y2="12"/>
          <line x1="12" y1="16" x2="12.01" y2="16"/>
        </svg>
      </div>

      <!-- Water depth telemetry tag -->
      <div class="absolute -bottom-2 z-20 px-1.5 py-0.2 bg-slate-50/90 text-red-700 font-mono text-[9px] font-black rounded border border-red-200 shadow-md whitespace-nowrap">
        FLOOD ZONE
      </div>
    </div>
  `;
  return createDivIcon(html, 'epicenter-icon', [52, 52], [26, 26]);
}

// 2. Custom SVG Animated Marker for IAF Chetak / Coast Guard Rescue Helicopter
function createHelicopterIcon(callsign: string, isAirborne: boolean = true) {
  const html = `
    <div class="relative flex items-center justify-center cursor-pointer group" style="width: 50px; height: 50px;">
      <!-- Radar scan ring for helicopter -->
      <div class="absolute inset-0 rounded-full border border-purple-400/50 animate-ping opacity-40"></div>
      <div class="absolute inset-2 rounded-full border border-purple-500/30"></div>

      <!-- Helicopter Body Box -->
      <div class="relative z-10 w-9 h-9 rounded-xl bg-gradient-to-br from-purple-700 via-indigo-900 to-slate-950 border-2 border-purple-300 shadow-glow-purple flex items-center justify-center text-slate-900 transform group-hover:scale-110 transition-transform">
        <!-- Spinning rotor blade SVG overlay -->
        <svg class="absolute -top-2 left-1/2 -translate-x-1/2 w-8 h-8 text-purple-200 animate-spin-rotor" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="2" y1="12" x2="22" y2="12" stroke-linecap="round"/>
          <circle cx="12" cy="12" r="2" fill="currentColor"/>
        </svg>

        <!-- Helicopter Cabin Icon -->
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="mt-1">
          <path d="M12 6v6"/>
          <path d="M5 12h14"/>
          <path d="M7 16h10"/>
          <path d="M4 18h16"/>
          <path d="M18 10l3-3"/>
        </svg>
      </div>

      <!-- Callsign Badge -->
      <div class="absolute -bottom-2 z-20 px-1 py-0.2 bg-slate-50/90 text-purple-300 font-mono text-[8px] font-bold rounded border border-purple-500/60 shadow-md whitespace-nowrap">
        ${callsign}
      </div>
    </div>
  `;
  return createDivIcon(html, 'helicopter-icon', [50, 50], [25, 25]);
}

// 3. Custom SVG Animated Marker for Amphibious Staging Base / Marine Rescue Base
function createAmphibiousIcon(callsign: string) {
  const html = `
    <div class="relative flex items-center justify-center cursor-pointer group" style="width: 48px; height: 48px;">
      <!-- Glowing cyan wave pulses -->
      <div class="absolute inset-1 rounded-full border border-cyan-400/60 animate-ping opacity-50"></div>
      <div class="absolute inset-3 rounded-full border border-cyan-200/40"></div>

      <!-- Vessel / Marine Badge -->
      <div class="relative z-10 w-8 h-8 rounded-xl bg-gradient-to-br from-cyan-600 via-teal-800 to-slate-950 border-2 border-cyan-300  flex items-center justify-center text-slate-900 transform group-hover:scale-110 transition-transform">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="5" r="3"/>
          <line x1="12" y1="22" x2="12" y2="8"/>
          <path d="M5 12H2a10 10 0 0 0 20 0h-3"/>
        </svg>
      </div>

      <!-- Marine Base Callout -->
      <div class="absolute -bottom-2 z-20 px-1 py-0.2 bg-slate-50/90 text-cyan-700 font-mono text-[8px] font-bold rounded border border-cyan-200/60 shadow-md whitespace-nowrap">
        ${callsign}
      </div>
    </div>
  `;
  return createDivIcon(html, 'amphibious-icon', [48, 48], [24, 24]);
}

// Map Click Interceptor Component
function MapClickHandler({
  onMapClick,
  activeDrawingMode,
}: {
  onMapClick: (coords: Coordinates) => void;
  activeDrawingMode: 'none' | 'circle' | 'polygon';
}) {
  useMapEvents({
    click(e) {
      if (activeDrawingMode !== 'none') {
        onMapClick([e.latlng.lat, e.latlng.lng]);
      }
    },
  });
  return null;
}

function MapViewport({ zones, step }: { zones: ChennaiMapProps['definedZones']; step?: ChennaiMapProps['currentStep'] }) {
  const map = useMap();
  useEffect(() => {
    const observer = new ResizeObserver(() => map.invalidateSize());
    observer.observe(map.getContainer());
    return () => observer.disconnect();
  }, [map]);
  useEffect(() => {
    const routes = [...(step?.evacuation_routes.features ?? []), ...(step?.supply_routes.features ?? [])];
    const pointsOnRoutes = routes.flatMap(route => route.geometry.coordinates);
    for (const trip of step?.rescue_fleet_plan?.trips ?? []) pointsOnRoutes.push(...(trip.geometry?.coordinates ?? []));
    if (pointsOnRoutes.length > 1) {
      map.fitBounds(pointsOnRoutes.map(point => [point[1], point[0]] as Coordinates), { padding: [32, 32], maxZoom: 13, animate: false });
      return;
    }
    if (!zones.length || !zones[0].coordinates.length) return;
    const zone = zones[0];
    const points = zone.coordinates;
    const lat = points.reduce((sum, p) => sum + p[0], 0) / points.length;
    const lon = points.reduce((sum, p) => sum + p[1], 0) / points.length;
    map.setView([lat, lon], 12, { animate: false });
  }, [map, zones, step]);
  return null;
}

export default function ChennaiMap({
  center,
  bounds,
  shelters,
  warehouses,
  distributionPoints,
  populationClusters,
  stagingBases = CHENNAI_STAGING_BASES,
  currentStep,
  showRescuePlayback = true,
  definedZones,
  activeDrawingMode,
  circleRadiusMeters,
  draftPolygonPoints,
  draftCircleCenter,
  onMapClick,
  visibleLayers,
  onSelectShelter,
  onSelectDistributionPoint,
  onSelectRoute,
}: ChennaiMapProps) {
  const fleetPlayback = useRescuePlayback(currentStep?.rescue_fleet_plan);
  // Convert GeoJSON polygon coordinates ([lon, lat]) to Leaflet [lat, lon]
  const convertGeoJsonPolygon = (coords: number[][][]): [number, number][] => {
    if (!coords || coords.length === 0 || !coords[0]) return [];
    return coords[0].map((pt) => [pt[1], pt[0]]);
  };

  // Convert GeoJSON LineString coordinates ([lon, lat]) to Leaflet [lat, lon]
  const convertGeoJsonLineString = (coords: number[][]): [number, number][] => {
    if (!coords) return [];
    return coords.map((pt) => [pt[1], pt[0]]);
  };

  // Flight arc interpolation for aerial helicopter tracks
  const generateAerialFlightArc = (
    p1: [number, number],
    p2: [number, number],
    numPoints = 28
  ): [number, number][] => {
    const [lat1, lon1] = p1;
    const [lat2, lon2] = p2;
    const midLat = (lat1 + lat2) / 2;
    const midLon = (lon1 + lon2) / 2;
    const dLat = lat2 - lat1;
    const dLon = lon2 - lon1;
    const dist = Math.sqrt(dLat * dLat + dLon * dLon);
    const curveFactor = 0.14 * dist;
    const perpLat = -dLon * (curveFactor / (dist || 1));
    const perpLon = dLat * (curveFactor / (dist || 1));
    const ctrlLat = midLat + perpLat;
    const ctrlLon = midLon + perpLon;

    const pts: [number, number][] = [];
    for (let i = 0; i <= numPoints; i++) {
      const t = i / numPoints;
      const lat = (1 - t) * (1 - t) * lat1 + 2 * (1 - t) * t * ctrlLat + t * t * lat2;
      const lon = (1 - t) * (1 - t) * lon1 + 2 * (1 - t) * t * ctrlLon + t * t * lon2;
      pts.push([lat, lon]);
    }
    return pts;
  };

  // Natural Catmull-Rom spline smoother for connector chords / sparse segments
  const smoothPathCoordinates = (
    pts: [number, number][],
    targetDensity = 4
  ): [number, number][] => {
    if (!pts || pts.length < 2) return pts || [];
    // High-resolution real OSM curves (> 10 points) already have surveyed street geometry
    if (pts.length > 10) return pts;

    if (pts.length === 2) {
      const [p0, p1] = pts;
      const midLat = (p0[0] + p1[0]) / 2;
      const midLon = (p0[1] + p1[1]) / 2;
      const dLat = p1[0] - p0[0];
      const dLon = p1[1] - p0[1];
      const dist = Math.sqrt(dLat * dLat + dLon * dLon);
      const bend = 0.06 * dist;
      const ctrlLat = midLat - dLon * (bend / (dist || 1));
      const ctrlLon = midLon + dLat * (bend / (dist || 1));

      const res: [number, number][] = [];
      for (let i = 0; i <= 14; i++) {
        const t = i / 14;
        const lat = (1 - t) * (1 - t) * p0[0] + 2 * (1 - t) * t * ctrlLat + t * t * p1[0];
        const lon = (1 - t) * (1 - t) * p0[1] + 2 * (1 - t) * t * ctrlLon + t * t * p1[1];
        res.push([lat, lon]);
      }
      return res;
    }

    const result: [number, number][] = [];
    for (let i = 0; i < pts.length - 1; i++) {
      const p0 = i === 0 ? pts[0] : pts[i - 1];
      const p1 = pts[i];
      const p2 = pts[i + 1];
      const p3 = i + 2 < pts.length ? pts[i + 2] : p2;

      for (let step = 0; step < targetDensity; step++) {
        const t = step / targetDensity;
        const t2 = t * t;
        const t3 = t2 * t;

        const lat =
          0.5 *
          (2 * p1[0] +
            (-p0[0] + p2[0]) * t +
            (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2 +
            (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3);

        const lon =
          0.5 *
          (2 * p1[1] +
            (-p0[1] + p2[1]) * t +
            (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2 +
            (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3);

        result.push([lat, lon]);
      }
    }
    result.push(pts[pts.length - 1]);
    return result;
  };

  const inspectRoute = (feature: any, category: 'evacuation' | 'supply') => {
    const p = feature.properties;
    onSelectRoute?.({
      network_source: p.network_source,
      network_timestamp: p.network_timestamp,
      access_connectors_m: p.access_connectors_m,
      access_note: p.access_note,
      geometry_kind: p.geometry_kind,
      route_id: p.route_id,
      route_name: p.route_id,
      route_category: category,
      transport_mode:
        p.transport_mode || (category === 'evacuation' ? 'foot' : 'truck'),
      vehicle_type: p.vehicle_type || 'Modeled transport',
      source_name: p.source_name || p.warehouse_name,
      destination_name: p.destination_name,
      distance_km: p.distance_km ?? 0,
      transit_time_min: p.estimated_time_min ?? p.transit_time_min ?? 0,
      convoy_vehicle_count: p.convoy_vehicles ?? 0,
      water_clearance_depth_m: p.wading_depth_clearance_m ?? 0,
      max_water_depth_m: 0,
      depth_profile: [],
      evacuee_or_capacity_count: p.evacuee_count ?? 0,
      manifest: {
        water_litres: p.cargo?.water_litres ?? 0,
        food_rations: p.cargo?.food_rations ?? 0,
        medical_kits: p.cargo?.medical_kits ?? 0,
      },
      status: p.status || 'clear',
      recommendation: 'Computed for the selected simulation hour.',
    });
  };
  const handleEvacRouteClick = (f: any) => inspectRoute(f, 'evacuation');
  const handleSupplyRouteClick = (f: any) => inspectRoute(f, 'supply');

  return (
    <div className="w-full h-full relative z-0 flex flex-col">
      <LeafletMap
        center={center}
        preferCanvas
        zoom={12}
        minZoom={10}
        maxZoom={18}
        maxBounds={[
          [12.75, 80.0],
          [13.35, 80.45],
        ]}
        style={{ width: '100%', height: '100%', flex: '1 1 0%', minHeight: 0, backgroundColor: '#020617' }}
      >
        <MapViewport zones={definedZones} step={showRescuePlayback ? currentStep : null} />
        <MapClickHandler
          onMapClick={onMapClick}
          activeDrawingMode={activeDrawingMode}
        />

        <OfflineBasemap places={populationClusters} />

        {/* 1. Population Density Heatmap Layer */}
        {visibleLayers.populationHeatmap &&
          populationClusters.map((cluster) => {
            const riskLevel = String(
              cluster.risk_level || 'moderate',
            ).toLowerCase();
            const color =
              riskLevel === 'extreme'
                ? '#EF4444'
                : riskLevel === 'high'
                  ? '#F97316'
                  : '#EAB308';
            const estPop = cluster.estimated_population ?? 0;
            const density = cluster.density_per_sq_km ?? 0;
            const radius = Math.min(1600, Math.max(700, estPop / 35));

            return (
              <Circle
                key={`pop-${cluster.id}`}
                center={cluster.location}
                radius={radius}
                pathOptions={{
                  color,
                  fillColor: color,
                  fillOpacity: 0.16,
                  weight: 1.5,
                  dashArray: '3, 6',
                }}
              >
                <Popup className="dark-popup">
                  <div className="p-2.5 text-sm font-sans text-slate-900">
                    <div className="font-bold text-sm text-slate-900 flex items-center gap-1.5">
                      <span
                        className="w-2.5 h-2.5 rounded-full inline-block"
                        style={{ backgroundColor: color }}
                      />
                      {cluster.name}
                    </div>
                    <div className="mt-1 text-slate-700 font-mono text-sm">
                      Ward Population Risk Cluster
                    </div>
                    <div className="mt-2 grid grid-cols-2 gap-1.5 pt-1.5 border-t border-slate-200">
                      <div>
                        <span className="text-sm text-slate-700 uppercase block">
                          Population
                        </span>
                        <span className="font-mono font-semibold text-slate-900">
                          {estPop.toLocaleString()}
                        </span>
                      </div>
                      <div>
                        <span className="text-sm text-slate-700 uppercase block">
                          Density
                        </span>
                        <span className="font-mono font-semibold text-slate-900">
                          {density.toLocaleString()} /km²
                        </span>
                      </div>
                    </div>
                    <div className="mt-2">
                      <span
                        className={`text-sm px-2 py-0.5 rounded font-mono font-bold uppercase tracking-wider ${
                          riskLevel === 'extreme'
                            ? 'bg-red-50 text-red-700 border border-red-200'
                            : riskLevel === 'high'
                              ? 'bg-orange-950 text-orange-300 border border-orange-700'
                              : 'bg-yellow-950 text-yellow-300 border border-yellow-700'
                        }`}
                      >
                        {riskLevel} Threat Zone
                      </span>
                    </div>
                  </div>
                </Popup>
              </Circle>
            );
          })}

        {/* 2. Defined Scenario Flood Zones & Interactive Drawing */}
        {definedZones.map((zone) =>
          zone.type === 'circle' ? (
            <React.Fragment key={`selected-${zone.id}`}>
              <Circle
                center={zone.coordinates[0]}
                radius={zone.radius_meters || 2000}
                pathOptions={{
                  color: '#22d3ee',
                  fillColor: '#06b6d4',
                  fillOpacity: 0.08,
                  dashArray: '6 6',
                  weight: 2,
                }}
              />
              {/* Animated Epicenter Pulse Marker */}
              <Marker
                position={zone.coordinates[0]}
                icon={createEpicenterIcon(2.2, zone.name || 'Epicenter')}
              >
                <Popup>
                  <div className="p-2 text-sm font-sans text-slate-900">
                    <span className="font-mono text-sm text-red-700 font-bold block uppercase">
                      Flood Epicenter
                    </span>
                    <div className="font-bold text-sm text-slate-900 mt-0.5">
                      {zone.name}
                    </div>
                    <div className="mt-1 text-sm text-slate-700">
                      Radius:{' '}
                      <b>
                        {((zone.radius_meters || 2000) / 1000).toFixed(1)} km
                      </b>
                    </div>
                  </div>
                </Popup>
              </Marker>
            </React.Fragment>
          ) : (
            <React.Fragment key={`selected-${zone.id}`}>
              <Polygon
                positions={zone.coordinates}
                pathOptions={{
                  color: '#22d3ee',
                  fillColor: '#06b6d4',
                  fillOpacity: 0.08,
                  dashArray: '6 6',
                  weight: 2,
                }}
              />
              {zone.coordinates.length > 0 && (
                <Marker
                  position={zone.coordinates[0]}
                  icon={createEpicenterIcon(2.4, zone.name || 'Surge Basin')}
                >
                  <Popup>
                    <div className="p-2 text-sm font-sans text-slate-900">
                      <span className="font-mono text-sm text-red-700 font-bold block uppercase">
                        Hydrological Basin Center
                      </span>
                      <div className="font-bold text-sm text-slate-900 mt-0.5">
                        {zone.name}
                      </div>
                    </div>
                  </Popup>
                </Marker>
              )}
            </React.Fragment>
          ),
        )}

        {/* Interactive Drawing Layers */}
        {activeDrawingMode === 'circle' && draftCircleCenter && (
          <Circle
            center={draftCircleCenter}
            radius={circleRadiusMeters}
            pathOptions={{
              color: '#06B6D4',
              fillColor: '#06B6D4',
              fillOpacity: 0.35,
              weight: 2,
              dashArray: '4, 6',
            }}
          />
        )}

        {activeDrawingMode === 'polygon' && draftPolygonPoints.length > 0 && (
          <>
            <Polygon
              positions={draftPolygonPoints}
              pathOptions={{
                color: '#3B82F6',
                fillColor: '#3B82F6',
                fillOpacity: 0.3,
                weight: 2,
                dashArray: '4, 4',
              }}
            />
            {draftPolygonPoints.map((pt, i) => (
              <CircleMarker
                key={`draft-pt-${i}`}
                center={pt}
                radius={5}
                pathOptions={{
                  color: '#2563EB',
                  fillColor: '#60A5FA',
                  fillOpacity: 1,
                  weight: 2,
                }}
              />
            ))}
          </>
        )}

        {/* 3. Active Simulation Flood Inundation Polygons Layer */}
        {visibleLayers.flood &&
          currentStep?.flood_polygons?.features.map((feature, idx) => {
            const positions = convertGeoJsonPolygon(
              feature.geometry.coordinates,
            );
            const props = feature.properties;

            return (
              <Polygon
                key={`flood-${props.zone_id}-${idx}`}
                positions={positions}
                pathOptions={{
                  color: props.stroke_color,
                  fillColor: props.fill_color,
                  fillOpacity: props.fill_opacity,
                  weight: 2.5,
                }}
              >
                <Popup>
                  <div className="p-2.5 text-sm font-sans text-slate-900 min-w-[200px]">
                    <div className="flex items-center gap-2">
                      <span
                        className="w-3 h-3 rounded-full"
                        style={{ backgroundColor: props.fill_color }}
                      />
                      <span className="font-bold text-sm text-slate-900">
                        Inundation Zone: {props.zone_id}
                      </span>
                    </div>
                    <div className="mt-2.5 grid grid-cols-2 gap-2 text-sm">
                      <div className="bg-slate-50/80 p-2 rounded-lg border border-slate-200">
                        <span className="text-sm text-slate-700 block uppercase font-mono">
                          Water Depth
                        </span>
                        <span className="font-bold font-mono text-cyan-700 text-sm">
                          {props.water_depth_m} m
                        </span>
                      </div>
                      <div className="bg-slate-50/80 p-2 rounded-lg border border-slate-200">
                        <span className="text-sm text-slate-700 block uppercase font-mono">
                          Severity Tier
                        </span>
                        <span className="font-bold uppercase text-red-700 text-sm">
                          {props.severity}
                        </span>
                      </div>
                    </div>
                    {props.area_sq_km && (
                      <div className="mt-2 text-sm text-slate-700 font-mono">
                        Surface Spread:{' '}
                        <b className="text-slate-900">{props.area_sq_km} km²</b>
                      </div>
                    )}
                  </div>
                </Popup>
              </Polygon>
            );
          })}

        {/* 4. Evacuation Routes Overlay with Multi-modal Visuals & Click Handler */}
        {visibleLayers.evacuation &&
          currentStep?.evacuation_routes?.features.map((feature, idx) => {
            const rawPositions = convertGeoJsonLineString(
              feature.geometry.coordinates,
            );
            const positions = smoothPathCoordinates(rawPositions);
            const props = feature.properties;
            const isRerouted = props.status === 'rerouted';
            const isImpassable = props.status === 'impassable';

            const routeColor = isImpassable
              ? '#EF4444'
              : isRerouted
                ? '#F59E0B'
                : '#10B981';
            const baseWeight = isRerouted ? 4.5 : isImpassable ? 3.5 : 5;

            return (
              <React.Fragment key={`evac-route-group-${props.route_id}-${idx}`}>
                {/* Visual underlay / glow casing for route definition */}
                <Polyline
                  positions={positions}
                  pathOptions={{
                    color: '#020617',
                    weight: baseWeight + 3,
                    opacity: 0.7,
                    lineCap: 'round',
                    lineJoin: 'round',
                  }}
                />
                <Polyline
                  key={`evac-route-${props.route_id}-${idx}`}
                  positions={positions}
                  eventHandlers={{
                    click: () => handleEvacRouteClick(feature),
                  }}
                  pathOptions={{
                    color: routeColor,
                    weight: baseWeight,
                    opacity: 0.95,
                    dashArray: isRerouted
                      ? '8, 6'
                      : isImpassable
                        ? '3, 6'
                        : undefined,
                    lineCap: 'round',
                    lineJoin: 'round',
                  }}
                >
                <Tooltip sticky>
                  <div className="text-sm font-sans p-1.5 min-w-[210px]">
                    <div className="font-bold flex items-center justify-between gap-2 text-emerald-700">
                      <span>🚶 Evacuation Corridor</span>
                      <span
                        className={`text-[9px] px-1.5 py-0.2 rounded font-mono font-bold uppercase ${
                          isRerouted
                            ? 'bg-amber-50 text-amber-800 border border-amber-200'
                            : isImpassable
                              ? 'bg-red-50 text-red-700 border border-red-200'
                              : 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                        }`}
                      >
                        {props.status}
                      </span>
                    </div>
                    <div className="text-slate-900 mt-1 font-semibold text-sm">
                      {props.source_name} ➔ {props.destination_name}
                    </div>
                    <div className="text-sm text-slate-700 mt-1 font-mono">
                      Evacuees:{' '}
                      <b>{(props.evacuee_count ?? 0).toLocaleString()}</b> •
                      Dist: <b>{props.distance_km ?? 0} km</b>
                    </div>
                    <div className="mt-1 text-[9px] text-cyan-700 font-mono underline">
                      Click route to view computed details ↗
                    </div>
                  </div>
                </Tooltip>
              </Polyline>
              </React.Fragment>
            );
          })}

        {/* 5. Supply Logistics Routes Overlay: Multi-Modal Styling & Click Handler */}
        {visibleLayers.supply &&
          currentStep?.supply_routes?.features.map((feature, idx) => {
            const rawPositions = convertGeoJsonLineString(
              feature.geometry.coordinates,
            );
            const props = feature.properties;
            const mode = props.transport_mode || 'truck';
            const isBlocked = props.status === 'blocked';

            const positions =
              mode === 'helicopter' && rawPositions.length === 2
                ? generateAerialFlightArc(rawPositions[0], rawPositions[1])
                : smoothPathCoordinates(rawPositions);

            // Differentiate visually between truck (amber), amphibious (cyan pulses), helicopter (purple dashed vectors)
            const strokeColor = isBlocked
              ? '#DC2626'
              : mode === 'helicopter'
                ? '#C084FC'
                : mode === 'amphibious'
                  ? '#00F0FF'
                  : '#F59E0B';

            const dashPattern =
              mode === 'helicopter'
                ? '8, 6'
                : mode === 'amphibious'
                  ? '6, 6'
                  : '5, 5';

            const baseWeight =
              mode === 'helicopter' ? 4 : mode === 'amphibious' ? 4.5 : 4.5;

            return (
              <React.Fragment key={`supply-route-group-${props.route_id}-${idx}`}>
                {/* Visual underlay casing */}
                <Polyline
                  positions={positions}
                  pathOptions={{
                    color: '#020617',
                    weight: baseWeight + 3,
                    opacity: 0.65,
                    lineCap: 'round',
                    lineJoin: 'round',
                  }}
                />
                <Polyline
                  key={`supply-route-${props.route_id}-${idx}`}
                  positions={positions}
                  eventHandlers={{
                    click: () => handleSupplyRouteClick(feature),
                  }}
                  pathOptions={{
                    color: strokeColor,
                    weight: baseWeight,
                    opacity: 0.92,
                    dashArray: dashPattern,
                    lineCap: 'round',
                    lineJoin: 'round',
                  }}
                >
                <Tooltip sticky>
                  <div className="text-sm font-sans p-1.5 min-w-[220px]">
                    <div className="font-bold flex items-center justify-between gap-2">
                      <span
                        className={
                          mode === 'helicopter'
                            ? 'text-purple-400'
                            : mode === 'amphibious'
                              ? 'text-cyan-700'
                              : 'text-amber-800'
                        }
                      >
                        {mode === 'helicopter'
                          ? '🚁 Aerial SAR Sortie'
                          : mode === 'amphibious'
                            ? '🚤 Amphibious Water Track'
                            : '🚛 Heavy 6x6 Logistics Convoy'}
                      </span>
                      <span className="text-[9px] px-1.5 py-0.2 rounded font-mono font-bold uppercase bg-slate-50 text-slate-900 border border-slate-200">
                        {props.status}
                      </span>
                    </div>
                    <div className="text-slate-900 mt-1 font-semibold text-sm">
                      {props.warehouse_name} ➔ {props.destination_name}
                    </div>
                    <div className="text-sm text-slate-700 mt-1 font-mono">
                      Dist: <b>{props.distance_km ?? 0} km</b> • Transit:{' '}
                      <b>{props.transit_time_min ?? 0}m</b>
                    </div>
                    {props.cargo && (
                      <div className="text-sm text-slate-700 mt-1.5 bg-slate-50/80 p-1.5 rounded border border-slate-200 font-mono">
                        📦 Water:{' '}
                        {(props.cargo.water_litres ?? 0).toLocaleString()}L |
                        Food: {(props.cargo.food_rations ?? 0).toLocaleString()}
                      </div>
                    )}
                    <div className="mt-1 text-[9px] text-cyan-700 font-mono underline">
                      Click route to view computed details ↗
                    </div>
                  </div>
                </Tooltip>
              </Polyline>
              </React.Fragment>
            );
          })}

        {visibleLayers.evacuation && currentStep?.rescue_fleet_plan?.trips.map((trip, index) => {
          if (!trip.geometry) return null;
          const rawPositions = convertGeoJsonLineString(trip.geometry.coordinates);
          const positions = trip.mode === 'helicopters' && rawPositions.length === 2
            ? generateAerialFlightArc(rawPositions[0], rawPositions[1])
            : smoothPathCoordinates(rawPositions);
          return (
            <React.Fragment key={`fleet-group-${trip.vehicle_id}-${index}`}>
              <Polyline
                positions={positions}
                pathOptions={{
                  color: '#020617',
                  weight: 8,
                  opacity: 0.6,
                  lineCap: 'round',
                  lineJoin: 'round',
                }}
              />
              <Polyline
                key={`fleet-${trip.vehicle_id}-${index}`}
                positions={positions}
                pathOptions={{
                  color: trip.mode === 'helicopters' ? '#9333ea' : trip.mode === 'boats' ? '#0891b2' : '#2563eb',
                  weight: 5,
                  opacity: .95,
                  dashArray: trip.mode === 'trucks' ? undefined : '8, 6',
                  lineCap: 'round',
                  lineJoin: 'round',
                }}
              >
                <Tooltip sticky>{trip.vehicle_id}: {trip.cluster_id} → {trip.destination_name} · {trip.people} people</Tooltip>
                <Popup><div className="space-y-2"><strong>{trip.vehicle_id} · Rescue transfer</strong><p>{trip.cluster_id} → {trip.destination_name}</p><p>{trip.people} people · {trip.distance_km.toFixed(1)} km round trip</p><p>Depart {trip.depart_minutes.toFixed(1)}m · Drop-off {trip.dropoff_minutes.toFixed(1)}m · Return {trip.return_available_minutes.toFixed(1)}m</p><p>{trip.feasibility}</p></div></Popup>
              </Polyline>
            </React.Fragment>
          );
        })}

        {visibleLayers.evacuation && <FleetVehicleMarkers plan={currentStep?.rescue_fleet_plan} minute={fleetPlayback.minute} />}
        {visibleLayers.evacuation && currentStep?.rescue_fleet_plan?.transfer_points?.map(point => <CircleMarker key={point.id} center={point.location} radius={7} pathOptions={{ color: '#0e7490', fillColor: '#fef08a', fillOpacity: 1 }}><Tooltip>{point.name} · boat → truck</Tooltip><Popup><strong>{point.name}</strong><p>Modeled depth: {point.depth_m.toFixed(2)} m</p><p>{point.access}</p></Popup></CircleMarker>)}
        {/* 6. Staging Bases (Rescue Helicopters & Amphibious Craft Bases) */}
        {stagingBases.map((base) => {
          const isHelicopter = base.type === 'helicopter_base';
          const icon = isHelicopter
            ? createHelicopterIcon(base.callsign, true)
            : createAmphibiousIcon(base.callsign);

          return (
            <Marker
              key={`staging-${base.id}`}
              position={base.location}
              icon={icon}
            >
              <Popup>
                <div className="p-2.5 text-sm font-sans text-slate-900 min-w-[240px]">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-sm text-slate-900">
                      {base.name}
                    </span>
                    <span className="text-[9px] font-mono font-bold bg-slate-50 px-1.5 py-0.5 rounded text-cyan-700 border border-cyan-200">
                      {base.callsign}
                    </span>
                  </div>
                  <div className="text-sm text-slate-700 mt-0.5 font-mono">
                    {isHelicopter
                      ? 'IAF / Coast Guard Air Base'
                      : 'Marine Amphibious Staging Base'}
                  </div>

                  <div className="mt-2.5 bg-slate-50/80 p-2 rounded-lg border border-slate-200 space-y-1 font-mono text-sm">
                    <div className="flex justify-between">
                      <span className="text-slate-700">Deployed Assets:</span>
                      <span className="text-slate-900 font-semibold">
                        {base.stationed_assets}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-700">Combat Radius:</span>
                      <span className="text-cyan-700 font-semibold">
                        {base.operational_radius_km} km
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-700">Readiness:</span>
                      <span className="text-emerald-700 font-bold uppercase">
                        {base.readiness_status}
                      </span>
                    </div>
                  </div>
                </div>
              </Popup>
            </Marker>
          );
        })}

        {/* 7. Warehouses (5 Major Depots) */}
        {visibleLayers.warehouses &&
          warehouses.map((wh) => {
            const iconHtml = `
              <div class="relative group cursor-pointer">
                <div class="w-8 h-8 rounded-lg bg-blue-600 border-2 border-white shadow-lg flex items-center justify-center text-slate-900 transform hover:scale-110 transition-transform">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M22 8.35V20a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V8.35A2 2 0 0 1 3.26 6.5l8-3.2a2 2 0 0 1 1.48 0l8 3.2A2 2 0 0 1 22 8.35Z"/>
                    <path d="M6 18h12"/>
                    <path d="M6 14h12"/>
                  </svg>
                </div>
                <div class="absolute -bottom-1 -right-1 w-3.5 h-3.5 rounded-full bg-cyan-400 border-2 border-white"></div>
              </div>
            `;
            const icon = createDivIcon(
              iconHtml,
              'warehouse-icon',
              [32, 32],
              [16, 16],
            );

            return (
              <Marker key={`wh-${wh.id}`} position={wh.location} icon={icon}>
                <Popup>
                  <div className="p-2.5 text-sm font-sans text-slate-900 min-w-[220px]">
                    <div className="flex items-center gap-1.5 font-bold text-sm text-slate-900">
                      <span>🏛️ {wh.name}</span>
                    </div>
                    <div className="text-sm text-slate-700 mt-0.5">
                      {wh.address}
                    </div>
                    <div className="mt-2 bg-slate-50/80 p-2 rounded-lg border border-slate-200">
                      <div className="text-sm font-bold text-blue-700 uppercase tracking-wider mb-1 font-mono">
                        Depot Stock Reserves
                      </div>
                      <div className="space-y-1 text-sm font-mono">
                        <div className="flex justify-between">
                          <span className="text-slate-700">
                            💧 Potable Water:
                          </span>
                          <span className="font-bold text-slate-900">
                            {(wh.supplies?.water_litres ?? 0).toLocaleString()}{' '}
                            L
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-slate-700">
                            🍞 Food Rations:
                          </span>
                          <span className="font-bold text-slate-900">
                            {(wh.supplies?.food_rations ?? 0).toLocaleString()}{' '}
                            pk
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-slate-700">
                            🩹 Medical Kits:
                          </span>
                          <span className="font-bold text-slate-900">
                            {(wh.supplies?.medical_kits ?? 0).toLocaleString()}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                </Popup>
              </Marker>
            );
          })}

        {/* 8. Shelters (12 Safe Shelters) */}
        {visibleLayers.shelters &&
          shelters.map((shelter) => {
            const simAlloc = currentStep?.shelter_allocations?.find(
              (sa) => sa.shelter_id === shelter.id,
            );
            const assignedEvacuees = simAlloc?.allocated_evacuees || 0;
            const totalAssigned =
              (shelter.current_occupancy ?? 0) + assignedEvacuees;
            const shelterCap = Math.max(1, shelter.capacity ?? 1);
            const occupancyPct = Math.min(
              100,
              Math.round((totalAssigned / shelterCap) * 100),
            );
            const isFull = occupancyPct >= 100;
            const isNearFull = occupancyPct >= 80;

            const iconHtml = `
              <div class="relative group cursor-pointer">
                <div class="w-8 h-8 rounded-lg ${
                  isFull
                    ? 'bg-red-600'
                    : isNearFull
                      ? 'bg-amber-600'
                      : 'bg-emerald-600'
                } border-2 border-white shadow-lg flex items-center justify-center text-slate-900 transform hover:scale-110 transition-transform">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>
                    <polyline points="9 22 9 12 15 12 15 22"/>
                  </svg>
                </div>
                <div class="absolute -top-1.5 -right-1.5 px-1 py-0.2 bg-slate-50 text-slate-900 rounded text-[9px] font-mono font-bold border border-white">
                  ${occupancyPct}%
                </div>
              </div>
            `;
            const icon = createDivIcon(
              iconHtml,
              'shelter-icon',
              [32, 32],
              [16, 16],
            );

            return (
              <Marker
                key={`shelter-${shelter.id}`}
                position={shelter.location}
                icon={icon}
                eventHandlers={{
                  click: () => onSelectShelter?.(shelter.id),
                }}
              >
                <Popup>
                  <div className="p-2.5 text-sm font-sans text-slate-900 min-w-[240px]">
                    <div className="flex items-start justify-between gap-1">
                      <div>
                        <div className="font-bold text-sm text-slate-900 leading-tight">
                          {shelter.name}
                        </div>
                        <div className="text-sm text-slate-700 font-medium">
                          {shelter.neighborhood}
                        </div>
                      </div>
                      <span className="text-sm font-mono font-bold bg-slate-50 px-1.5 py-0.5 rounded text-slate-900 border border-slate-200">
                        {shelter.id}
                      </span>
                    </div>

                    {/* Capacity Progress Bar */}
                    <div className="mt-2.5 bg-slate-50/80 p-2 rounded-lg border border-slate-200">
                      <div className="flex justify-between items-center text-sm mb-1 font-mono">
                        <span className="text-slate-700 font-medium">
                          Occupancy
                        </span>
                        <span className="font-bold text-slate-900">
                          {totalAssigned.toLocaleString()} /{' '}
                          {(shelter.capacity ?? 0).toLocaleString()}
                        </span>
                      </div>
                      <div className="w-full bg-slate-50 h-2 rounded-full overflow-hidden">
                        <div
                          className={`h-full transition-all duration-500 ${
                            occupancyPct >= 95
                              ? 'bg-red-500'
                              : occupancyPct >= 75
                                ? 'bg-amber-500'
                                : 'bg-emerald-500'
                          }`}
                          style={{ width: `${occupancyPct}%` }}
                        />
                      </div>
                      <div className="flex justify-between text-sm font-mono text-slate-700 mt-1">
                        <span>
                          Slots Available:{' '}
                          <span className="text-slate-900">
                            {Math.max(
                              0,
                              (shelter.capacity ?? 0) - totalAssigned,
                            ).toLocaleString()}
                          </span>
                        </span>
                        <span className="font-bold text-slate-900">
                          {occupancyPct}% Full
                        </span>
                      </div>
                    </div>

                    {/* Amenities */}
                    {shelter.amenities && (
                      <div className="mt-2 flex flex-wrap gap-1">
                        {shelter.amenities.map((amenity, i) => (
                          <span
                            key={i}
                            className="text-[9px] bg-slate-50 text-slate-700 px-1.5 py-0.5 rounded border border-slate-200"
                          >
                            ✓ {amenity}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                </Popup>
              </Marker>
            );
          })}

        {/* 9. Distribution Points (10 Relief Distribution Centers) */}
        {visibleLayers.distributionPoints &&
          distributionPoints.map((dp) => {
            const iconHtml = `
              <div class="relative cursor-pointer">
                <div class="w-8 h-8 rounded-lg bg-amber-600 border-2 border-white shadow-md flex items-center justify-center text-slate-900 transform hover:scale-110 transition-transform">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polygon points="1 6 1 22 8 18 16 22 23 18 23 2 16 6 8 2 1 6"/>
                    <line x1="8" y1="2" x2="8" y2="18"/>
                    <line x1="16" y1="6" x2="16" y2="22"/>
                  </svg>
                </div>
                <div class="absolute -top-1 -right-1 text-[9px] px-1 bg-amber-50 text-amber-800 rounded font-mono font-bold">
                  ${dp.id}
                </div>
              </div>
            `;
            const icon = createDivIcon(iconHtml, 'dp-icon', [32, 32], [16, 16]);

            return (
              <Marker
                key={`dp-${dp.id}`}
                position={dp.location}
                icon={icon}
                eventHandlers={{
                  click: () => onSelectDistributionPoint?.(dp.id),
                }}
              >
                <Popup>
                  <div className="p-2.5 text-sm font-sans text-slate-900 min-w-[220px]">
                    <div className="font-bold text-sm text-slate-900 flex items-center gap-1">
                      <span>🏕️ {dp.name}</span>
                    </div>
                    <div className="text-sm text-slate-700 font-mono">
                      {dp.target_ward}
                    </div>
                    <div className="mt-2 bg-slate-50/80 p-2 rounded-lg border border-slate-200 text-sm font-mono space-y-1">
                      <div className="text-sm font-bold text-amber-800 uppercase">
                        Relief Demand & Stock
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-700">💧 Water Needed:</span>
                        <span className="font-bold text-slate-900">
                          {(dp.demand?.water_litres ?? 0).toLocaleString()} L
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-700">🍞 Food Rations:</span>
                        <span className="font-bold text-slate-900">
                          {(dp.demand?.food_rations ?? 0).toLocaleString()} pk
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-700">🩹 Medical Kits:</span>
                        <span className="font-bold text-slate-900">
                          {dp.demand?.medical_kits ?? 0}
                        </span>
                      </div>
                    </div>
                  </div>
                </Popup>
              </Marker>
            );
          })}
      </LeafletMap>
      {showRescuePlayback && visibleLayers.evacuation && <RescuePlaybackControls plan={currentStep?.rescue_fleet_plan} playback={fleetPlayback} />}
    </div>
  );
}
