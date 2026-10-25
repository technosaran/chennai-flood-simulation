"""
Tests for Chennai Reservoir Hydrology Engine and IEEE MCDM TOPSIS Decision Support.
"""

import pytest
from backend.app.services.reservoir_engine import (
    ChennaiReservoirEngine,
    RESERVOIR_SPECS,
)
from backend.app.services.ai_advisor import AIAdvisorService
from backend.app.services.flood_engine import FloodSimulationEngine
from backend.app.services.road_network import RoadNetworkEngine


def test_reservoir_specs_and_initialization():
    engine = ChennaiReservoirEngine()
    summary = engine.get_all_reservoirs_summary()

    assert summary["total_capacity_mcft"] == pytest.approx(11257.0, rel=1e-2)
    assert len(summary["reservoirs"]) == 4

    chem = next(r for r in summary["reservoirs"] if r["id"] == "chembarambakkam")
    assert chem["capacity_mcft"] == 3645.0
    assert chem["full_tank_level_ft"] == 85.40
    assert "Adyar River" in chem["primary_river"]
    assert chem["storage_pct"] > 70.0


def test_rational_inflow_calculation():
    engine = ChennaiReservoirEngine()
    # 50 mm/hr cloudburst
    chem_inflow = engine.calculate_inflow_cusecs("chembarambakkam", rainfall_rate_mm_hr=50.0)
    poondi_inflow = engine.calculate_inflow_cusecs("poondi", rainfall_rate_mm_hr=50.0)

    # Poondi has much larger catchment (2072 sq km vs 358 sq km)
    assert poondi_inflow > chem_inflow
    assert chem_inflow > 1000.0
    assert poondi_inflow > 5000.0


def test_wrd_dam_safety_gate_rules():
    engine = ChennaiReservoirEngine()
    # Low storage scenario (50% capacity) -> base release
    low_gate = engine.compute_gate_discharge("chembarambakkam", current_storage_mcft=1800.0, inflow_cusecs=2000.0)
    assert low_gate["alert_level"] == "NORMAL"
    assert low_gate["discharge_cusecs"] <= 150.0

    # Critical surcharge scenario (>95% capacity) -> emergency release
    crit_gate = engine.compute_gate_discharge("chembarambakkam", current_storage_mcft=3550.0, inflow_cusecs=12000.0)
    assert crit_gate["alert_level"] == "CRITICAL_DISCHARGE"
    assert crit_gate["discharge_cusecs"] > 10000.0
    assert crit_gate["gates_open"] == RESERVOIR_SPECS["chembarambakkam"]["sluice_gates_count"]


def test_multi_hour_reservoir_simulation():
    engine = ChennaiReservoirEngine()
    step_res = engine.step_simulation(rainfall_mm_hr=80.0, step_hours=3.0)

    assert step_res["rainfall_intensity_mm_hr"] == 80.0
    assert "river_surge_summary" in step_res
    adyar = step_res["river_surge_summary"]["adyar_river"]
    assert adyar["governing_reservoir"] == "Chembarambakkam"
    assert "projected_stage_surge_m" in adyar


def test_mcdm_topsis_rankings():
    advisor = AIAdvisorService()
    flood_engine = FloodSimulationEngine()

    # Simulate flood scenario where Zone 13 (Adyar/Kotturpuram) is severely inundated
    mock_step_zones = [
        {
            "id": "FZ-01",
            "type": "circle",
            "center": [13.0158, 80.2224],  # Zone 13
            "current_radius": 2500.0,
            "peak_depth": 2.2,
        }
    ]

    ward_rankings = advisor.compute_ward_vulnerability_index(mock_step_zones, flood_engine)
    casualty_data = {"total_stranded_citizens": 15000, "high_risk_chokepoints": []}
    isolated_clusters = [{"id": "c1", "name": "Saidapet Lowlands", "location": [13.0158, 80.2224]}]

    topsis = advisor.compute_mcdm_topsis_rankings(ward_rankings, casualty_data, isolated_clusters)

    assert topsis["methodology"] == "IEEE TOPSIS (Technique for Order Preference by Similarity to Ideal Solution)"
    assert topsis["total_ranked_zones"] == 15
    assert len(topsis["rankings"]) == 15

    # Check top ranked zone
    top_zone = topsis["rankings"][0]
    assert top_zone["dispatch_rank"] == 1
    assert 0.0 <= top_zone["topsis_score"] <= 1.0
    assert top_zone["priority_tier"] in ["P1_IMMEDIATE_DISPATCH", "P2_HIGH_PRIORITY"]

    # Verify scores are sorted in descending order
    scores = [z["topsis_score"] for z in topsis["rankings"]]
    assert scores == sorted(scores, reverse=True)


def test_reservoirs_api_routes(client):
    # 1. GET /api/reservoirs
    res = client.get("/api/reservoirs")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert "reservoirs" in data["data"]

    # 2. POST /api/reservoirs/simulate
    sim_payload = {
        "rainfall_intensity_mm_hr": 70.0,
        "duration_hours": 4,
    }
    sim_res = client.post("/api/reservoirs/simulate", json=sim_payload)
    assert sim_res.status_code == 200
    sim_data = sim_res.json()
    assert sim_data["status"] == "success"
    assert len(sim_data["timeline"]) == 4

    # 3. GET /api/reservoirs/historical
    hist_res = client.get("/api/reservoirs/historical")
    assert hist_res.status_code == 200
    hist_data = hist_res.json()
    assert len(hist_data["benchmarks"]) >= 3
    assert any("2015" in b["event_name"] for b in hist_data["benchmarks"])
