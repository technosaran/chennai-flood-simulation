import type { DisasterParameters } from './types';

export function rainfallMmPerHour(parameters: Pick<DisasterParameters, 'rainfall_intensity_mm_hr' | 'rainfall_input_unit'>): number {
  const value = parameters.rainfall_intensity_mm_hr;
  // Old presets/browser snapshots used levels 1-5. Explicit physical readings,
  // including exactly 1, 2, 3, 4 or 5 mm/h, must never be mapped to a level.
  return parameters.rainfall_input_unit === 'mm_per_hour' ? value : ([0,25,50,90,140,220][value] ?? value);
}
