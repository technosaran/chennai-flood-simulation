import math
import pytest
from backend.app.models.disaster import DisasterParameters, FloodZoneInput
from backend.app.services.demand_predictor import DemandPredictor, ITEMS


def test_polygon_does_not_flood_its_circumscribed_circle(flood_engine):
    state = [{"type": "polygon", "center": [13.0, 80.2], "current_radius": 5000,
              "peak_depth": 2.0, "polygon_latlon": [[13.0, 80.2], [13.02, 80.2], [13.0, 80.22]]}]
    assert flood_engine.get_point_depth(13.015, 80.215, state) == 0
    assert flood_engine.get_edge_depth(13.015, 80.215, 13.02, 80.22, state) == 0
    assert flood_engine.get_point_depth(13.005, 80.205, state) == 2


def test_timeline_reaches_duration_and_polygon_overlay_matches_depth(flood_engine):
    zone = FloodZoneInput(type="polygon", coordinates=[[13.0, 80.2], [13.02, 80.2], [13.0, 80.22]])
    timeline = flood_engine.compute_timeline([zone], DisasterParameters(duration_hours=1, time_step_hours=0.75, flood_depth_meters=2))
    assert [s["time_elapsed_hours"] for s in timeline] == [0, 0.75, 1]
    for step in timeline:
        feature = step["flood_polygons"]["features"][0]
        assert feature["properties"]["depth_meters"] == round(step["zones_state"][0]["peak_depth"], 2)
        assert feature["geometry"]["coordinates"][0] == [[lon, lat] for lat, lon in step["zones_state"][0]["polygon_latlon"]]


def test_zero_depth_has_no_flood_overlay(flood_engine):
    zone = FloodZoneInput(type="circle", center=[13, 80.2], radius_meters=1000)
    result = flood_engine.compute_timeline([zone], DisasterParameters(flood_depth_meters=0))
    assert all(not s["flood_polygons"]["features"] for s in result)


@pytest.mark.parametrize("pop", [0, 1, 2000, 100000])
def test_portable_demand_has_floors_intervals_and_scales_with_population(pop):
    model = DemandPredictor()
    assert model.is_loaded
    result = model.predict_demand(140, 1.2, 24000, 0.85, pop)
    for item, floor in zip(ITEMS, [3, 3, .02]):
        assert result[item] >= math.ceil(pop * floor)
        bounds = result["prediction_intervals"][item]
        assert 0 <= bounds["lower"] <= result[item] <= bounds["upper"]
    assert model.metadata()["training_data"] == "synthetic"


def test_ml_out_of_domain_and_missing_artifact_fallback(tmp_path):
    assert DemandPredictor(tmp_path / "missing.json").predict_demand(90, 1, 20000, .8, 100) is None
    model = DemandPredictor()
    assert model.predict_demand(90, 20, 20000, .8, 100) is None
    assert model.predict_demand(float("nan"), 1, 20000, .8, 100) is None


def test_graph_depth_cache_invalidates_when_zones_change(road_engine):
    dry = road_engine.build_dynamic_graph([])
    zone = {"type": "circle", "center": [12.9796, 80.2185], "current_radius": 10000, "peak_depth": 6}
    wet = road_engine.build_dynamic_graph([zone])
    assert wet.number_of_edges() < dry.number_of_edges()
    assert road_engine.build_dynamic_graph([]).number_of_edges() == dry.number_of_edges()


def test_simulation_exports_model_provenance_and_timing(client):
    response = client.post('/api/simulation/run', json={"flood_zones": [], "parameters": {}})
    data = response.json()
    assert response.status_code == 200
    assert data["status"] == "completed"
    assert data["diagnostics"]["compute_time_ms"] > 0
    assert data["diagnostics"]["demand_model"]["training_data"] == "synthetic"
    assert data["timeline"][-1]["hour"] == 6


def test_unknown_preset_is_rejected(client):
    result = client.post('/api/simulation/run', json={"flood_zones": [{"type": "preset", "preset_key": "unknown"}]})
    assert result.status_code == 422


def test_failed_run_preserves_previous_inventory(client, monkeypatch):
    from backend.app.main import app
    client.post('/api/simulation/run', json={"flood_zones": [], "parameters": {}})
    before = client.get('/api/resources/state').json()
    previous_id = app.state.latest_simulation["simulation_id"]
    def fail(*args, **kwargs):
        raise RuntimeError("Injected solver failure")
    monkeypatch.setattr(app.state.supply_solver, "solve_supply_distribution", fail)
    with pytest.raises(RuntimeError, match="Injected solver failure"):
        client.post('/api/simulation/run', json={"flood_zones": [], "parameters": {}})
    assert client.get('/api/resources/state').json() == before
    assert app.state.latest_simulation["simulation_id"] == previous_id
