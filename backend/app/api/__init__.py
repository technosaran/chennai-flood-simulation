from fastapi import APIRouter
from backend.app.api.health import router as health_router
from backend.app.api.map import router as map_router
from backend.app.api.simulation import router as simulation_router
from backend.app.api.resources import router as resources_router
from backend.app.api.advisory import router as advisory_router
from backend.app.api.evaluation import router as evaluation_router
from backend.app.api.weather import router as weather_router
from backend.app.api.archive import router as archive_router
from backend.app.api.reservoirs import router as reservoirs_router

from backend.app.api.realtime import router as realtime_router

api_router = APIRouter()
api_router.include_router(realtime_router, tags=["Recent weather & alerts"])

api_router.include_router(health_router, tags=["Health"])
api_router.include_router(map_router, tags=["Map"])
api_router.include_router(simulation_router, tags=["Simulation"])
api_router.include_router(resources_router, tags=["Resources"])
api_router.include_router(advisory_router, tags=["AI Advisory"])
api_router.include_router(evaluation_router, tags=["Model Evaluation"])
api_router.include_router(weather_router, tags=["Weather ML"])
api_router.include_router(archive_router, tags=['Saved Simulations'])
api_router.include_router(reservoirs_router, tags=["Reservoirs"])

__all__ = ["api_router"]
