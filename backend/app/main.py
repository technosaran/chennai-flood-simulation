from contextlib import asynccontextmanager
import os
from threading import RLock
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api import api_router
from backend.app.services.road_network import RoadNetworkEngine
from backend.app.services.flood_engine import FloodSimulationEngine
from backend.app.services.evacuation_solver import EvacuationSolver
from backend.app.services.supply_solver import SupplyChainSolver
from backend.app.services.ai_advisor import AIAdvisorService


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize singleton simulation engines
    road_engine = RoadNetworkEngine()
    flood_engine = FloodSimulationEngine()
    evac_solver = EvacuationSolver(road_engine)
    
    # Initialize ML Predictor with graceful fallback
    from backend.app.services.demand_predictor import DemandPredictor
    ml_predictor = DemandPredictor()
    if os.environ.get("ENABLE_ML", "0") == "1":
        try:
            from backend.app.services.ml_predictor import MLPredictor
            legacy_predictor = MLPredictor()
            if legacy_predictor.is_loaded:
                ml_predictor = legacy_predictor
        except Exception as e:
            print(f"ML Predictor fallback initialized: {e}")
    
    supply_solver = SupplyChainSolver(road_engine, ml_predictor=ml_predictor)
    ai_advisor = AIAdvisorService(ml_predictor=ml_predictor)

    app.state.road_engine = road_engine
    app.state.flood_engine = flood_engine
    app.state.evac_solver = evac_solver
    app.state.supply_solver = supply_solver
    app.state.ai_advisor = ai_advisor
    app.state.ml_predictor = ml_predictor
    from backend.app.services.weather_predictor import WeatherPredictor
    app.state.weather_predictor = WeatherPredictor()
    from backend.app.services.realtime_data import RealtimeDataService
    app.state.realtime_data = RealtimeDataService()
    from backend.app.services.kaggle_weather import KaggleWeatherPredictor
    app.state.kaggle_weather_predictor = KaggleWeatherPredictor()
    app.state.simulation_lock = RLock()
    from backend.app.services.simulation_archive import SimulationArchive
    app.state.simulation_archive = SimulationArchive()
    from backend.app.services.reservoir_engine import ChennaiReservoirEngine
    app.state.reservoir_engine = ChennaiReservoirEngine()

    yield


app = FastAPI(
    title="Chennai Natural Disaster (Flood) Simulation Engine",
    description="REST API for spatio-temporal flood modeling, dynamic evacuation pathfinding, and relief logistics routing.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware for Next.js frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "*",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routers under /api
app.include_router(api_router, prefix="/api")


@app.get("/")
def root():
    return {
        "service": "Chennai Natural Disaster Simulation Engine",
        "status": "online",
        "docs_url": "/docs",
        "api_prefix": "/api",
    }
