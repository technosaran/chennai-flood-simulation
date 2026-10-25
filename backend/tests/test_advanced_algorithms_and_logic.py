"""
Unit and integration tests for advanced mathematical algorithms and scientific models:
1. Computational Geometry: Douglas-Peucker simplification, Monotone Chain convex hull, Shoelace area, Centroid
2. Graph Theory: A* with Haversine admissible heuristic, BPR volume delay, Tarjan bridges, Island components
3. Hydrology & Hydraulics: SCS Curve Number runoff, Manning velocity, Defra flood hazard rating
4. Logistics & Operations Research: Sphere standard relief calculation, hydrodynamic vehicle stability
5. Decision Analysis: TOPSIS Multi-Criteria Decision Analysis (MCDA)
"""
import pytest
import math
import networkx as nx

from backend.app.services.geometry import (
    simplify_polyline_douglas_peucker,
    compute_convex_hull,
    polygon_area_sq_meters,
    polygon_centroid,
    haversine,
)
from backend.app.services.road_network import RoadNetworkEngine
from backend.app.services.flood_engine import FloodSimulationEngine
from backend.app.services.supply_solver import SupplyChainSolver
from backend.app.services.ai_advisor import AIAdvisorService


def test_douglas_peucker_simplification():
    # Straight line with intermediate collinear and near-collinear points
    coords = [[13.0, 80.0], [13.01, 80.0001], [13.02, 80.0], [13.03, 80.0]]
    simplified = simplify_polyline_douglas_peucker(coords, tolerance_meters=50.0)
    assert len(simplified) < len(coords)
    assert simplified[0] == coords[0]
    assert simplified[-1] == coords[-1]

    # Preserves endpoints for 2 points
    pair = [[13.0, 80.0], [13.1, 80.1]]
    assert simplify_polyline_douglas_peucker(pair, tolerance_meters=10.0) == pair


def test_convex_hull_monotone_chain():
    # Square with an interior point
    pts = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0), (0.5, 0.5)]
    hull = compute_convex_hull(pts)
    assert len(hull) == 4
    assert (0.5, 0.5) not in hull
    for corner in [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]:
        assert corner in hull


def test_shoelace_polygon_area_and_centroid():
    # Approximate ~1km x 1km square around Chennai
    # 0.009 deg lat ~= 1000m, 0.009 deg lon ~= 1000m * cos(13 deg) ~= 976m
    square = [
        [13.00, 80.00],
        [13.00, 80.01],
        [13.01, 80.01],
        [13.01, 80.00],
    ]
    area_sq_m = polygon_area_sq_meters(square)
    assert 500000.0 < area_sq_m < 2000000.0

    cx, cy = polygon_centroid(square)
    assert math.isclose(cx, 13.005, abs_tol=0.002)
    assert math.isclose(cy, 80.005, abs_tol=0.002)


def test_astar_pathfinding(road_engine):
    # Verify A* returns exact shortest path between Chennai Central and Guindy
    source = "N_CENTRAL"
    target = "N_GUINDY_RACE"
    dynamic_graph = road_engine.base_graph

    astar_route = road_engine.find_astar_path(dynamic_graph, source, target)
    dijkstra_route = nx.shortest_path(dynamic_graph, source, target, weight="weight")

    assert astar_route is not None
    assert astar_route[0] == source
    assert astar_route[-1] == target
    assert astar_route == dijkstra_route


def test_bpr_traffic_delay_formula():
    base_time = 10.0
    # Zero flow: no congestion
    t_zero = RoadNetworkEngine.compute_bpr_travel_time(base_time, flow=0.0, capacity=8000.0)
    assert t_zero == 10.0

    # Flow equal to capacity: t = 10 * (1 + 0.15 * 1^4) = 11.5
    t_cap = RoadNetworkEngine.compute_bpr_travel_time(base_time, flow=8000.0, capacity=8000.0)
    assert math.isclose(t_cap, 11.5, rel_tol=1e-3)

    # Over-capacity flow (16,000 evacuees): congestion delay increases significantly
    t_high = RoadNetworkEngine.compute_bpr_travel_time(base_time, flow=16000.0, capacity=8000.0)
    assert t_high > 11.5


def test_critical_bridges_and_isolated_components(road_engine):
    bridges = road_engine.find_critical_bridges()
    assert isinstance(bridges, list)

    # Disconnect road network into components by cutting off Kathipara junction
    test_graph = road_engine.base_graph.copy()
    if test_graph.has_node("N_KATHIPARA"):
        test_graph.remove_node("N_KATHIPARA")
    components = road_engine.detect_isolated_components(test_graph)
    assert len(components) >= 1


def test_scs_curve_number_runoff():
    # Below initial abstraction: zero runoff
    assert FloodSimulationEngine.compute_scs_curve_number_runoff(rainfall_mm=5.0, curve_number=80.0) == 0.0

    # High rainfall (100mm) on urban impervious surface (CN=90)
    runoff = FloodSimulationEngine.compute_scs_curve_number_runoff(rainfall_mm=100.0, curve_number=90.0)
    assert runoff > 60.0  # Urban areas generate over 60mm of surface runoff


def test_mannings_velocity_and_hazard_rating():
    # Shallow water 0.1m, mild slope 0.001
    v_shallow = FloodSimulationEngine.compute_mannings_flow_velocity(depth_m=0.1, slope_m_per_m=0.001)
    assert 0.05 <= v_shallow <= 1.0

    # Deep water 1.5m flow velocity should be higher
    v_deep = FloodSimulationEngine.compute_mannings_flow_velocity(depth_m=1.5, slope_m_per_m=0.005)
    assert v_deep > v_shallow

    # Hazard rating classification
    hr_safe, cat_safe = FloodSimulationEngine.compute_hazard_rating(depth_m=0.01, velocity_m_s=0.1)
    assert cat_safe == "safe"

    hr_extreme, cat_extreme = FloodSimulationEngine.compute_hazard_rating(depth_m=1.8, velocity_m_s=1.5)
    assert cat_extreme == "extreme"
    assert hr_extreme >= 2.0


def test_sphere_standards_relief_calculator():
    needs = SupplyChainSolver.compute_sphere_standard_relief_needs(population=500, duration_days=2, severity="moderate")
    assert needs["water_litres"] >= 500 * 3 * 2
    assert needs["food_rations"] == 500 * 3 * 2
    assert needs["medical_kits"] >= 10
    assert needs["hygiene_family_kits"] == 100


def test_vehicle_hydrodynamic_traversability():
    # Low water (0.1m): van and truck safe
    res_shallow = SupplyChainSolver.evaluate_vehicle_traversability(water_depth_m=0.10, flow_velocity_m_s=0.2)
    assert res_shallow["passable"] is True
    assert "Van" in res_shallow["recommended_vehicle"] or "Truck" in res_shallow["recommended_vehicle"]

    # High water (0.8m): truck impassable, amphibious boat required
    res_deep = SupplyChainSolver.evaluate_vehicle_traversability(water_depth_m=0.80, flow_velocity_m_s=0.5)
    assert res_deep["passable"] is False
    assert res_deep["recommended_vehicle"] == "Amphibious Rescue Boat"


def test_topsis_mcda_rankings():
    # Alternative 1: Deep flood, high density, low elevation (very high hazard)
    # Alternative 2: Shallow flood, low density, high elevation (low hazard)
    matrix = [
        [2.5, 1.8, 30000.0, 0.90, 2.0],
        [0.1, 0.05, 5000.0, 0.40, 25.0],
    ]
    weights = [0.35, 0.20, 0.20, 0.15, 0.10]
    is_benefit = [True, True, True, True, False]

    scores = AIAdvisorService.compute_topsis_scores(matrix, weights, is_benefit)
    assert len(scores) == 2
    # Alternative 1 should have much higher TOPSIS closeness to worst-case flood disaster
    assert scores[0] > scores[1]
    assert 0.0 <= scores[0] <= 1.0
    assert 0.0 <= scores[1] <= 1.0
