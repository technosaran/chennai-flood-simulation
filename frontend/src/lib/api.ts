import { rainfallMmPerHour } from './rainfall';
import {
  DisasterParameters,
  MapInitResponse,
  SimulationRequest,
  SimulationResponse,
  ResourceAllocateRequest,
  ResourceAllocateResponse,
} from './types';
import {
  CHENNAI_CENTER,
  CHENNAI_BOUNDS,
  CHENNAI_SHELTERS,
  CHENNAI_WAREHOUSES,
  CHENNAI_DISTRIBUTION_POINTS,
  CHENNAI_POPULATION_CLUSTERS,
  HISTORICAL_PRESETS,
} from './constants';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || '';

export async function checkHealth(): Promise<{
  status: string;
  version: string;
  isLive: boolean;
}> {
  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), 5000);
  try {
    const res = await fetch(`${API_BASE_URL}/api/health`, {
      signal: controller.signal,
    });
    clearTimeout(id);
    if (res.ok) {
      const data = await res.json();
      return {
        status: data.status || 'ok',
        version: data.version || '1.0.0',
        isLive: true,
      };
    }
  } catch {
    // Backend offline
  } finally {
    clearTimeout(id);
  }
  return { status: 'standby', version: '1.0.0-client', isLive: false };
}

export async function getMapInit(): Promise<MapInitResponse> {
  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), 2500);
  try {
    const res = await fetch(`${API_BASE_URL}/api/map/init`, {
      signal: controller.signal,
    });
    clearTimeout(id);
    if (res.ok) {
      return await res.json();
    }
  } catch {
    // Keep baseline map data available while the backend is offline.
  } finally {
    clearTimeout(id);
  }

  return {
    center: CHENNAI_CENTER,
    bounds: CHENNAI_BOUNDS,
    shelters: CHENNAI_SHELTERS,
    warehouses: CHENNAI_WAREHOUSES,
    distribution_points: CHENNAI_DISTRIBUTION_POINTS,
    population_clusters: CHENNAI_POPULATION_CLUSTERS,
    presets: HISTORICAL_PRESETS,
  };
}

async function post<T>(
  path: string,
  request: unknown,
  timeoutMs: number,
): Promise<T> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
      signal: controller.signal,
    });
    const data = await response.json().catch(() => ({
      detail: `The simulation engine returned an error (${response.status}). Please try again.`,
    }));
    if (!response.ok) {
      throw new Error(
        typeof data.detail === 'string'
          ? data.detail
          : `Request failed (${response.status}). Check your scenario and quantities.`,
      );
    }
    return data as T;
  } catch (error) {
    if (
      error instanceof TypeError ||
      (error instanceof Error && error.name === 'AbortError')
    ) {
      throw new Error(
        'The backend is unavailable or the request timed out. Start the Python backend and try again.',
      );
    }
    throw error;
  } finally {
    clearTimeout(timer);
  }
}

export async function runSimulation(
  request: SimulationRequest,
): Promise<SimulationResponse> {
  return post<SimulationResponse>(
    '/api/simulation/run',
    {
      ...request,
      parameters: toSimulationParameters(request.parameters),
    },
    120000,
  );
}

export function toSimulationParameters(
  parameters: DisasterParameters,
): DisasterParameters {
  return {
    ...parameters,
    rainfall_intensity_mm_hr: rainfallMmPerHour(parameters),
    rainfall_input_unit: 'mm_per_hour',
  };
}

export async function allocateResources(
  request: ResourceAllocateRequest,
): Promise<ResourceAllocateResponse> {
  return post<ResourceAllocateResponse>(
    '/api/resources/allocate',
    request,
    30000,
  );
}

export async function getResourceState(): Promise<Pick<
  MapInitResponse,
  'warehouses' | 'distribution_points'
> & { simulation_id: string | null } | null> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 5000);
  try {
    const res = await fetch(`${API_BASE_URL}/api/resources/state`, {
      signal: controller.signal,
    });
    return res.ok ? await res.json() : null;
  } catch {
    return null;
  } finally {
    clearTimeout(timer);
  }
}

export function adaptBackendAdvisoryToClient(raw: any): import('./types').AIAdvisorData {
  if (!raw) {
    return {
      risk_radar_level: 'DEFCON 3 (ELEVATED)',
      radar_score: 65,
      tactical_summary: 'Hydrologic monitoring active. Prepare designated elevated shelters and dewatering pumps.',
      evacuation_advice: [],
      broadcast: {
        english: 'Chennai Flood Lab Advisory in effect. Monitor local water accumulation.',
        tamil: 'சென்னை வெள்ள ஆலோசனை நடைமுறையில் உள்ளது. நீர் தேக்கத்தை கண்காணிக்கவும்.',
        timestamp: new Date().toISOString(),
        code: 'ADVISORY-MONITOR',
        alert_level: 'Orange Alert',
      },
      bottlenecks: [],
      ward_rankings: [],
    };
  }

  const summary = raw.summary || {};
  const peakDepth = summary.peak_inundation_observed_m ?? 0.8;
  const radarScore = peakDepth <= 0 ? 0 : Math.min(99, Math.max(20, Math.round(peakDepth * 35 + (summary.total_stranded_citizens > 0 ? 30 : 10))));

  const radarLevel =
    radarScore >= 85
      ? 'DEFCON 1 (CRITICAL)'
      : radarScore >= 65
      ? 'DEFCON 2 (SEVERE)'
      : radarScore >= 40
      ? 'DEFCON 3 (ELEVATED)'
      : 'DEFCON 4 (ADVISORY)';

  const casualty = raw.casualty_prevention_indicators || {};
  const bottlenecks = (casualty.chokepoints_and_bottlenecks || []).map((b: any, idx: number) => ({
    id: `BN-${idx + 1}`,
    corridor_name: `${b.source_node} → ${b.target_node}`,
    zone: 'GCC Arterial Network',
    water_depth_m: b.water_depth_m ?? 0,
    traffic_choke_status: b.delay_factor >= 2.5 ? 'SEVERED' : 'HIGH IMPEDANCE',
    suggested_detour: b.directive || 'Divert to elevated bypass corridors',
  }));

  const traps = casualty.stranded_population_traps || [];
  const evacuationAdvice = traps.map((t: any, idx: number) => ({
    id: `ADV-${idx + 1}`,
    priority: t.urgency === 'CRITICAL' ? 'CRITICAL' : t.urgency === 'HIGH' ? 'URGENT' : 'MONITOR',
    title: `Emergency Rescue: ${t.name}`,
    details: `${t.trapped_population?.toLocaleString() ?? 0} residents trapped at water depth ${t.water_depth_m ?? 0}m. Protocol: ${t.rescue_protocol || 'Dispatch rescue boat'}`,
    affected_ward: t.name,
    target_shelter: 'Nearest Safe Relief Center',
    mode_suggested: (t.water_depth_m >= 1.2 ? 'IAF Chetak Sortie' : t.water_depth_m >= 0.5 ? 'Amphibious Zodiac' : 'High-Clearance 6x6 Truck') as any,
  }));

  const broadcasts = raw.bilingual_emergency_broadcasts || {};
  const wardRankings = (raw.ward_vulnerability_index || []).map((w: any) => ({
    ward_id: w.zone_id || `W-${w.zone_number}`,
    ward_name: w.zone_name || `Zone ${w.zone_number}`,
    risk_index: Math.round(w.vulnerability_index ?? 0),
    vulnerable_population: w.population ?? 0,
    water_depth_m: w.peak_flood_depth_m ?? 0,
    trend: (w.peak_flood_depth_m >= 1.0 ? 'rising' : w.peak_flood_depth_m >= 0.4 ? 'peaking' : 'receding') as any,
  }));

  return {
    risk_radar_level: radarLevel,
    radar_score: radarScore,
    tactical_summary: summary.overall_severity
      ? `Severity level: ${summary.overall_severity}. ${summary.critical_wards_count || 0} critical zones, ${summary.total_stranded_citizens?.toLocaleString() || 0} residents require immediate attention.`
      : 'Continuous hydrodynamic decision analysis active.',
    evacuation_advice: evacuationAdvice,
    snapshot_hour: raw.snapshot_hour,
    broadcast: {
      english: broadcasts.siren_broadcast_english || 'No sample bulletin is available for this scenario.',
      tamil: broadcasts.siren_broadcast_tamil || 'இந்த மாதிரி காட்சிக்கு அறிக்கை இல்லை.',
      timestamp: raw.generated_at || new Date().toISOString(),
      code: `WARN-${radarLevel.split(' ')[1] || 'ACT'}`,
      alert_level: peakDepth <= 0 ? 'No modeled flood' : radarScore >= 80 ? 'Emergency Evacuation' : radarScore >= 60 ? 'Red Alert' : 'Orange Alert',
    },
    bottlenecks: bottlenecks,
    ward_rankings: wardRankings,
    mcdm_topsis_rankings: raw.mcdm_topsis_rankings,
  };
}

export async function getAdvisory(simulationId?: string): Promise<import('./types').AIAdvisorData | null> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 6000);
  try {
    const res = await fetch(`${API_BASE_URL}/api/advisory${simulationId ? `?simulation_id=${encodeURIComponent(simulationId)}` : ''}`, {
      signal: controller.signal,
    });
    if (res.ok) {
      const data = await res.json();
      return adaptBackendAdvisoryToClient(data);
    }
  } catch {
    // Offline or unreachable
  } finally {
    clearTimeout(timer);
  }
  return null;
}
