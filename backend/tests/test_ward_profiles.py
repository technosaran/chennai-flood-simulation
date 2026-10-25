import hashlib
import json
from pathlib import Path
from backend.app.services.ward_profiles import profiles, contains, DATA


def test_all_official_wards_and_modeled_population_provenance():
    result = profiles()
    assert {int(w['ward_id']) for w in result['wards']} == set(range(1, 201))
    clusters = json.loads((DATA / 'population_clusters.json').read_text())
    ids = [c['id'] for w in result['wards'] for c in w['modeled_clusters']]
    outside = [c['id'] for c in result['outside_gcc_clusters']]
    assert len(ids) == len(set(ids))
    assert set(ids + outside) == {c['id'] for c in clusters}
    for ward in result['wards']:
        assert ward['official_population'] is None
        assert ward['vulnerable_group_counts'] is None
        assert ward['modeled_population'] == (sum(c['estimated_population'] for c in ward['modeled_clusters']) if ward['modeled_clusters'] else None)
        assert len(ward['nearby_shelters']) == 3
        assert [s['straight_line_km'] for s in ward['nearby_shelters']] == sorted(s['straight_line_km'] for s in ward['nearby_shelters'])


def test_holes_and_disjoint_polygons_do_not_assign_the_wrong_ward():
    outer = [[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]]
    hole = [[4, 4], [6, 4], [6, 6], [4, 6], [4, 4]]
    geometry = {'type': 'Polygon', 'coordinates': [outer, hole]}
    assert contains(geometry, [2, 2])
    assert not contains(geometry, [5, 5])
    assert not contains(geometry, [20, 20])
    assert contains({'type': 'MultiPolygon', 'coordinates': [[outer, hole]]}, [2, 2])


def test_reference_layers_are_bundled_with_matching_fingerprints():
    public = DATA.parents[2] / 'frontend/public/data'
    manifest = json.loads((public / 'reference_manifest.json').read_text())
    for name, digest in manifest['files'].items():
        assert hashlib.sha256((public / name).read_bytes()).hexdigest() == digest
        assert json.loads((public / name).read_text())['features']
    assert json.loads((public / 'ward_profiles.json').read_text()) == profiles()


def test_ward_api(client):
    response = client.get('/api/wards')
    assert response.status_code == 200
    assert len(response.json()['wards']) == 200
