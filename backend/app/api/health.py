from datetime import datetime, timezone
from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/health")
def get_health(request: Request):
    road_engine = getattr(request.app.state, "road_engine", None)
    evac_solver = getattr(request.app.state, "evac_solver", None)
    supply_solver = getattr(request.app.state, "supply_solver", None)

    nodes_count = len(road_engine.nodes_data) if road_engine else 0
    edges_count = len(road_engine.edges_data) if road_engine else 0
    shelters_count = len(evac_solver.shelters) if evac_solver else 0
    warehouses_count = len(supply_solver.warehouses_baseline) if supply_solver else 0
    dp_count = len(supply_solver.distribution_points_baseline) if supply_solver else 0

    return {
        "status": "ok",
        "service": "chennai-flood-sim",
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "environment": "production",
        "demand_model": "ensemble" if supply_solver and supply_solver.ml_predictor and supply_solver.ml_predictor.is_loaded else "rule_based",
        "model_details": supply_solver.ml_predictor.metadata() if supply_solver and hasattr(supply_solver.ml_predictor, "metadata") else None,
        "network_stats": {
            "nodes_count": nodes_count,
            "edges_count": edges_count,
            "warehouses_count": warehouses_count,
            "shelters_count": shelters_count,
            "distribution_points_count": dp_count,
        },
    }
