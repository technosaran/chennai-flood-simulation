"""All advisory views share one completed, simulation-scoped snapshot."""
from copy import deepcopy
from typing import Optional
from fastapi import APIRouter, HTTPException, Request

router = APIRouter()


def advisory_snapshot(request: Request, simulation_id: Optional[str]):
    with request.app.state.simulation_lock:
        latest = getattr(request.app.state, "latest_simulation", None)
        if not latest:
            raise HTTPException(status_code=409, detail="Run a simulation before requesting advice.")
        if simulation_id and latest["simulation_id"] != simulation_id:
            raise HTTPException(status_code=409, detail="The active simulation has changed. Run your scenario again.")
        advisory = latest.get("ai_advisory")
        if not advisory:
            raise HTTPException(status_code=503, detail="Advice is unavailable for this simulation.")
        return {**deepcopy(advisory), "simulation_id": latest["simulation_id"],
                "snapshot_hour": latest["timeline"][-1]["hour"]}


@router.get("/advisory")
def get_latest_advisory(request: Request, simulation_id: Optional[str] = None):
    return advisory_snapshot(request, simulation_id)


@router.get("/advisory/wards")
def get_ward_vulnerability_rankings(request: Request, simulation_id: Optional[str] = None):
    snapshot = advisory_snapshot(request, simulation_id)
    return {"status": "success", "simulation_id": snapshot["simulation_id"],
            "snapshot_hour": snapshot["snapshot_hour"], "ward_rankings": snapshot["ward_vulnerability_index"]}


@router.get("/advisory/airlift")
def get_optimal_airlift_zones(request: Request, simulation_id: Optional[str] = None):
    snapshot = advisory_snapshot(request, simulation_id)
    return {"status": "success", "simulation_id": snapshot["simulation_id"],
            "snapshot_hour": snapshot["snapshot_hour"], "optimal_airlift_drop_zones": snapshot["optimal_airlift_drop_zones"]}


@router.get("/advisory/broadcast")
def get_bilingual_broadcasts(request: Request, simulation_id: Optional[str] = None):
    snapshot = advisory_snapshot(request, simulation_id)
    return {"status": "success", "simulation_id": snapshot["simulation_id"],
            "snapshot_hour": snapshot["snapshot_hour"], "emergency_broadcasts": snapshot["bilingual_emergency_broadcasts"]}


@router.get("/advisory/mcdm")
def get_mcdm_topsis_rankings(request: Request, simulation_id: Optional[str] = None):
    snapshot = advisory_snapshot(request, simulation_id)
    return {
        "status": "success",
        "simulation_id": snapshot["simulation_id"],
        "snapshot_hour": snapshot["snapshot_hour"],
        "mcdm_topsis_rankings": snapshot.get("mcdm_topsis_rankings", {}),
    }
