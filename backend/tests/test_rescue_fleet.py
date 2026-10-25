from types import SimpleNamespace
import networkx as nx
import pytest
from pydantic import ValidationError
from backend.app.models.disaster import RescueFleetConfig
from backend.app.services.rescue_fleet import plan_rescue_fleet
from backend.app.services.geometry import haversine


class Roads:
    def __init__(self, disconnected=False):
        self.coords = {'A': [13., 80.2], 'B': [13., 80.21], 'C': [13., 80.22]}
        self.graph = nx.DiGraph()
        self.graph.add_nodes_from(self.coords)
        if not disconnected:
            for a in self.coords:
                for b in self.coords:
                    if a != b:
                        self.graph.add_edge(a, b, weight=1, distance_km=haversine(*self.coords[a], *self.coords[b]))
    def build_dynamic_graph(self, *args, **kwargs):
        return self.graph.copy()
    def find_nearest_node(self, lat, lon):
        return min(self.coords, key=lambda n: haversine(lat, lon, *self.coords[n]))
    def get_route_coordinates(self, path):
        return [self.coords[n] for n in path]


def config(mode='helicopters', count=1, **options):
    pools = {key: {'count': 0} for key in ('trucks', 'boats', 'helicopters')}
    pools[mode] = dict(count=count, seats=10, speed_kmh=120, handling_minutes=5, **options)
    return RescueFleetConfig(base_location=(13., 80.2), planning_window_minutes=60, **pools)


def plan(fleet, capacity=100, depth=1, roads=None, depth_function=None):
    clusters = [dict(cluster_id='P', name='Test cluster', location=[13., 80.21], trapped_population=100)]
    shelters = [dict(shelter_id='S', name='Test shelter', location=[13., 80.22], status='available', remaining_capacity=capacity)]
    flood = SimpleNamespace(get_point_depth=depth_function or (lambda lat, lon, zones: depth if abs(lon-80.21) < .0001 else 0))
    return plan_rescue_fleet(fleet, clusters, shelters, roads or Roads(), flood, [])


def test_vehicle_capacity_nonoverlap_deadlines_and_person_conservation():
    result = plan(config())
    assert len(result['trips']) > 1
    assert 0 < result['provisionally_served'] < 100
    assert result['provisionally_served'] + result['still_needing_support'] == 100
    assert sum(t['people'] for t in result['trips']) == result['provisionally_served']
    for trip in result['trips']:
        assert 0 < trip['people'] <= 10
        assert trip['depart_minutes'] < trip['dropoff_minutes'] <= 60
        assert trip['dropoff_minutes'] <= trip['return_available_minutes']
    for previous, following in zip(result['trips'], result['trips'][1:]):
        assert following['depart_minutes'] >= previous['return_available_minutes']


def test_shelter_reservations_cannot_exceed_residual_capacity():
    result = plan(config(), capacity=7)
    assert result['provisionally_served'] == 7
    assert result['safe_shelter_spaces_after'] == 0
    assert result['still_needing_support'] == 93
    assert result['unserved'][0]['reason'] == 'no_safe_shelter_space'


def test_zero_fleet_and_delayed_vehicles_cannot_serve_demand():
    assert plan(config(count=0))['provisionally_served'] == 0
    delayed = plan(config(ready_after_minutes=90))
    assert delayed['provisionally_served'] == 0
    assert delayed['vehicles'][0]['status_at_window_end'] == 'not_ready'


def test_extra_vehicles_increase_service_without_exceeding_demand():
    one = plan(config(count=1))
    two = plan(config(count=2))
    assert one['provisionally_served'] < two['provisionally_served'] <= 100


def test_boat_depth_and_truck_road_access_are_enforced():
    assert plan(config(mode='boats'), depth=0)['provisionally_served'] == 0
    assert plan(config(mode='boats'), depth=1)['provisionally_served'] > 0
    assert plan(config(mode='trucks'), depth=1)['provisionally_served'] == 0
    assert plan(config(mode='trucks'), depth=0, roads=Roads(disconnected=True))['provisionally_served'] == 0
    hazard = lambda lat, lon, zones: .4 if 80.204 < lon < 80.206 else 0
    assert plan(config(mode='trucks'), depth_function=hazard)['provisionally_served'] == 0
    assert plan(config(mode='trucks'), depth=0)['provisionally_served'] > 0


def test_flooded_destinations_and_full_shelters_cannot_accept_rescuees():
    assert plan(config(), capacity=0)['provisionally_served'] == 0
    assert plan(config(), depth_function=lambda *args: 1)['provisionally_served'] == 0


def test_configuration_bounds():
    with pytest.raises(ValidationError):
        RescueFleetConfig(trucks={'count': 20}, boats={'count': 20})
    with pytest.raises(ValidationError):
        RescueFleetConfig(base_location=(0, 0))
    with pytest.raises(ValidationError):
        RescueFleetConfig(trucks={'speed_kmh': float('nan')})


def test_unused_vehicles_explain_depth_access_and_time_constraints():
    flooded = plan(config(mode='trucks'), depth=1)
    assert flooded['vehicles'][0]['allocation_reason'] == 'pickup_depth_incompatible'
    dry = plan(config(mode='boats'), depth=0)
    assert dry['vehicles'][0]['allocation_reason'] == 'pickup_depth_incompatible'
    disconnected = plan(config(mode='trucks'), depth=0, roads=Roads(disconnected=True))
    assert disconnected['vehicles'][0]['allocation_reason'] == 'no_screened_road_access'
    slow = config(mode='boats')
    slow.boats.speed_kmh = 1
    timed = plan(slow)
    assert timed['vehicles'][0]['allocation_reason'] == 'trip_exceeds_planning_window'
    assert timed['vehicles'][0]['earliest_dropoff_minutes'] > 60


@pytest.mark.parametrize('mode,depth', [('trucks', 0), ('boats', 1), ('helicopters', 1)])
def test_planned_routes_use_geojson_and_include_base_pickup_shelter_return(mode, depth):
    result = plan(config(mode=mode), depth=depth)
    assert result['trips']
    for trip in result['trips']:
        assert trip['geometry']['type'] == 'LineString'
        coords = trip['geometry']['coordinates']
        assert coords[0] == coords[-1] == [80.2, 13.]
        assert [80.21, 13.] in coords
        assert [80.22, 13.] in coords


def test_live_simulation_fleet_output_preserves_ground_planning(client):
    body = {'flood_zones': [{'type': 'circle', 'center': [12.9796, 80.2185], 'radius_meters': 700}],
            'parameters': {'flood_depth_meters': 2, 'duration_hours': 2, 'rainfall_intensity_mm_hr': 90}}
    original = client.post('/api/simulation/run', json=body).json()
    fleet = config().model_dump()
    fleet['planning_window_minutes'] = 240
    response = client.post('/api/simulation/run', json={**body, 'rescue_fleet': fleet})
    assert response.status_code == 200, response.text
    result = response.json()
    assert any(step['rescue_fleet_plan']['provisionally_served'] > 0 for step in result['timeline'])
    for old, step in zip(original['timeline'], result['timeline']):
        assert {k: v for k, v in old['metrics'].items() if k != 'compute_time_ms'} == {k: v for k, v in step['metrics'].items() if k != 'compute_time_ms'}
        assert old['inventory_status'] == step['inventory_status']
        assert old['shelter_allocations'] == step['shelter_allocations']
        fleet_plan = step['rescue_fleet_plan']
        assert fleet_plan['snapshot_demand'] == step['metrics']['unassigned_stranded_population']
        assert fleet_plan['provisionally_served'] + fleet_plan['still_needing_support'] == fleet_plan['snapshot_demand']
    assert client.post('/api/simulation/run', json={**body, 'rescue_fleet': {'boats': {'count': -1}}}).status_code == 422


def transfer_plan(capacity=100, window=60, enabled=True, truck_delay=0, disconnected=False):
    fleet = RescueFleetConfig(base_location=(13., 80.2), planning_window_minutes=window,
        enable_intermodal_transfers=enabled, boats=dict(count=1, seats=12, speed_kmh=10, handling_minutes=5),
        trucks=dict(count=1, seats=8, speed_kmh=120, handling_minutes=5, ready_after_minutes=truck_delay),
        helicopters=dict(count=0))
    roads = Roads(disconnected=disconnected)
    roads.coords['C'] = [13.05, 80.5]
    clusters = [dict(cluster_id='P', name='Wet pickup', location=roads.coords['B'], trapped_population=100)]
    shelters = [dict(shelter_id='S', name='Dry shelter', location=roads.coords['C'], status='available', remaining_capacity=capacity)]
    flood = SimpleNamespace(get_point_depth=lambda lat, lon, zones: 1 if abs(lat-13.) < .001 and abs(lon-80.21) < .002 else 0)
    return plan_rescue_fleet(fleet, clusters, shelters, roads, flood, [])


def test_boat_truck_handoff_reserves_both_vehicles_and_counts_people_once():
    result = transfer_plan()
    assert result['intermodal_served'] > 0
    assert result['provisionally_served'] == result['intermodal_served']
    assert sum(j['people'] for j in result['journeys']) == result['provisionally_served']
    assert sum(t['people'] for t in result['trips'] if t['counts_toward_served']) == result['provisionally_served']
    assert result['provisionally_served'] + result['still_needing_support'] == 100
    for journey in result['journeys']:
        assert journey['kind'] == 'boat_to_truck'
        assert journey['boat_unloaded_minutes'] <= journey['truck_loading_minutes'] < journey['completed_minutes'] <= 60
        legs = [t for t in result['trips'] if t['journey_id'] == journey['journey_id']]
        assert len(legs) == 2
        assert len({t['people'] for t in legs}) == 1
        assert journey['people'] <= 8
    for vehicle in result['vehicles']:
        legs = sorted([t for t in result['trips'] if t['vehicle_id'] == vehicle['vehicle_id']], key=lambda t: t['depart_minutes'])
        for a, b in zip(legs, legs[1:]):
            assert a['return_available_minutes'] <= b['depart_minutes']
    for point in result['transfer_points']:
        assert point['depth_m'] < .3


def test_handoffs_respect_shelter_window_partner_delay_and_road_access():
    assert transfer_plan(capacity=3)['provisionally_served'] == 3
    assert transfer_plan(window=15)['intermodal_served'] == 0
    assert transfer_plan(truck_delay=90)['intermodal_served'] == 0
    assert transfer_plan(disconnected=True)['intermodal_served'] == 0
    assert transfer_plan(enabled=False)['intermodal_served'] == 0


def test_animation_phases_follow_schedule_and_return_to_base():
    for result in [transfer_plan(), plan(config())]:
        for trip in result['trips']:
            phases = trip['phases']
            assert phases[0]['start_minutes'] == trip['depart_minutes']
            assert phases[-1]['end_minutes'] == trip['return_available_minutes']
            assert phases[0]['geometry']['coordinates'][0] == [80.2, 13.]
            assert phases[-1]['geometry']['coordinates'][-1] == [80.2, 13.]
            for phase in phases:
                assert phase['start_minutes'] <= phase['end_minutes']
            for a, b in zip(phases, phases[1:]):
                assert a['end_minutes'] == b['start_minutes']
                assert a['geometry']['coordinates'][-1] == b['geometry']['coordinates'][0]


def test_recommendations_are_grounded_in_constraints():
    timed = transfer_plan(window=15)
    recommendation = next(r for r in timed['recommendations'] if r['kind'] == 'planning_window')
    assert 15 < recommendation['suggested_window_minutes'] <= 240
    assert any(r['kind'] == 'shelter_capacity' for r in transfer_plan(capacity=3)['recommendations'])
    assert any(r['kind'] == 'enable_transfers' for r in transfer_plan(enabled=False)['recommendations'])
    empty = plan(config(count=0))
    assert any(r['kind'] == 'access' for r in empty['recommendations'])


def test_real_chennai_graph_supports_intermodal_rescue_destination(client):
    body = {'flood_zones': [{'type': 'circle', 'center': [12.9796, 80.2208], 'radius_meters': 2600}],
        'parameters': {'duration_hours': 1, 'flood_depth_meters': 2.2, 'spread_rate_meters_hr': 280, 'rainfall_intensity_mm_hr': 140},
        'rescue_fleet': {'destination_shelter_id': 'SH-01', 'planning_window_minutes': 240,
            'boats': {'count': 4, 'seats': 12, 'speed_kmh': 8, 'handling_minutes': 5},
            'trucks': {'count': 6, 'seats': 24, 'speed_kmh': 30, 'handling_minutes': 5}, 'helicopters': {'count': 0}}}
    response = client.post('/api/simulation/run', json=body)
    assert response.status_code == 200
    result = response.json()
    assert any(step['rescue_fleet_plan']['intermodal_served'] > 0 for step in result['timeline'])
    for step in result['timeline']:
        plan = step['rescue_fleet_plan']
        assert all(j['shelter_id'] == 'SH-01' for j in plan['journeys'])
        assert sum(j['people'] for j in plan['journeys']) == plan['provisionally_served']
    body['rescue_fleet']['destination_shelter_id'] = 'UNKNOWN'
    assert client.post('/api/simulation/run', json=body).status_code == 422
