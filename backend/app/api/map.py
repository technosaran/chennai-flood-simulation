import json
import os
from fastapi import APIRouter, Request

router = APIRouter()


@router.get('/wards')
def ward_profiles():
    from backend.app.services.ward_profiles import profiles
    return profiles()


@router.get("/map/init")
def get_map_init(request: Request):
    evac_solver = getattr(request.app.state, "evac_solver", None)
    supply_solver = getattr(request.app.state, "supply_solver", None)
    flood_engine = getattr(request.app.state, "flood_engine", None)

    shelters = evac_solver.shelters if evac_solver else []
    warehouses = supply_solver.warehouses_baseline if supply_solver else []
    distribution_points = supply_solver.distribution_points_baseline if supply_solver else []
    raw_clusters = evac_solver.population_clusters if evac_solver else []
    population_clusters = []
    for c in raw_clusters:
        c_dict = dict(c)
        dens = c.get("density_per_sqkm", c.get("density_per_sq_km", 0))
        c_dict["density_per_sqkm"] = dens
        c_dict["density_per_sq_km"] = dens
        risk = str(c.get("risk_level", "moderate")).lower()
        c_dict["risk_level"] = "extreme" if risk == "very high" else risk
        population_clusters.append(c_dict)
    presets = list(flood_engine.presets.values()) if flood_engine else []

    return {
        "road_network": getattr(request.app.state, "road_engine", None).metadata if getattr(request.app.state, "road_engine", None) else {},
        "city": "Chennai",
        "center": [13.0827, 80.2707],
        "default_zoom": 12,
        "bounds": [[12.85, 80.10], [13.25, 80.35]],
        "shelters": shelters,
        "warehouses": warehouses,
        "distribution_points": distribution_points,
        "population_clusters": population_clusters,
        "presets": presets,
    }
