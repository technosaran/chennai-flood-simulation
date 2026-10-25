from types import SimpleNamespace
from backend.app.models.disaster import RescueFleetConfig
from backend.app.services.rescue_continuity import ContinuousRescuePlanner
from backend.tests.test_rescue_fleet import Roads


def setup(speed=120, capacity=100):
    fleet=RescueFleetConfig(continue_across_hours=True, planning_window_minutes=240, base_location=(13.,80.2),
        trucks={'count':0},boats={'count':0},helicopters={'count':1,'seats':10,'speed_kmh':speed,'handling_minutes':5})
    state=ContinuousRescuePlanner(fleet)
    flood=SimpleNamespace(get_point_depth=lambda lat,lon,zones:1 if abs(lon-80.21)<.0001 else 0)
    return state,flood,capacity


def step(state,flood,capacity,minute,next_minute):
    committed,reserved,arrived=state.reservations(minute)
    clusters=[dict(cluster_id='P',name='Pickup',location=[13.,80.21],trapped_population=max(0,100-committed.get('P',0)))]
    shelters=[dict(shelter_id='S',name='Shelter',location=[13.,80.22],status='available',remaining_capacity=capacity-reserved.get('S',0))]
    return state.plan(minute,next_minute,clusters,shelters,Roads(),flood,[])


def test_long_trip_continues_without_teleporting_or_double_booking():
    state,flood,capacity=setup(speed=1)
    first=step(state,flood,capacity,0,60)
    second=step(state,flood,capacity,60,120)
    assert first['new_vehicle_trips']==1
    assert first['cumulative_rescued']==0
    assert second['new_vehicle_trips']==0
    assert second['committed_not_arrived']==10
    assert second['vehicles'][0]['location']!=[13.,80.2]
    assert second['vehicles'][0]['activity_at_snapshot']=='travelling_to_pickup'
    assert second['trips'][0]==first['trips'][0]
    assert second['vehicles'][0]['allocation_reason']=='continuing_previous_trip'
    assert second['snapshot_demand']==90


def test_people_shelter_slots_and_completion_are_carried_once():
    state,flood,capacity=setup(capacity=13)
    first=step(state,flood,capacity,0,60)
    second=step(state,flood,capacity,60,120)
    final=step(state,flood,capacity,120,120)
    assert first['cumulative_committed']==13
    assert second['cumulative_rescued']==13
    assert second['newly_completed_people']==13
    assert final['newly_completed_people']==0
    assert final['cumulative_rescued']==13
    assert final['new_vehicle_trips']==0
    committed,reserved,arrived=state.reservations(120)
    assert committed=={'P':13}
    assert reserved==arrived=={'S':13}
    assert final['still_needing_support']==87


def test_global_journey_ids_and_vehicle_intervals_remain_unique():
    state,flood,capacity=setup()
    snapshots=[step(state,flood,capacity,t,t+60) for t in (0,60,120)]
    final=step(state,flood,capacity,180,180)
    assert final['cumulative_rescued']==100
    assert final['cumulative_committed']==100
    assert final['still_needing_support']==0
    journeys=final['journeys']
    assert len({j['journey_id'] for j in journeys})==len(journeys)
    assert sum(j['people'] for j in journeys)==100
    trips=sorted(final['trips'],key=lambda t:t['depart_minutes'])
    for before,after in zip(trips,trips[1:]):
        assert before['return_available_minutes']<=after['depart_minutes']+1e-6
    for snapshot in snapshots:
        for trip in snapshot['trips']:
            assert trip['depart_minutes']<snapshot['decision_end_minutes']
    # Earlier API snapshots must not change when state gains later jobs.
    assert len(snapshots[0]['trips'])<len(final['trips'])


def test_continuous_api_preserves_capacity_and_deducts_prior_rescues(client):
    body={'flood_zones':[{'type':'circle','center':[12.9796,80.2208],'radius_meters':2600}],
        'parameters':{'duration_hours':4,'flood_depth_meters':2.2,'spread_rate_meters_hr':280,'rainfall_intensity_mm_hr':140},
        'rescue_fleet':{'continue_across_hours':True,'destination_shelter_id':'SH-01','planning_window_minutes':240,
            'boats':{'count':4,'seats':12,'speed_kmh':8,'handling_minutes':5},
            'trucks':{'count':6,'seats':24,'speed_kmh':30,'handling_minutes':5},'helicopters':{'count':0}}}
    response=client.post('/api/simulation/run',json=body)
    assert response.status_code==200,response.text
    plans=[s['rescue_fleet_plan'] for s in response.json()['timeline']]
    assert plans[-1]['cumulative_rescued']>0
    assert all(b['cumulative_rescued']>=a['cumulative_rescued'] for a,b in zip(plans,plans[1:]))
    assert plans[-1]['new_vehicle_trips']==0
    for snapshot in response.json()['timeline']:
        plan=snapshot['rescue_fleet_plan']
        assert snapshot['metrics']['unassigned_stranded_population']==plan['still_needing_support']
        for shelter in snapshot['shelter_allocations']:
            assert shelter['total_occupancy']+shelter['remaining_capacity']+shelter['rescue_pending_reservations']==shelter['total_capacity']
        assert sum(j['people'] for j in plan['journeys'])==plan['cumulative_committed']
    all_trips=plans[-1]['trips']
    for vid in {t['vehicle_id'] for t in all_trips}:
        trips=sorted([t for t in all_trips if t['vehicle_id']==vid],key=lambda t:t['depart_minutes'])
        for before,after in zip(trips,trips[1:]):
            assert before['return_available_minutes']<=after['depart_minutes']+1e-6


def test_continuous_schedule_survives_saved_snapshot_roundtrip(client,tmp_path,monkeypatch):
    from backend.app.main import app
    from backend.app.services.simulation_archive import SimulationArchive
    monkeypatch.setattr(app.state,'simulation_archive',SimulationArchive(tmp_path/'saved.sqlite3'))
    response=client.post('/api/simulation/run',json={
        'flood_zones':[{'type':'circle','center':[12.9796,80.2185],'radius_meters':700}],
        'parameters':{'duration_hours':3,'flood_depth_meters':2,'rainfall_intensity_mm_hr':90},
        'rescue_fleet':{'continue_across_hours':True,'planning_window_minutes':240,'trucks':{'count':0},'boats':{'count':0},'helicopters':{'count':1,'speed_kmh':120}}})
    assert response.status_code==200
    result=response.json()
    saved=client.post('/api/simulations/saved',json={'simulation_id':result['simulation_id'],'name':'Continuing rescue'})
    assert saved.status_code==200
    snapshot=client.get('/api/simulations/saved/'+saved.json()['id']).json()
    assert snapshot['result']['timeline'][-1]['rescue_fleet_plan']['mode']=='continuous'
    imported=client.post('/api/simulations/saved/import',json=snapshot)
    assert imported.status_code==200,imported.text
    restored=client.get('/api/simulations/saved/'+imported.json()['id']).json()
    assert restored['result']['timeline']==result['timeline']
