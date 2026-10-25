import networkx as nx
from backend.app.services.flood_engine import (
    get_topographic_context,
    FloodSimulationEngine,
)
from backend.app.services.evacuation_solver import EvacuationSolver
from backend.app.services.supply_solver import SupplyChainSolver
from backend.app.services.road_network import RoadNetworkEngine
from unittest.mock import patch

def test_topographic_elevation_and_drainage_context():
    # Coastal point at Marina Beach should have low elevation (~2m)
    marina_elev, marina_runoff, marina_basin, dist_ch = get_topographic_context(13.0500, 80.2820)
    assert 1.0 <= marina_elev <= 5.0
    assert 0.5 <= marina_runoff <= 0.95
    assert "Marina" in marina_basin

    # St. Thomas Mount ridge should have much higher elevation (>15m)
    mount_elev, mount_runoff, mount_basin, _ = get_topographic_context(13.0020, 80.1980)
    assert mount_elev > 14.0
    assert mount_elev > marina_elev

def setup_mock_road_engine():
    from pathlib import Path
    road_engine = RoadNetworkEngine(str(Path(__file__).parents[1]/"app/data/chennai_roads.json"))
    # Override nodes and edges for testing
    road_engine.nodes_data = {
        "n1": {"id": "n1", "lat": 13.0500, "lon": 80.2820}, # Marina (elev ~2.0m)
        "n2": {"id": "n2", "lat": 13.0020, "lon": 80.1980}, # Mount (elev ~22.0m)
        "n3": {"id": "n3", "lat": 13.0158, "lon": 80.2224}  # Saidapet (elev ~4.5m)
    }
    road_engine.base_graph = nx.DiGraph()
    for nid, nd in road_engine.nodes_data.items():
        road_engine.base_graph.add_node(nid, **nd)
        road_engine.spatial_index.insert(nid, nd["lat"], nd["lon"], nd)
    
    # n1 -> n2
    road_engine.base_graph.add_edge("n1", "n2", distance_km=10.0, base_time_min=15.0, weight=15.0, capacity=8000.0, is_closed=False, water_depth_m=0.0, is_elevated=True)
    # n1 -> n3
    road_engine.base_graph.add_edge("n1", "n3", distance_km=15.0, base_time_min=20.0, weight=20.0, capacity=8000.0, is_closed=False, water_depth_m=0.0)
    # Reverse edges for multimodal undirected graph testing
    road_engine.base_graph.add_edge("n2", "n1", distance_km=10.0, base_time_min=15.0, weight=15.0, capacity=8000.0, is_closed=False, water_depth_m=0.0, is_elevated=True)

    road_engine.edges_data = {
        "e1": {"id": "e1", "source": "n1", "target": "n2", "distance_km": 10.0, "base_time_min": 15.0, "weight": 15.0, "capacity": 8000.0, "is_closed": False, "water_depth_m": 0.0, "is_elevated": True},
        "e2": {"id": "e2", "source": "n1", "target": "n3", "distance_km": 15.0, "base_time_min": 20.0, "weight": 20.0, "capacity": 8000.0, "is_closed": False, "water_depth_m": 0.0},
        "e3": {"id": "e3", "source": "n2", "target": "n1", "distance_km": 10.0, "base_time_min": 15.0, "weight": 15.0, "capacity": 8000.0, "is_closed": False, "water_depth_m": 0.0, "is_elevated": True}
    }
    return road_engine

def test_evacuation_bpr_congestion_and_urgency():
    road_engine = setup_mock_road_engine()
    flood_engine = FloodSimulationEngine()
    
    # Peak depth 1.0m, water surface 3.0m, depth 1.0m (< 1.5m elevated threshold)
    step_zones_state = [
        {
            "id": "z1", "type": "circle", "center": [13.0500, 80.2820],
            "current_radius": 2000.0, "peak_depth": 0.35, 
        }
    ]

    solver = EvacuationSolver(road_engine)
    # Cluster at n1 (flooded). Demand = 12000
    solver.population_clusters = [
        {"id": "c1", "name": "Cluster 1", "location": [13.0500, 80.2820], "estimated_population": 12000}
    ]
    # Shelter at n2 (high elevation ~22.0m, safe).
    solver.shelters = [
        {"id": "s1", "name": "Shelter 1", "location": [13.0020, 80.1980], "capacity": 20000}
    ]

    dynamic_graph = road_engine.build_dynamic_graph(step_zones_state)
    res = solver.solve_evacuation(dynamic_graph, step_zones_state, flood_engine)
    routes = res["evacuation_routes"]["features"]
    
    assert len(routes) == 1
    props = routes[0]["properties"]
    
    # BPR > 1.0 because flow exceeds capacity. With iterative updates, BPR scales up significantly.
    assert props["congested_time_min"] > props["estimated_time_min"]
    assert props["congestion_delay_factor"] > 1.0

def test_supply_multimodal_vehicle_classification():
    road_engine = setup_mock_road_engine()
    flood_engine = FloodSimulationEngine()
    
    # Flood at n3 (Saidapet ~4.5m) to 5.4m water surface -> 0.9m depth
    step_zones_state = [
        {
            "id": "z1", "type": "circle", "center": [13.0158, 80.2224],
            "current_radius": 1000.0, "peak_depth": 0.9,
        }
    ]

    road_engine.flood_engine = flood_engine
    solver = SupplyChainSolver(road_engine)

    solver.point_demands = {
        "dp1": {
            "id": "dp1", "name": "DP1", "location": [13.0020, 80.1980], "target_ward": "W1", "assigned_evacuees": 100,
            "demand": {"water_litres": 3000, "food_rations": 2000, "medical_kits": 50},
            "allocated": {"water_litres": 0, "food_rations": 0, "medical_kits": 0}, "status": "deficit"
        },
        "dp2": {
            "id": "dp2", "name": "DP2", "location": [13.0158, 80.2224], "target_ward": "W2", "assigned_evacuees": 100,
            "demand": {"water_litres": 500, "food_rations": 500, "medical_kits": 10},
            "allocated": {"water_litres": 0, "food_rations": 0, "medical_kits": 0}, "status": "deficit"
        }
    }
    solver.warehouse_stocks = {
        "w1": {
            "id": "w1", "name": "W1", "location": [13.0500, 80.2820], # Node n1
            "total": {"water_litres": 10000, "food_rations": 10000, "medical_kits": 100},
            "available": {"water_litres": 10000, "food_rations": 10000, "medical_kits": 100},
            "allocated": {"water_litres": 0, "food_rations": 0, "medical_kits": 0},
            "dispatched": {"water_litres": 0, "food_rations": 0, "medical_kits": 0}
        }
    }
    
    res = solver.solve_supply_distribution(step_zones_state)
    features = res["supply_routes"]["features"]
    assert len(features) == 2
    
    dp1_feat = next(f for f in features if f["properties"]["destination_id"] == "dp1")
    # DP1 is at n2 (safe). Reached by truck from w1 (n1).
    assert dp1_feat["properties"]["vehicle_type"] == "Heavy All-Terrain Truck (6x6)" or dp1_feat["properties"]["vehicle_type"] == "Rapid Logistics Utility Van"
    
    dp2_feat = next(f for f in features if f["properties"]["destination_id"] == "dp2")
    # DP2 is at n3 (1.0m flooded). Reached by Amphibious Rescue Boat because 1.0m is passable for boat but impassable for truck.
    assert dp2_feat["properties"]["vehicle_type"] == "Amphibious Rescue Boat"
