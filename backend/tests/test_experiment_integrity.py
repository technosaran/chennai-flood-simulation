import pytest
from backend.app.main import app


def run(client, **overrides):
    body = {"flood_zones": [], "parameters": {"flood_depth_meters": 0, "duration_hours": 1}}
    body.update(overrides)
    response = client.post('/api/simulation/run', json=body)
    assert response.status_code == 200, response.text
    return response.json()


def test_selected_warehouse_is_the_only_dispatch_source(client):
    warehouse = client.get('/api/map/init').json()['warehouses'][0]['id']
    result = run(client, warehouse_ids=[warehouse])
    routes = [f for s in result['timeline'] for f in s['supply_routes']['features']]
    assert routes
    assert {f['properties']['warehouse_id'] for f in routes} == {warehouse}
    for stock in result['inventory_ledger']['warehouses']:
        if stock['warehouse_id'] != warehouse:
            assert not any(stock['allocated_stock'].values())


def test_explicit_empty_facilities_do_not_enable_all_facilities(client):
    result = run(client, warehouse_ids=[], shelter_ids=[])
    assert all(not s['shelter_allocations'] and not s['supply_routes']['features'] for s in result['timeline'])


@pytest.mark.parametrize('field', ['shelter_ids', 'warehouse_ids'])
def test_invalid_facilities_preserve_previous_run(client, field):
    previous = run(client)
    response = client.post('/api/simulation/run', json={
        'parameters': {}, 'flood_zones': [], field: ['unknown-facility']})
    assert response.status_code == 422
    assert client.get('/api/simulation/latest').json() == previous


def test_manual_dispatch_is_reflected_in_latest_snapshot(client):
    previous = run(client, warehouse_ids=[])
    state = client.get('/api/resources/state').json()
    request = {'simulation_id': previous['simulation_id'],
               'warehouse_id': state['warehouses'][0]['id'],
               'shelter_or_point_id': state['distribution_points'][0]['id'],
               'supplies': {'water_litres': 11}}
    allocation = client.post('/api/resources/allocate', json=request)
    assert allocation.status_code == 200, allocation.text
    latest = client.get('/api/simulation/latest').json()
    assert latest['inventory_ledger'] == allocation.json()['ledger']
    assert latest['timeline'][-1]['inventory_status']['allocated_water_litres'] == 11
    assert latest['timeline'][0]['inventory_status']['allocated_water_litres'] == 0
    assert len(latest['timeline'][-1]['supply_routes']['features']) == 1
    assert client.get('/api/resources/state').json()['simulation_id'] == previous['simulation_id']


def test_allocation_exception_rolls_back_committed_stock(client, monkeypatch):
    previous = run(client, warehouse_ids=[])
    solver = app.state.supply_solver
    baseline = solver.get_ledger_snapshot()
    original = solver.allocate_supplies
    def fail_after_commit(*args, **kwargs):
        original(*args, **kwargs)
        raise ValueError('Simulated failure after planning')
    monkeypatch.setattr(solver, 'allocate_supplies', fail_after_commit)
    response = client.post('/api/resources/allocate', json={
        'simulation_id': previous['simulation_id'],
        'shelter_or_point_id': baseline['distribution_points'][0]['distribution_point_id'],
        'supplies': {'water_litres': 10}})
    assert response.status_code == 400
    assert solver.get_ledger_snapshot() == baseline
    assert client.get('/api/simulation/latest').json() == previous


def test_peak_summary_and_reproduction_input_are_explicit(client):
    result = run(client)
    assert result['summary']['peak_affected_population'] == max(s['metrics']['total_affected_population'] for s in result['timeline'])
    assert result['scenario']['parameters']['duration_hours'] == 1
    assert 'not cumulative' in result['summary']['semantics']
