"""Reproducible engine benchmark; run from the repository root."""
import json
import time
from types import SimpleNamespace
from backend.app.api.simulation import _run_simulation
from backend.app.models.disaster import SimulationRequest
from backend.app.services.road_network import RoadNetworkEngine
from backend.app.services.evacuation_solver import EvacuationSolver
from backend.app.services.supply_solver import SupplyChainSolver
from backend.app.services.demand_predictor import DemandPredictor


def benchmark():
    road = RoadNetworkEngine()
    state = SimpleNamespace(road_engine=road, flood_engine=road.flood_engine,
                            evac_solver=EvacuationSolver(road),
                            supply_solver=SupplyChainSolver(road, ml_predictor=DemandPredictor()))
    request = SimpleNamespace(app=SimpleNamespace(state=state))
    cases = {}
    for name, zone in {
        "circle_12h": {"type": "circle", "center": [12.9796, 80.2185], "radius_meters": 2500},
        "polygon_12h": {"type": "polygon", "coordinates": [[12.95, 80.20], [13.02, 80.20], [13.02, 80.25], [12.95, 80.25]]},
    }.items():
        req = SimulationRequest(flood_zones=[zone], parameters={"duration_hours": 12, "flood_depth_meters": 2.0})
        timings = []
        for _ in range(3):
            start = time.perf_counter()
            result = _run_simulation(req, request)
            timings.append(round(time.perf_counter() - start, 4))
        cases[name] = {"seconds": timings, "steps": len(result["timeline"])}
    return cases


if __name__ == "__main__":
    print(json.dumps(benchmark(), indent=2))
