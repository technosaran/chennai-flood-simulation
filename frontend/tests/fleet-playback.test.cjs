const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const Module = require('node:module');
const ts = require('typescript');
const file = path.resolve(__dirname, '../src/lib/fleet-playback.ts');
const loaded = new Module(file, module);
loaded._compile(ts.transpileModule(fs.readFileSync(file, 'utf8'), { compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2020 } }).outputText, file);
const { positionAlongLine, vehicleAtMinute } = loaded.exports;
const line = points => ({ type: 'LineString', coordinates: points });
const trip = { vehicle_id: 'TRUCKS-01', depart_minutes: 10, return_available_minutes: 40, geometry: line([[80,13],[80.1,13],[80,13]]), phases: [
  { status: 'travelling_to_transfer', start_minutes: 10, end_minutes: 20, geometry: line([[80,13],[80.1,13]]) },
  { status: 'waiting_for_boat', start_minutes: 20, end_minutes: 30, geometry: line([[80.1,13],[80.1,13]]) },
  { status: 'returning', start_minutes: 30, end_minutes: 40, geometry: line([[80.1,13],[80,13]]) },
] };
test('position uses distance along geometry and preserves GeoJSON coordinate order', () => {
  const position = positionAlongLine([[80,13],[80.01,13],[80.1,13]], .5);
  assert.ok(Math.abs(position[0]-13)<1e-9);
  assert.ok(Math.abs(position[1]-80.05)<1e-9);
  assert.equal(positionAlongLine([], .5), null);
  assert.deepEqual(positionAlongLine([[80,13],[80,13]], .5), [13,80]);
});
test('playback handles readiness, stationary handoff waiting, return and completion', () => {
  assert.equal(vehicleAtMinute([trip], 9).status, 'not_ready');
  assert.equal(vehicleAtMinute([trip], 10).status, 'travelling_to_transfer');
  assert.deepEqual(vehicleAtMinute([trip], 25).position, [13,80.1]);
  assert.equal(vehicleAtMinute([trip], 25).status, 'waiting_for_boat');
  assert.equal(vehicleAtMinute([trip], 30).status, 'returning');
  assert.equal(vehicleAtMinute([trip], 40).status, 'ready_at_base');
});
test('second trip supersedes first at the exact shared return/departure boundary', () => {
  const second = { ...trip, depart_minutes: 40, return_available_minutes: 70, phases: trip.phases.map(p => ({ ...p, start_minutes:p.start_minutes+30, end_minutes:p.end_minutes+30 })) };
  assert.equal(vehicleAtMinute([second, trip], 40).trip, second);
  assert.equal(vehicleAtMinute([{ ...trip, phases:undefined }], 15), null);
});
