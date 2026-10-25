"""
API Router for Chennai Reservoir Hydrology and River Surge Modeling.
Provides telemetry, multi-hour rainfall simulation, and Kaggle historical benchmarks.
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from backend.app.services.reservoir_engine import ChennaiReservoirEngine

router = APIRouter(prefix="/reservoirs", tags=["Reservoirs"])


class ReservoirSimulationRequest(BaseModel):
    rainfall_intensity_mm_hr: float = Field(
        ...,
        ge=0.0,
        le=500.0,
        description="Rainfall intensity in mm/hr across reservoir catchments",
    )
    duration_hours: int = Field(
        default=6,
        ge=1,
        le=72,
        description="Simulation duration in hours",
    )
    initial_storage: Optional[Dict[str, float]] = Field(
        default=None,
        description="Optional initial storage override (Mcft) for Chembarambakkam, Poondi, Red Hills, Cholavaram",
    )


@router.get("", summary="Get real-time Chennai reservoir telemetry and river surge status")
def get_reservoirs_status(request: Request):
    """
    Returns live storage levels, capacity percentages, inflow/outflow cusecs,
    sluice gate statuses, and projected downstream river surges.
    """
    engine = getattr(request.app.state, "reservoir_engine", None)
    if engine is None:
        engine = ChennaiReservoirEngine()
        request.app.state.reservoir_engine = engine

    return {
        "status": "success",
        "data": engine.get_all_reservoirs_summary(),
    }


@router.post("/simulate", summary="Simulate reservoir inflow, storage rise, and discharge surges")
def simulate_reservoir_dynamics(payload: ReservoirSimulationRequest, request: Request):
    """
    Simulates multi-hour rainstorm runoff into the 4 reservoirs.
    Computes storage accumulation, automatic sluice gate openings under WRD dam safety SOPs,
    and downstream river overflow stages for Adyar, Kosasthalaiyar, and Puzhal Surplus corridors.
    """
    init_state = None
    if payload.initial_storage:
        init_state = {k: {"current_storage_mcft": v} for k, v in payload.initial_storage.items()}

    engine = ChennaiReservoirEngine(initial_state=init_state)

    timeline = []
    for hr in range(1, payload.duration_hours + 1):
        step_out = engine.step_simulation(rainfall_mm_hr=payload.rainfall_intensity_mm_hr, step_hours=1.0)
        timeline.append({
            "hour": hr,
            "rainfall_rate_mm_hr": payload.rainfall_intensity_mm_hr,
            "cumulative_rainfall_mm": payload.rainfall_intensity_mm_hr * hr,
            "reservoirs": step_out["reservoirs"],
            "river_surges": step_out["river_surge_summary"],
        })

    return {
        "status": "success",
        "simulation_parameters": {
            "rainfall_intensity_mm_hr": payload.rainfall_intensity_mm_hr,
            "duration_hours": payload.duration_hours,
            "total_rainfall_mm": payload.rainfall_intensity_mm_hr * payload.duration_hours,
        },
        "final_summary": engine.get_all_reservoirs_summary(),
        "timeline": timeline,
    }


@router.get("/historical", summary="Get Kaggle-calibrated historical flood reservoir benchmarks")
def get_historical_benchmarks():
    """
    Returns verified historical discharge and flood crest episodes (2015, 2021, 2023)
    derived from Chennai Water Management data and Tamil Nadu WRD archives.
    """
    return {
        "status": "success",
        "benchmarks": ChennaiReservoirEngine.get_historical_benchmarks(),
    }
