'use client';

import type { TimelineStep } from '@/lib/types';

interface MetricsOverviewProps {
  currentStep: TimelineStep | null;
  onCardClick?: (metricType: 'flood' | 'people' | 'evac' | 'rescue' | 'roads' | 'shelters') => void;
}

export default function MetricsOverview({ currentStep, onCardClick }: MetricsOverviewProps) {
  const m = currentStep?.metrics;
  const foodAlloc = (currentStep?.shelter_allocations || []).reduce(
    (sum, s) => sum + (s.allocated_supplies?.food_rations || 0),
    0,
  );
  const waterAlloc = (currentStep?.shelter_allocations || []).reduce(
    (sum, s) => sum + (s.allocated_supplies?.water_litres || 0),
    0,
  );

  const cards = [
    {
      id: 'people',
      label: currentStep?.rescue_fleet_plan?.mode === 'continuous' ? 'Baseline flood exposure' : 'Affected people',
      value: m?.total_affected_population.toLocaleString(),
      unit: currentStep?.rescue_fleet_plan?.mode === 'continuous' ? 'people before rescue removals' : 'people in flood zones',
    },
    {
      id: 'evac',
      label: currentStep?.rescue_fleet_plan?.mode === 'continuous' ? 'Ground shelter assignments' : 'Assigned to shelters',
      value: m?.total_evacuated_population.toLocaleString(),
      unit: 'people · selected hour',
    },
    {
      id: 'rescue',
      label: 'Still needing rescue',
      value: m?.unassigned_stranded_population.toLocaleString(),
      unit: currentStep?.rescue_fleet_plan?.mode === 'continuous' ? 'awaiting rescue assignment' : 'unassigned people',
    },
    {
      id: 'flood',
      label: 'Modeled flood area',
      value: m?.total_flooded_area_sq_km.toFixed(1),
      unit: 'km² · modeled area',
    },
  ] as const;

  return (
    <section className="clean-metrics" aria-label="Simulation metrics">
      {cards.map((card) => (
        <button
          key={card.id}
          onClick={() => onCardClick?.(card.id)}
          disabled={!m}
          className="clean-metric"
        >
          <span>{card.label}</span>
          <strong
            className={
              card.id === 'rescue' && (m?.unassigned_stranded_population || 0) > 0
                ? 'text-amber-800'
                : ''
            }
          >
            {card.value ?? '—'}
          </strong>
          <small>{card.unit}</small>
        </button>
      ))}
    </section>
  );
}
