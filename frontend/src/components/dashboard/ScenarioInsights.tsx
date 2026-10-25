'use client';
import { BrainCircuit, Clock3, ArrowUpRight, Users, Route } from 'lucide-react';
import { SimulationResponse } from '@/lib/types';

export default function ScenarioInsights({ result, selected, onSelect }: {
  result: SimulationResponse; selected: number; onSelect: (index: number) => void;
}) {
  const timeline = result.timeline;
  const peak = timeline.reduce((best, step, i) => step.metrics.total_affected_population > timeline[best].metrics.total_affected_population ? i : best, 0);
  const current = timeline[selected];
  const max = Math.max(1, ...timeline.map(s => s.metrics.total_affected_population));
  const diagnostics = result.diagnostics;
  const capacity = current.shelter_allocations.reduce((n, s) => n + s.total_capacity, 0);
  const occupied = current.shelter_allocations.reduce((n, s) => n + s.allocated_evacuees, 0);
  const rescued = current.metrics.unassigned_stranded_population;
  const available = current.shelter_allocations.filter(s => s.status !== 'compromised' && s.remaining_capacity > 0).length;
  return (
    <section className="scenario-insights" aria-label="Scenario analysis">
      <div className="insight-heading">
        <div><span className="eyebrow">RESPONSE OUTLOOK</span><h3>Every hour changes the plan.</h3></div>
        <span className="computation-badge"><Clock3 size={13} />{diagnostics ? `${(diagnostics.compute_time_ms / 1000).toFixed(2)}s compute` : `${timeline.length} snapshots`}</span>
      </div>
      <div className="response-priorities">
        <article><span className="priority-label">RESCUE NEED · T+{current.hour}h</span><strong className={rescued > 0 ? 'rescue-number' : ''}>{rescued.toLocaleString()} <small>people</small></strong><p>{rescued > 0 ? `${current.isolated_clusters.length} affected clusters need modeled rescue support.` : 'No unassigned affected population in this snapshot.'}</p></article>
        <article><span className="priority-label">SHELTER ASSIGNMENTS</span><strong>{occupied.toLocaleString()} <small>/ {capacity.toLocaleString()}</small></strong><p>{available} shelters have usable space. Flood-compromised shelters cannot accept assignments.</p></article>
        <article><span className="priority-label">RELIEF DISPATCHES</span><strong>{current.supply_routes.features.length} <small>routes</small></strong><p>Deliveries shown for this hour. Inventory accumulates across the run; manual dispatches apply at the final hour.</p></article>
      </div>
      <div className="insight-content">
        <div className="exposure-chart">
          <div className="chart-caption"><span><Users size={13} /> Estimated people affected</span><strong>{current.metrics.total_affected_population.toLocaleString()} at T+{current.hour}h</strong></div>
          <div className="hour-bars">
            {timeline.map((s, i) => (
              <button key={i} className={selected === i ? 'selected' : ''} onClick={() => onSelect(i)} aria-label={`View hour ${s.hour}: ${s.metrics.total_affected_population.toLocaleString()} people affected`} aria-pressed={selected === i}>
                <span className="bar-track"><i style={{ height: `${Math.max(3, 100 * s.metrics.total_affected_population / max)}%` }} /></span>
                <small>{s.hour}h</small>
              </button>
            ))}
          </div>
          <button className="peak-link" onClick={() => onSelect(peak)}>Inspect peak exposure · T+{timeline[peak].hour}h <ArrowUpRight size={13} /></button>
        </div>
        <div className="model-context">
          <span className="model-label"><BrainCircuit size={15} />{diagnostics?.demand_model.name || 'Demand planning'}</span>
          <p>{diagnostics?.ml_predictions ?? 0} ML estimates · {diagnostics?.rule_predictions ?? 0} rule estimates across the run.</p>
          <p>Demand estimation leverages split-conformal prediction intervals with formal uncertainty bounds per resource.</p>
          <span className="routing-note"><Route size={13} />Flood-aware routes with shelter capacity and congestion.</span>
        </div>
      </div>
    </section>
  );
}
