export interface RealtimeWeather {
  location: string; requested_location: number[]; grid_location: number[]; observed_at: string; hourly_at: string;
  temperature_c: number; humidity_pct: number; wind_kmh: number; precipitation_mm: number; interval_seconds: number;
  hourly_precipitation_mm: number; rainfall_mm_hr: number; attribution: string; source_url: string; interpretation: string;
}
export interface RealtimeAlerts {
  items: { id: string; title: string; description: string; issuer: string; issued_at: string; url: string }[];
  matched_count: number; scope: string; source_url: string; interpretation: string;
}
export interface RealtimeSource<T> {
  status: 'fresh' | 'stale' | 'unavailable'; fetched_at: string | null; attempted_at: string | null;
  age_seconds: number | null; error: string | null; data: T | null;
}
export interface RealtimeSnapshot {
  checked_at: string; refresh_interval_seconds: number; cache_warning: string | null;
  weather: RealtimeSource<RealtimeWeather>; alerts: RealtimeSource<RealtimeAlerts>;
}

export function canApplyWeather(source?: RealtimeSource<RealtimeWeather>, now = Date.now()): boolean {
  if (!source?.data || source.status !== 'fresh' || source.error || !source.fetched_at) return false;
  const ages = [source.fetched_at, source.data.observed_at, source.data.hourly_at].map(time => now-Date.parse(time));
  const rate = source.data.rainfall_mm_hr;
  return ages.every(age => Number.isFinite(age) && age >= -1200000) && ages[0] <= 900000 && ages[1] <= 7200000 && ages[2] <= 7200000 && Number.isFinite(rate) && rate >= 0 && rate <= 350;
}
