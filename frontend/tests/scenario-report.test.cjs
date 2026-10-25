const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const Module = require('node:module');
const ts = require('typescript');
const file = path.resolve(__dirname, '../src/lib/scenario-report.ts');
const compiled = ts.transpileModule(fs.readFileSync(file, 'utf8'), { compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2020 } }).outputText;
const loaded = new Module(file, module);
loaded._compile(compiled, file);
const { createScenarioReport } = loaded.exports;

function fixture() {
  const step = (hour, affected, assigned, stranded) => ({ hour, metrics: { total_affected_population: affected, total_evacuated_population: assigned, unassigned_stranded_population: stranded, total_flooded_area_sq_km: hour, severed_roads_count: hour }, flood_polygons: { features: [] }, evacuation_routes: { features: [] }, supply_routes: { features: [] } });
  return { simulation_id: '<script>bad()</script>', computed_at: '2026-10-18T12:00:00Z', timeline: [step(0, 120, 100, 20), step(1, 80, 70, 10)], inventory_ledger: { shelters: [{ name: '<img src=x onerror=bad()>', deficit: { water_litres: 17, food_rations: 12, medical_kits: 2 } }] } };
}
const parameters = { rainfall_intensity_mm_hr: 140, flood_depth_meters: 2.2, spread_rate_meters_hr: 280, duration_hours: 1 };

test('export escapes user-controlled text and contains no executable or remote map dependencies', () => {
  const html = createScenarioReport(fixture(), parameters);
  assert.ok(html.includes('&lt;script&gt;bad()&lt;/script&gt;'));
  assert.ok(!html.includes('<script>'));
  assert.ok(!html.includes('<img'));
  assert.ok(!html.includes('<link'));
  assert.ok(html.includes('<svg'));
  assert.ok(html.includes('Final resource shortages'));
  assert.ok(html.includes('<td>17</td>'));
});

test('report selects peak exposure snapshot and does not sum hourly plans', () => {
  const html = createScenarioReport(fixture(), parameters);
  assert.ok(html.includes('Peak exposure snapshot T+0h'));
  assert.ok(html.includes('Peak affected<strong>120</strong>'));
  assert.ok(html.includes('Peak assigned<strong>100</strong>'));
  assert.ok(html.includes('must not be added'));
  assert.ok(html.includes('Unavailable at export time'));
});

test('empty timelines cannot create a misleading completed report', () => {
  assert.throws(() => createScenarioReport({ ...fixture(), timeline: [] }, parameters), /completed timeline/);
});

test('imported report retains escaped file provenance', () => {
  const html = createScenarioReport({ ...fixture(), archive_origin: 'Imported file; evidence not independently verified. <script>bad()</script>' }, parameters);
  assert.ok(html.includes('Imported file; evidence not independently verified.'));
  assert.ok(html.includes('&lt;script&gt;bad()&lt;/script&gt;'));
  assert.ok(!html.includes('<script>'));
});

test('configured fleet estimates export separately from completed evacuation counts', () => {
  const result = fixture();
  result.timeline[0].rescue_fleet_plan = { planning_window_minutes: 60, snapshot_demand: 20, provisionally_served: 10, still_needing_support: 10, trips: [{}] };
  const html = createScenarioReport(result, parameters);
  assert.ok(html.includes('Limited rescue fleet estimates'));
  assert.ok(html.includes('not executed rescues'));
  assert.ok(html.includes('Provisional service'));
  assert.ok(html.includes('Peak assigned<strong>100</strong>'));
});

test('handoff journeys, recommendations and rescue map export with escaped text', () => {
  const result = fixture();
  result.timeline[0].rescue_fleet_plan = {
    planning_window_minutes: 120, snapshot_demand: 20, provisionally_served: 12, still_needing_support: 8,
    trips: [{ mode:'boats', geometry:{ type:'LineString', coordinates:[[80.2,13],[80.21,13.01]] } }],
    journeys: [{ kind:'boat_to_truck', journey_id:'J-1', vehicle_ids:['BOATS-01','TRUCKS-01'], people:12, completed_minutes:90 }],
    recommendations: [{ title:'<script>bad()</script>', message:'Add boats & rerun' }],
  };
  const html = createScenarioReport(result, parameters);
  assert.ok(html.includes('Boat → truck journeys'));
  assert.ok(html.includes('Passengers counted once'));
  assert.ok(html.includes('BOATS-01 → TRUCKS-01'));
  assert.ok(html.includes('&lt;script&gt;bad()&lt;/script&gt;'));
  assert.ok(html.includes('Add boats &amp; rerun'));
  assert.ok(html.includes('stroke="#0891b2"'));
});

test('continuous export labels cumulative arrivals and avoids repeating carried handoff journeys', () => {
  const result = fixture();
  const journey = { kind:'boat_to_truck',journey_id:'UNIQUE-HANDOFF',vehicle_ids:['BOATS-01','TRUCKS-01'],people:12,completed_minutes:90 };
  for (let i=0;i<2;i++) result.timeline[i].rescue_fleet_plan={mode:'continuous',planning_window_minutes:120,snapshot_demand:20,provisionally_served:i?0:12,still_needing_support:8,trips:[],journeys:[journey],new_journey_ids:i?[]:['UNIQUE-HANDOFF'],cumulative_rescued:i?12:0,committed_not_arrived:i?0:12};
  const html=createScenarioReport(result,parameters);
  assert.ok(html.includes('Continuous simulated rescue schedule'));
  assert.ok(html.includes('Cumulative simulated arrivals'));
  assert.equal(html.split('UNIQUE-HANDOFF').length-1,1);
});
