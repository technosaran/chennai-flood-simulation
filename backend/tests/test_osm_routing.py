"""Street topology regressions independent of the legacy named-junction fixture."""
import json
from pathlib import Path
import pytest
from backend.app.data.import_osm_roads import compile_network, distance
from backend.app.services.road_network import RoadNetworkEngine


def way(wid, ids, coords, **tags):
    return {'type':'way','id':wid,'nodes':ids,
            'geometry':[{'lat':a,'lon':b} for a,b in coords],
            'tags':{'highway':'residential',**tags}}


def engine(tmp_path, ways):
    graph=compile_network({'elements':ways,'osm3s':{'timestamp_osm_base':'2026-07-24T11:04:51Z'}})
    path=tmp_path/'roads.json';path.write_text(json.dumps(graph))
    return RoadNetworkEngine(str(path))


def test_curves_and_mode_specific_oneway(tmp_path):
    points=[[13,80.2],[13.001,80.201],[13,80.202]]
    r=engine(tmp_path,[way(1,[1,2,3],points,oneway='yes')])
    truck=r.build_dynamic_graph([],mode='truck')
    assert truck.has_edge('OSM-1','OSM-3')
    assert not truck.has_edge('OSM-3','OSM-1')
    assert r.get_severed_roads_count(truck)==0
    assert r.get_route_coordinates(['OSM-1','OSM-3'],truck)==points
    walking=r.build_dynamic_graph([],mode='foot')
    assert walking.has_edge('OSM-3','OSM-1')
    km, minutes=r.get_route_metrics(walking,['OSM-1','OSM-3'])
    assert minutes==pytest.approx(sum(distance(a,b) for a,b in zip(points,points[1:]))/5*60,abs=.05)
    assert r.find_nearest_node(13.1,80.2) is None


def test_flood_checks_bend_instead_of_endpoint_chord(tmp_path):
    r=engine(tmp_path,[way(1,[1,2,3],[[13,80.2],[13.002,80.201],[13,80.202]])])
    zone={'type':'circle','center':[13.002,80.201],'current_radius':40,'peak_depth':1.2}
    graph=r.build_dynamic_graph([zone],mode='truck')
    assert not graph.has_edge('OSM-1','OSM-3')
    assert r.get_severed_roads_count(graph)==2
    dry=r.build_dynamic_graph([],mode='truck')
    assert dry.has_edge('OSM-1','OSM-3')


def test_parallel_ways_access_and_grade_separation(tmp_path):
    r=engine(tmp_path,[
        way(1,[1,2],[[13,80.2],[13,80.202]]),
        way(2,[1,3,2],[[13,80.2],[13.001,80.201],[13,80.202]],highway='footway'),
        way(3,[4,5],[[12.999,80.201],[13.002,80.201]],bridge='yes'),
        way(4,[6,7],[[13,80.203],[13,80.204]],access='private'),
    ])
    graph=r.build_dynamic_graph([],mode='truck')
    assert len(graph['OSM-1']['OSM-2']['geometry'])==2
    assert 'OSM-6' not in graph
    assert r.find_astar_path(graph,'OSM-1','OSM-4') is None
    assert graph['OSM-4']['OSM-5']['is_elevated'] is False


def test_bundled_snapshot_has_real_curves_and_reachable_city_route(monkeypatch):
    monkeypatch.setenv("USE_OSM_ROADS", "1")
    r=RoadNetworkEngine()
    assert r.metadata['node_count']>10000
    assert r.metadata['license']=='ODbL'
    graph=r.build_dynamic_graph([],mode='truck')
    start=r.find_nearest_node(13.0827,80.2707,mode='truck')
    end=r.find_nearest_node(13.007,80.205,mode='truck')
    path=r.find_astar_path(graph,start,end)
    assert path
    coords=r.get_route_coordinates(path,graph)
    assert len(coords)>len(path)
    geometry_length=sum(distance(a,b) for a,b in zip(coords,coords[1:]))
    km,_=r.get_route_metrics(graph,path)
    assert km==pytest.approx(geometry_length,abs=.01)
    assert km>distance(coords[0],coords[-1])
