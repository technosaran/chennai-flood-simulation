import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.services.road_network import RoadNetworkEngine
from backend.app.services.flood_engine import FloodSimulationEngine
from backend.app.services.evacuation_solver import EvacuationSolver
from backend.app.services.supply_solver import SupplyChainSolver


@pytest.fixture(scope="session")
def client():
    """Session-scoped TestClient with active lifespan."""
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="session")
def road_engine():
    from pathlib import Path
    return RoadNetworkEngine(str(Path(__file__).parents[1]/"app/data/chennai_roads.json"))


@pytest.fixture(scope="session")
def flood_engine():
    return FloodSimulationEngine()


@pytest.fixture(scope="session")
def evac_solver(road_engine):
    return EvacuationSolver(road_engine)


@pytest.fixture(scope="session")
def supply_solver(road_engine):
    return SupplyChainSolver(road_engine)
