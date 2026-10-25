import json
from pathlib import Path
from types import SimpleNamespace
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.api.evaluation import load_verified_report
from backend.app.services.ai_advisor import AIAdvisorService


def run_dry(client):
    response = client.post('/api/simulation/run', json={
        'flood_zones': [], 'parameters': {'rainfall_intensity_mm_hr': 0,
        'flood_depth_meters': 0, 'spread_rate_meters_hr': 0, 'duration_hours': 1}})
    assert response.status_code == 200, response.text
    return response.json()


def test_no_advice_before_completed_run():
    with TestClient(app) as client:
        # app state may have been populated by another lifespan in this process.
        old = getattr(app.state, 'latest_simulation', None)
        app.state.latest_simulation = None
        try:
            assert client.get('/api/advisory').status_code == 409
        finally:
            app.state.latest_simulation = old


def test_dry_advice_and_consistent_subviews(client):
    result = run_dry(client)
    sim_id = result['simulation_id']
    advice = client.get('/api/advisory', params={'simulation_id': sim_id}).json()
    assert advice['summary']['overall_severity'] == 'None'
    assert advice['snapshot_hour'] == result['timeline'][-1]['hour']
    text = advice['bilingual_emergency_broadcasts']['siren_broadcast_english']
    assert 'SIMULATION ONLY' in text
    assert 'EMERGENCY FLOOD WARNING' not in text
    for path, key, source in [('wards', 'ward_rankings', 'ward_vulnerability_index'),
                              ('airlift', 'optimal_airlift_drop_zones', 'optimal_airlift_drop_zones'),
                              ('broadcast', 'emergency_broadcasts', 'bilingual_emergency_broadcasts')]:
        subview = client.get('/api/advisory/' + path, params={'simulation_id': sim_id}).json()
        assert subview[key] == advice[source]
        assert subview['simulation_id'] == sim_id
    for suffix in ['', '/wards', '/airlift', '/broadcast']:
        assert client.get('/api/advisory' + suffix, params={'simulation_id': 'replaced'}).status_code == 409


def test_airlift_rejects_all_flooded_sites():
    advisor = AIAdvisorService()
    engine = SimpleNamespace(get_point_depth=lambda *args: 2.0)
    routes = advisor.compute_optimal_airlift_drop_zones(
        [{'cluster_id': 'test', 'name': 'Test', 'location': [13, 80.2], 'trapped_population': 500}], [], engine)
    assert len(routes) == 1
    assert routes[0]['status'] == 'no_safe_drop_zone'
    assert routes[0]['drop_zone_coordinates'] is None


def test_evaluation_endpoint_exposes_verified_deployed_metrics(client):
    result = client.get('/api/model/evaluation').json()
    assert result['evaluation_status'] == 'verified'
    assert result['evaluation']['rows'] >= 16513
    assert result['evaluation']['tree_count'] == result['model']['tree_count']
    assert result['model']['training_data'] == 'synthetic'


def test_evaluation_rejects_changed_artifacts(tmp_path):
    assert load_verified_report(tmp_path) is None
    root = Path(__file__).parents[1] / 'ml_pipeline'
    report = json.loads((root / 'models/runtime_evaluation.json').read_text())
    (tmp_path / 'models').mkdir()
    (tmp_path / 'models/runtime_evaluation.json').write_text(json.dumps(report))
    (tmp_path / 'models/demand_forest.json').write_text('{}')
    assert load_verified_report(tmp_path) is None
