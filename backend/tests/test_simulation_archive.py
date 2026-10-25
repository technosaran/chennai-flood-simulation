from copy import deepcopy
import sqlite3
import json
import pytest
from backend.app.main import app
from backend.app.services.simulation_archive import SimulationArchive, ArchiveCorrupt


@pytest.fixture
def archive(client, tmp_path, monkeypatch):
    store = SimulationArchive(tmp_path / 'snapshots.sqlite3')
    monkeypatch.setattr(app.state, 'simulation_archive', store)
    return store


def run(client):
    response = client.post('/api/simulation/run', json={'flood_zones': [{'type': 'circle', 'center': [12.9796, 80.2185], 'radius_meters': 700}],
                          'parameters': {'rainfall_intensity_mm_hr': 90, 'duration_hours': 1, 'flood_depth_meters': 1},
                          'rescue_fleet': {'planning_window_minutes': 240, 'trucks': {'count': 0}, 'boats': {'count': 0}, 'helicopters': {'count': 1, 'speed_kmh': 120}}})
    assert response.status_code == 200
    return response.json()


def test_complete_snapshot_survives_store_recreation(client, archive):
    result = run(client)
    saved = client.post('/api/simulations/saved', json={'simulation_id': result['simulation_id'], 'name': ' Rainfall study '})
    assert saved.status_code == 200, saved.text
    identity = saved.json()['id']
    reopened = SimulationArchive(archive.path).get(identity)
    assert reopened['result'] == result
    assert reopened['read_only'] is True
    assert reopened['name'] == 'Rainfall study'
    assert reopened['view']['parameters']['rainfall_intensity_mm_hr'] == 3
    assert reopened['view']['zones'][0]['coordinates'] == [[12.9796, 80.2185]]
    assert reopened['evidence']['demand']['evaluation_status'] == 'verified'
    assert reopened['map_data']['shelters']
    assert reopened['result']['timeline'][0]['rescue_fleet_plan'] is not None
    listing = client.get('/api/simulations/saved').json()
    assert listing['total'] == 1 and listing['items'][0]['fleet_included']
    assert client.get('/api/simulations/saved/' + identity).json() == reopened
    # Reopening must not depend on the in-memory active result surviving startup.
    active = app.state.latest_simulation
    app.state.latest_simulation = None
    try:
        assert client.get('/api/simulations/saved/' + identity).json()['result'] == result
        assert client.get('/api/simulation/latest').status_code == 404
    finally:
        app.state.latest_simulation = active


def test_reading_archive_never_replaces_active_inventory(client, archive):
    first = run(client)
    identity = client.post('/api/simulations/saved', json={'simulation_id': first['simulation_id'], 'name': 'Old run'}).json()['id']
    current = run(client)
    before = deepcopy(app.state.supply_solver.get_ledger_snapshot())
    assert client.get('/api/simulations/saved/' + identity).status_code == 200
    assert client.get('/api/simulation/latest').json() == current
    assert app.state.supply_solver.get_ledger_snapshot() == before
    assert client.post('/api/simulations/saved', json={'simulation_id': first['simulation_id'], 'name': 'Stale'}).status_code == 409


def test_saved_allocations_are_frozen_when_new_allocations_happen(client, archive):
    original = run(client)
    identity = client.post('/api/simulations/saved', json={'simulation_id': original['simulation_id'], 'name': 'Before allocation'}).json()['id']
    solver = app.state.supply_solver
    destination = next(iter(solver.point_demands))
    allocated = client.post('/api/resources/allocate', json={'simulation_id': original['simulation_id'], 'shelter_or_point_id': destination, 'supplies': {'water_litres': 1}})
    assert allocated.status_code == 200, allocated.text
    latest = client.get('/api/simulation/latest').json()
    newer = client.post('/api/simulations/saved', json={'simulation_id': original['simulation_id'], 'name': 'After allocation'}).json()['id']
    assert archive.get(identity)['result']['inventory_ledger'] == original['inventory_ledger']
    assert archive.get(newer)['result']['inventory_ledger'] == latest['inventory_ledger']
    assert archive.get(newer)['result']['timeline'] == latest['timeline']


def test_corrupt_archive_is_rejected_without_changing_current_run(client, archive):
    current = run(client)
    identity = client.post('/api/simulations/saved', json={'simulation_id': current['simulation_id'], 'name': 'Integrity check'}).json()['id']
    with sqlite3.connect(archive.path) as connection:
        connection.execute('UPDATE snapshots SET payload=? WHERE id=?', (b'broken-gzip', identity))
    with pytest.raises(ArchiveCorrupt):
        archive.get(identity)
    assert client.get('/api/simulations/saved/' + identity).status_code == 409
    assert client.get('/api/simulation/latest').json() == current


def test_archive_validation_pagination_and_missing_record(client, archive):
    current = run(client)
    assert client.post('/api/simulations/saved', json={'simulation_id': current['simulation_id'], 'name': '  '}).status_code == 422
    for name in ['A', 'B', 'C']:
        assert client.post('/api/simulations/saved', json={'simulation_id': current['simulation_id'], 'name': name}).status_code == 200
    page = client.get('/api/simulations/saved?offset=1&limit=1').json()
    assert page['total'] == 3 and len(page['items']) == 1 and page['items'][0]['name'] == 'B'
    assert client.get('/api/simulations/saved/not-found').status_code == 404
    assert client.get('/api/simulations/saved?limit=101').status_code == 422


def portable_snapshot(client, archive):
    result = run(client)
    identity = client.post('/api/simulations/saved', json={'simulation_id': result['simulation_id'], 'name': 'Portable run'}).json()['id']
    return archive.get(identity)


def test_import_preserves_results_without_activating_or_overwriting(client, archive):
    exported = portable_snapshot(client, archive)
    current = run(client)
    before = deepcopy(app.state.supply_solver.get_ledger_snapshot())
    for _ in range(2):
        response = client.post('/api/simulations/saved/import', json=exported)
        assert response.status_code == 200, response.text
        imported = archive.get(response.json()['id'])
        assert imported['id'] != exported['id']
        for key in ('result', 'map_data', 'view', 'evidence'):
            assert imported[key] == exported[key]
        assert imported['read_only'] is True
        assert imported['imported_from']['name'] == 'Portable run'
    assert archive.list()['total'] == 3
    assert archive.list()['items'][0]['imported'] is True
    assert archive.get(exported['id']) == exported
    assert client.get('/api/simulation/latest').json() == current
    assert app.state.supply_solver.get_ledger_snapshot() == before


@pytest.mark.parametrize('damage', ['version', 'timeline', 'coordinate', 'fleet', 'numeric', 'map', 'parameters', 'advice'])
def test_malformed_imports_are_rejected_atomically(client, archive, damage):
    exported = portable_snapshot(client, archive)
    if damage == 'version': exported['schema_version'] = 2
    elif damage == 'timeline': exported['result']['timeline'] = []
    elif damage == 'coordinate': exported['map_data']['center'] = [999, 80]
    elif damage == 'fleet': exported['result']['timeline'][0]['rescue_fleet_plan']['vehicles'] = 'wrong'
    elif damage == 'numeric': exported['result']['timeline'][0]['metrics']['total_affected_population'] = True
    elif damage == 'map': del exported['map_data']['shelters'][0]['location']
    elif damage == 'parameters': del exported['view']['parameters']['duration_hours']
    elif damage == 'advice': exported['result']['ai_advisory']['ward_vulnerability_index'] = {}
    response = client.post('/api/simulations/saved/import', json=exported)
    assert response.status_code == 422, response.text
    assert archive.list()['total'] == 1


def test_import_bad_json_nonfinite_and_size_limits(client, archive, monkeypatch):
    exported = portable_snapshot(client, archive)
    for raw in (b'not json', b'\xff', b'{"schema_version":1,"schema_version":1}', json.dumps(exported).replace('"schema_version": 1', '"schema_version": NaN').encode()):
        assert client.post('/api/simulations/saved/import', content=raw).status_code == 422
    from backend.app.api import archive as archive_api
    monkeypatch.setattr(archive_api, 'MAX_IMPORT_BYTES', 64)
    assert client.post('/api/simulations/saved/import', content=b' ' * 65).status_code == 413
    assert archive.list()['total'] == 1


def test_import_works_without_an_active_simulation(client, archive):
    exported = portable_snapshot(client, archive)
    app.state.latest_simulation = None
    assert client.post('/api/simulations/saved/import', json=exported).status_code == 200
    assert client.get('/api/simulation/latest').status_code == 404


@pytest.mark.parametrize('damage', ['phase_time', 'phase_geometry', 'transfer_point', 'journeys', 'recommendations'])
def test_import_rejects_invalid_rescue_playback_payloads(client, archive, damage):
    exported = portable_snapshot(client, archive)
    fleet = next(s['rescue_fleet_plan'] for s in exported['result']['timeline'] if s['rescue_fleet_plan']['trips'])
    if damage == 'phase_time':
        fleet['trips'][0]['phases'][0]['end_minutes'] = -1
    elif damage == 'phase_geometry':
        fleet['trips'][0]['phases'][0]['geometry']['coordinates'] = [[80, 999], [80, 13]]
    elif damage == 'transfer_point':
        fleet['transfer_points'] = [{'id': 'P', 'name': 'Bad', 'access': 'unknown', 'depth_m': 0, 'location': [999, 80]}]
    elif damage == 'journeys':
        fleet['journeys'] = [{'kind': 'boat_to_truck'}]
    else:
        fleet['recommendations'] = 'invalid'
    response = client.post('/api/simulations/saved/import', json=exported)
    assert response.status_code == 422
    assert archive.list()['total'] == 1
