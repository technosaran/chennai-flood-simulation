import pytest


@pytest.mark.parametrize("zone", [
    {"type": "circle", "coordinates": [[13.0]]},
    {"type": "polygon", "coordinates": [[13.0, 80.2], [13.0, 80.2], [13.0, 80.2]]},
    {"type": "polygon", "coordinates": [[13.0, 80.2], [13.02, 80.22], [13.02, 80.2], [13.0, 80.22]]},
])
def test_invalid_geometry_is_rejected_before_computation(client, zone):
    response = client.post('/api/simulation/run', json={'flood_zones': [zone], 'parameters': {}})
    assert response.status_code == 422


def test_manual_allocation_updates_depot_and_detects_stale_scenario(client):
    result = client.post('/api/simulation/run', json={'flood_zones': [], 'parameters': {'flood_depth_meters': 0}})
    assert result.status_code == 200
    simulation_id = result.json()['simulation_id']
    state = client.get('/api/resources/state').json()
    warehouse = state['warehouses'][0]
    destination = state['distribution_points'][0]
    request = {'simulation_id': simulation_id, 'warehouse_id': warehouse['id'],
               'shelter_or_point_id': destination['id'],
               'supplies': {'water_litres': 10, 'food_rations': 5, 'medical_kits': 1}}
    allocated = client.post('/api/resources/allocate', json=request)
    assert allocated.status_code == 200
    after = client.get('/api/resources/state').json()
    depot = next(w for w in after['warehouses'] if w['id'] == warehouse['id'])
    assert depot['supplies']['water_litres'] == warehouse['supplies']['water_litres'] - 10
    point = next(p for p in after['distribution_points'] if p['id'] == destination['id'])
    assert point['current_stock']['water_litres'] == destination['current_stock']['water_litres'] + 10
    client.post('/api/simulation/run', json={'flood_zones': [], 'parameters': {}})
    assert client.post('/api/resources/allocate', json=request).status_code == 409
