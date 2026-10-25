"""
Supply Chain Logistics & Resource Inventory Ledger Solver.
Tracks multi-depot emergency stocks, calculates relief demands (Sphere standards),
computes flood-avoidant truck delivery routes (depth < 0.3m),
and manages resource allocations with strict conservation invariants.
STRICT CONSTRAINT: No SciPy dependencies.
"""
import json
import os
import math
from copy import deepcopy
from typing import List, Dict, Any, Tuple, Optional
import networkx as nx

from backend.app.services.geometry import (
    haversine,
    point_in_polygon,
    segment_intersects_polygon,
)
from backend.app.services.road_network import RoadNetworkEngine
from backend.app.services.flood_engine import FloodSimulationEngine
from backend.app.models.logistics import (
    SupplyStock,
    SupplyRoute,
    InventoryLedgerWarehouse,
    InventoryLedgerDistributionPoint,
    InventoryStatus,
    AllocationTransfer,
)


class SupplyChainSolver:
    def __init__(
        self,
        road_engine: RoadNetworkEngine,
        data_dir: Optional[str] = None,
        ml_predictor = None
    ):
        self.road_engine = road_engine
        self.ml_predictor = ml_predictor
        if data_dir is None:
            data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
        self.data_dir = data_dir
        self.warehouses_baseline: List[Dict[str, Any]] = []
        self.distribution_points_baseline: List[Dict[str, Any]] = []

        # Active state ledgers
        self.warehouse_stocks: Dict[str, Dict[str, Any]] = {}
        self.point_demands: Dict[str, Dict[str, Any]] = {}
        self._load_data()
        self.reset_ledger()

    def _load_data(self):
        wh_path = os.path.join(self.data_dir, "warehouses.json")
        if os.path.exists(wh_path):
            with open(wh_path, "r", encoding="utf-8") as f:
                self.warehouses_baseline = json.load(f)

        dp_path = os.path.join(self.data_dir, "distribution_points.json")
        if os.path.exists(dp_path):
            with open(dp_path, "r", encoding="utf-8") as f:
                self.distribution_points_baseline = json.load(f)
        shelter_path = os.path.join(self.data_dir, "shelters.json")
        self.shelter_destinations = []
        if os.path.exists(shelter_path):
            with open(shelter_path, "r", encoding="utf-8") as f:
                self.shelter_destinations = json.load(f)

    def reset_ledger(self):
        self.ml_predictions = 0
        self.rule_predictions = 0
        """Resets warehouse inventories and distribution point allocations to baseline."""
        self.warehouse_stocks = {}
        for w in self.warehouses_baseline:
            wid = w["id"]
            sup = w.get("supplies", {})
            self.warehouse_stocks[wid] = {
                "id": wid,
                "name": w["name"],
                "location": w["location"],
                "total": {
                    "water_litres": sup.get("water_litres", 0),
                    "food_rations": sup.get("food_rations", 0),
                    "medical_kits": sup.get("medical_kits", 0),
                },
                "allocated": {
                    "water_litres": 0,
                    "food_rations": 0,
                    "medical_kits": 0,
                },
                "dispatched": {
                    "water_litres": 0,
                    "food_rations": 0,
                    "medical_kits": 0,
                },
                "available": {
                    "water_litres": sup.get("water_litres", 0),
                    "food_rations": sup.get("food_rations", 0),
                    "medical_kits": sup.get("medical_kits", 0),
                },
            }

        self.point_demands = {}
        for dp in self.distribution_points_baseline + self.shelter_destinations:
            dpid = dp["id"]
            dem = dp.get("demand", {})
            self.point_demands[dpid] = {
                "id": dpid,
                "name": dp["name"],
                "location": dp["location"],
                "target_ward": dp.get("target_ward", ""),
                "assigned_evacuees": dp.get("assigned_evacuee_capacity", 0),
                "demand": {
                    "water_litres": dem.get("water_litres", 0),
                    "food_rations": dem.get("food_rations", 0),
                    "medical_kits": dem.get("medical_kits", 0),
                },
                "allocated": {
                    "water_litres": 0,
                    "food_rations": 0,
                    "medical_kits": 0,
                },
                "status": "deficit",
            }

    def verify_invariants(self):
        """
        Asserts fundamental ledger invariants:
        1. Non-negativity of all stocks.
        2. TotalStock == AvailableStock + AllocatedStock + DispatchedStock.
        """
        for wid, w in self.warehouse_stocks.items():
            for item in ["water_litres", "food_rations", "medical_kits"]:
                tot = w["total"][item]
                avail = w["available"][item]
                alloc = w["allocated"][item]
                disp = w["dispatched"][item]

                assert avail >= 0, f"Negative available stock for {wid} - {item}: {avail}"
                assert alloc >= 0, f"Negative allocated stock for {wid} - {item}: {alloc}"
                assert disp >= 0, f"Negative dispatched stock for {wid} - {item}: {disp}"
                assert tot == (avail + alloc + disp), (
                    f"Conservation violated for {wid} - {item}: total {tot} != "
                    f"avail {avail} + alloc {alloc} + disp {disp}"
                )

    def update_demands_from_evacuees(self, shelter_or_point_evacuees: Dict[str, int], params=None, step_zones=None):
        """
        Dynamically updates supply demands based on evacuee headcounts
        using either the PyTorch DNN ML model or Sphere Humanitarian Standards fallback.
        """
        for pid, pop in shelter_or_point_evacuees.items():
            if pid in self.point_demands:
                pt = self.point_demands[pid]
                pt["assigned_evacuees"] = pop
                
                # Attempt ML prediction
                if self.ml_predictor and self.ml_predictor.is_loaded and params and step_zones:
                    p_lat, p_lon = pt["location"]
                    depth = self.road_engine.flood_engine.get_point_depth(p_lat, p_lon, step_zones)
                    rainfall = getattr(params, "rainfall_intensity_mm_hr", 65.0)
                    
                    # Estimate population density (mocked for point) and vulnerability
                    clusters = getattr(self.road_engine, "population_clusters", None)
                    if clusters is None:
                        with open(os.path.join(self.data_dir, "population_clusters.json"), encoding="utf-8") as f:
                            clusters = json.load(f)
                        self.road_engine.population_clusters = clusters
                    nearest = min(clusters, key=lambda c: haversine(p_lat, p_lon, *c["location"])) if clusters else {}
                    pop_density = nearest.get("density_per_sqkm", 15000.0)
                    # Estimated categorical mapping, not measured vulnerability.
                    vulnerability = {"Low": 0.6, "Moderate": 0.7, "High": 0.85, "Very High": 0.95, "Extreme": 0.99}.get(nearest.get("risk_level"), 0.8)

                    # Determine effective disaster depth for arriving evacuees (bounded to model domain)
                    scenario_depth = getattr(params, "flood_depth_meters", 1.2)
                    eff_depth = max(0.1, min(4.5, float(depth if depth > 0 else scenario_depth)))
                    eff_rain = max(15.0, min(500.0, float(rainfall if rainfall > 0 else 65.0)))
                    eff_density = max(10203.0, min(43689.0, float(pop_density if pop_density > 0 else 18000.0)))
                    eff_vuln = max(0.6175, min(0.99, float(vulnerability if vulnerability > 0 else 0.85)))
                    
                    prediction = self.ml_predictor.predict_demand(
                        rainfall_mm_hr=eff_rain,
                        flood_depth_m=eff_depth,
                        pop_density_sqkm=eff_density,
                        vulnerability=eff_vuln,
                        shelter_occupancy=pop
                    )
                    
                    if prediction:
                        pt["demand"]["water_litres"] = prediction["water_litres"]
                        pt["demand"]["food_rations"] = prediction["food_rations"]
                        pt["demand"]["medical_kits"] = prediction["medical_kits"]
                        pt["demand"]["is_ai_predicted"] = True
                        pt["prediction_metadata"] = {k: v for k, v in prediction.items() if k not in ("water_litres", "food_rations", "medical_kits")}
                        self.ml_predictions += 1
                        continue
                
                # Fallback to Sphere Standards
                pt["demand"]["water_litres"] = pop * 3
                pt["demand"]["food_rations"] = pop * 3
                pt["demand"]["medical_kits"] = max(10, math.ceil(pop * 0.02)) if pop > 0 else 0
                pt["demand"]["is_ai_predicted"] = False
                pt["prediction_metadata"] = {"model": "planning_rules", "reason": "ML unavailable or inputs outside training range"}
                self.rule_predictions += 1

    def is_route_safe(
        self,
        coords: List[List[float]],
        step_zones_state: List[Dict[str, Any]],
        depth_threshold_m: float = 0.30
    ) -> bool:
        """
        Verifies that every point and road segment along the proposed route is
        completely free of flood water >= depth_threshold_m, checking both edge depth
        and analytical polygon intersections.
        """
        if not coords or len(coords) < 2:
            return False

        # Check endpoints and vertices
        for pt in coords:
            pt_d = self.road_engine.flood_engine.get_point_depth(pt[0], pt[1], step_zones_state)
            if pt_d >= depth_threshold_m:
                return False

        # Check all segments analytically
        for i in range(len(coords) - 1):
            p1 = coords[i]
            p2 = coords[i + 1]
            source = self.road_engine.find_nearest_node(*p1)
            target = self.road_engine.find_nearest_node(*p2)
            source_node = self.road_engine.nodes_data.get(source, {})
            target_node = self.road_engine.nodes_data.get(target, {})
            on_road = (source_node.get("lat") == p1[0] and source_node.get("lon") == p1[1]
                       and target_node.get("lat") == p2[0] and target_node.get("lon") == p2[1])
            edge = self.road_engine.base_graph.get_edge_data(source, target, {}) if on_road else {}
            elevated = bool(edge.get("is_elevated", False))
            edge_depth = self.road_engine.flood_engine.get_edge_depth(
                p1[0], p1[1], p2[0], p2[1], step_zones_state, is_elevated=elevated
            )
            if edge_depth >= depth_threshold_m:
                return False

            # Direct analytical segment-polygon intersection check against flood polygons
            for z in step_zones_state:
                if isinstance(z, dict) and "geometry" in z:
                    z_depth = float(z.get("properties", {}).get("depth_meters", z.get("properties", {}).get("water_depth_m", 0.0)))
                    if z_depth >= depth_threshold_m:
                        if segment_intersects_polygon(p1, p2, z["geometry"].get("coordinates", [])):
                            return False
                    continue

                z_peak = float(z.get("peak_depth", z.get("water_depth_m", 0.0)))
                if elevated and z_peak < 1.50:
                    continue
                if z_peak >= depth_threshold_m:
                    poly = z.get("polygon_latlon")
                    if poly and segment_intersects_polygon(p1, p2, poly):
                        return False

        return True

    def solve_supply_distribution(
        self,
        step_zones_state: List[Dict[str, Any]],
        auto_allocate: bool = True,
        selected_warehouse_ids: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Builds truck-safe road graph (depth < 0.3m), computes delivery paths from
        closest available warehouses to distribution points, and tracks inventory.
        Strictly guarantees truck routes avoid depth >= 0.30m, rerouting to
        amphibious rescue boat or helicopter airlift when flooded.
        """
        # Build truck-safe graph: depth >= 0.3m is impassable
        truck_graph = self.road_engine.build_dynamic_graph(
            step_zones_state, closure_threshold_m=0.30, slowdown_threshold_m=0.05, mode="truck"
        )

        # Build amphibious graph for deep water routing
        amphibious_graph = self.road_engine.build_dynamic_graph(
            step_zones_state, closure_threshold_m=1.50, slowdown_threshold_m=0.50, is_amphibious=True, mode="truck"
        )

        supply_routes = []
        isolated_points = []
        eligible_warehouses = {
            wid: w for wid, w in self.warehouse_stocks.items()
            if selected_warehouse_ids is None or wid in selected_warehouse_ids
        }

        max_passes = 3 if auto_allocate else 1
        for pass_num in range(max_passes):
            allocated_any_in_pass = False
            for dpid, pt in self.point_demands.items():
                if auto_allocate and all(pt["allocated"][k] >= pt["demand"][k] for k in ("water_litres", "food_rations", "medical_kits")):
                    pt["status"] = "supplied"
                    continue
                p_lat, p_lon = pt["location"]

                # Calculate depth at destination point
                pt_depth = self.road_engine.flood_engine.get_point_depth(p_lat, p_lon, step_zones_state)
                p_node = self.road_engine.find_nearest_node(p_lat, p_lon, mode="truck")

                needed_items = [k for k in ("water_litres", "food_rations", "medical_kits") if pt["demand"][k] > pt["allocated"][k]]
                candidate_items = needed_items if (auto_allocate and needed_items) else ["water_litres", "food_rations", "medical_kits"]

                best_candidate = None
                
                # 1. Try Truck Route: strictly only if destination is flood-free (depth < 0.30m)
                if pt_depth < 0.30:
                    min_t = float('inf')
                    for wid, w in eligible_warehouses.items():
                        if not any(w["available"][k] > 0 for k in candidate_items):
                            continue
                        w_lat, w_lon = w["location"]
                        w_depth = self.road_engine.flood_engine.get_point_depth(w_lat, w_lon, step_zones_state)
                        if w_depth >= 0.30:
                            continue

                        w_node = self.road_engine.find_nearest_node(w_lat, w_lon, mode="truck")
                        if w_node and p_node and truck_graph.has_node(w_node) and truck_graph.has_node(p_node):
                            try:
                                path = nx.shortest_path(truck_graph, source=w_node, target=p_node, weight="weight")
                                dist_km, time_min = self.road_engine.get_route_metrics(truck_graph, path)
                                route_coords = self.road_engine.get_route_coordinates(path, truck_graph)
                                candidate_coords = [w["location"]] + route_coords + [[p_lat, p_lon]]

                                # Zero Flood Intersection Guarantee for truck route:
                                if self.is_route_safe(candidate_coords, step_zones_state, depth_threshold_m=0.30):
                                    if time_min < min_t:
                                        min_t = time_min
                                        best_candidate = {
                                            "warehouse_id": wid,
                                            "warehouse_name": w["name"],
                                            "warehouse_loc": [w_lat, w_lon],
                                            "node_path": path,
                                            "distance_km": dist_km,
                                            "travel_time_min": time_min,
                                            "mode": "truck",
                                            "coords": candidate_coords,
                                            "road_coords": route_coords,
                                        }
                            except nx.NetworkXNoPath:
                                pass
                                
                # 2. Try Amphibious Boat Route if truck route impossible (destination flooded >= 0.30m or severed roads)
                if not best_candidate and pt_depth < 1.50:
                    min_t = float('inf')
                    for wid, w in eligible_warehouses.items():
                        if not any(w["available"][k] > 0 for k in candidate_items):
                            continue
                        w_lat, w_lon = w["location"]
                        w_node = self.road_engine.find_nearest_node(w_lat, w_lon, mode="truck")
                        if w_node and p_node and amphibious_graph.has_node(w_node) and amphibious_graph.has_node(p_node):
                            try:
                                path = nx.shortest_path(amphibious_graph, source=w_node, target=p_node, weight="weight")
                                dist_km, time_min = self.road_engine.get_route_metrics(amphibious_graph, path)
                                route_coords = self.road_engine.get_route_coordinates(path, amphibious_graph)
                                candidate_coords = [w["location"]] + route_coords + [[p_lat, p_lon]]
                                if time_min < min_t:
                                    min_t = time_min
                                    best_candidate = {
                                        "warehouse_id": wid,
                                        "warehouse_name": w["name"],
                                        "warehouse_loc": [w_lat, w_lon],
                                        "node_path": path,
                                        "distance_km": dist_km,
                                        "travel_time_min": time_min,
                                        "mode": "amphibious",
                                        "coords": candidate_coords,
                                        "road_coords": route_coords,
                                    }
                            except nx.NetworkXNoPath:
                                pass
                                
                # 3. Try Helicopter Route (direct air path) for stranded or deep flooded destinations
                if not best_candidate:
                    min_t = float('inf')
                    for wid, w in eligible_warehouses.items():
                        if not any(w["available"][k] > 0 for k in candidate_items):
                            continue
                        w_lat, w_lon = w["location"]
                        dist_km = haversine(w_lat, w_lon, p_lat, p_lon)
                        time_min = (dist_km / 120.0) * 60.0
                        if time_min < min_t:
                            min_t = time_min
                            best_candidate = {
                                "warehouse_id": wid,
                                "warehouse_name": w["name"],
                                "warehouse_loc": [w_lat, w_lon],
                                "node_path": [],
                                "distance_km": round(dist_km, 2),
                                "travel_time_min": round(time_min, 1),
                                "mode": "helicopter",
                                "coords": [[w_lat, w_lon], [p_lat, p_lon]],
                            }

                if not best_candidate:
                    if pass_num == 0:
                        pt["status"] = "isolated"
                        isolated_points.append({
                            "point_id": dpid,
                            "name": pt["name"],
                            "location": [p_lat, p_lon],
                            "status": "ISOLATED_ROAD_IMPASSABLE",
                            "recommendation": "AWAIT_RESUPPLY",
                        })
                    continue

                if best_candidate.get("coords"):
                    full_coords = []
                    for coord_pt in best_candidate["coords"]:
                        if not full_coords or haversine(full_coords[-1][0], full_coords[-1][1], coord_pt[0], coord_pt[1]) > 0.000001:
                            full_coords.append(coord_pt)
                elif best_candidate["mode"] == "helicopter":
                    full_coords = [best_candidate["warehouse_loc"], [p_lat, p_lon]]
                else:
                    route_coords = self.road_engine.get_route_coordinates(best_candidate["node_path"])
                    raw_pts = [best_candidate["warehouse_loc"]] + route_coords + [[p_lat, p_lon]]
                    full_coords = []
                    for coord_pt in raw_pts:
                        if not full_coords or haversine(full_coords[-1][0], full_coords[-1][1], coord_pt[0], coord_pt[1]) > 0.000001:
                            full_coords.append(coord_pt)

                # Report the complete displayed geometry, including access approaches.
                if best_candidate['mode'] != 'helicopter':
                    road_coords = best_candidate['road_coords']
                    gaps = self.road_engine.route_provenance(road_coords, best_candidate['warehouse_loc'], [p_lat,p_lon])['access_connectors_m']
                    best_candidate['distance_km'] = round(sum(haversine(*a,*b) for a,b in zip(full_coords,full_coords[1:])),3)
                    best_candidate['travel_time_min'] = round(best_candidate['travel_time_min'] + sum(gaps)/1000/5*60,1)
                wid = best_candidate["warehouse_id"]
                w = self.warehouse_stocks[wid]
                cargo = {"water_litres": 0, "food_rations": 0, "medical_kits": 0}

                if auto_allocate:
                    for item in ["water_litres", "food_rations", "medical_kits"]:
                        needed = max(0, pt["demand"][item] - pt["allocated"][item])
                        if needed > 0 and w["available"][item] > 0:
                            alloc = min(needed, w["available"][item])
                            cargo[item] = alloc
                            w["available"][item] -= alloc
                            w["allocated"][item] += alloc
                            pt["allocated"][item] += alloc

                if any(cargo[k] > 0 for k in cargo):
                    allocated_any_in_pass = True

                is_satisfied = all(
                    pt["allocated"][k] >= pt["demand"][k] for k in ["water_litres", "food_rations", "medical_kits"]
                )
                pt["status"] = "supplied" if is_satisfied else "deficit"

                total_cargo_units = cargo["water_litres"] + cargo["food_rations"]
                
                if best_candidate["mode"] == "helicopter":
                    vehicle_type = "Relief Helicopter"
                    wading_clearance_m = 99.0
                    convoy_vehicles = max(1, int(total_cargo_units / 1000 + 0.9)) if total_cargo_units > 0 else 1
                elif best_candidate["mode"] == "amphibious":
                    vehicle_type = "Amphibious Rescue Boat"
                    wading_clearance_m = 1.50
                    convoy_vehicles = max(1, int(total_cargo_units / 1500 + 0.9)) if total_cargo_units > 0 else 1
                else:
                    vehicle_type = "Heavy All-Terrain Truck (6x6)" if total_cargo_units >= 3000 else "Rapid Logistics Utility Van"
                    wading_clearance_m = 0.40 if total_cargo_units >= 3000 else 0.30
                    convoy_vehicles = max(1, int(total_cargo_units / 2500 + 0.9)) if total_cargo_units > 0 else 1

                route_id = f"SR-{wid}-TO-{dpid}-{pass_num+1}" if pass_num > 0 else f"SR-{wid}-TO-{dpid}"
                supply_routes.append({
                    "route_id": route_id,
                    "warehouse_id": wid,
                    "warehouse_name": best_candidate["warehouse_name"],
                    "destination_id": dpid,
                    "destination_name": pt["name"],
                    "distance_km": best_candidate["distance_km"],
                    "transit_time_min": best_candidate["travel_time_min"],
                    "allocated_cargo": cargo,
                    "vehicle_type": vehicle_type,
                    "transport_mode": best_candidate["mode"],
                    "wading_depth_clearance_m": wading_clearance_m,
                    "convoy_vehicles": convoy_vehicles,
                    "route_status": "unblocked",
                    "coordinates": full_coords,
                    "road_provenance": self.road_engine.route_provenance(
                        best_candidate.get("road_coords", []) if best_candidate["mode"] != "helicopter" else [],
                        best_candidate["warehouse_loc"], [p_lat,p_lon], "truck")
                        if best_candidate["mode"] != "helicopter" else {"geometry_kind":"direct_air_proxy", "access_note":"Direct airlift estimate; flight permissions and landing access are not modeled."},
                })
            if not allocated_any_in_pass:
                break
        self.verify_invariants()

        # Format GeoJSON FeatureCollection
        features = []
        for sr in supply_routes:
            # Standard GeoJSON format: coordinates are [lon, lat]
            geojson_line = [[round(pt[1], 6), round(pt[0], 6)] for pt in sr["coordinates"]]
            features.append({
                "type": "Feature",
                "id": sr["route_id"],
                "geometry": {
                    "type": "LineString",
                    "coordinates": geojson_line,
                },
                "properties": {
                    **sr.get("road_provenance", {}),
                    "route_id": sr["route_id"],
                    "warehouse_id": sr["warehouse_id"],
                    "warehouse_name": sr["warehouse_name"],
                    "destination_id": sr["destination_id"],
                    "destination_name": sr["destination_name"],
                    "distance_km": sr["distance_km"],
                    "transit_time_min": sr["transit_time_min"],
                    "allocated_cargo": sr["allocated_cargo"],
                    "cargo": sr["allocated_cargo"],
                    "status": "active",
                    "vehicle_type": sr.get("vehicle_type", "Rapid Logistics Utility Van"),
                    "transport_mode": sr["transport_mode"],
                    "wading_depth_clearance_m": sr.get("wading_depth_clearance_m", 0.30),
                    "convoy_vehicles": sr.get("convoy_vehicles", 1),
                    "route_status": sr["route_status"],
                },
            })

        routes_geojson = {
            "type": "FeatureCollection",
            "features": features,
        }

        # Format inventory status summary
        tot_w = sum(w["total"]["water_litres"] for w in self.warehouse_stocks.values())
        alloc_w = sum(w["allocated"]["water_litres"] for w in self.warehouse_stocks.values())
        tot_f = sum(w["total"]["food_rations"] for w in self.warehouse_stocks.values())
        alloc_f = sum(w["allocated"]["food_rations"] for w in self.warehouse_stocks.values())
        tot_m = sum(w["total"]["medical_kits"] for w in self.warehouse_stocks.values())
        alloc_m = sum(w["allocated"]["medical_kits"] for w in self.warehouse_stocks.values())

        inventory_status = {
            "available_water_litres": tot_w - alloc_w,
            "available_food_rations": tot_f - alloc_f,
            "available_medical_kits": tot_m - alloc_m,
            "total_water_litres": tot_w,
            "allocated_water_litres": alloc_w,
            "total_food_rations": tot_f,
            "allocated_food_rations": alloc_f,
            "total_medical_kits": tot_m,
            "allocated_medical_kits": alloc_m,
        }

        return {
            "supply_routes": routes_geojson,
            "isolated_points": isolated_points,
            "inventory_status": inventory_status,
            "ledger": self.get_ledger_snapshot(),
        }

    def allocate_supplies(
        self,
        transfers: List[AllocationTransfer],
        step_zones_state: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Executes explicit manual or targeted supply allocations from warehouses to distribution points.
        Validates inventory availability and recalculates truck routes.
        """
        warnings = []
        # Validate the entire batch before changing any stock. Repeated transfers
        # from the same warehouse must be checked cumulatively.
        remaining = {wid: dict(w["available"]) for wid, w in self.warehouse_stocks.items()}
        for tr in transfers:
            if tr.source_warehouse_id not in remaining:
                raise ValueError(f"Warehouse ID '{tr.source_warehouse_id}' does not exist.")
            if tr.destination_point_id not in self.point_demands:
                raise ValueError(f"Distribution point / Shelter ID '{tr.destination_point_id}' does not exist.")
            for item, qty in tr.supplies.model_dump().items():
                if qty > remaining[tr.source_warehouse_id][item]:
                    raise ValueError(f"Insufficient inventory in warehouse '{tr.source_warehouse_id}' for {item}.")
                remaining[tr.source_warehouse_id][item] -= qty
        planned_routes = []
        all_stocks, all_demands = self.warehouse_stocks, self.point_demands
        try:
            for transfer in transfers:
                # Plan against the depot actually selected, before committing stock.
                self.warehouse_stocks = {transfer.source_warehouse_id: all_stocks[transfer.source_warehouse_id]}
                self.point_demands = {transfer.destination_point_id: deepcopy(all_demands[transfer.destination_point_id])}
                plan = self.solve_supply_distribution(step_zones_state or [], auto_allocate=False)
                if not plan["supply_routes"]["features"]:
                    raise ValueError("No delivery route is available from the selected warehouse.")
                for feature in plan["supply_routes"]["features"]:
                    feature["properties"]["allocated_cargo"] = transfer.supplies.model_dump()
                    feature["properties"]["cargo"] = transfer.supplies.model_dump()
                    planned_routes.append(feature)
        finally:
            self.warehouse_stocks, self.point_demands = all_stocks, all_demands

        for tr in transfers:
            wid = tr.source_warehouse_id
            dpid = tr.destination_point_id
            req_sup = tr.supplies

            if wid not in self.warehouse_stocks:
                raise ValueError(f"Warehouse ID '{wid}' does not exist.")
            if dpid not in self.point_demands:
                raise ValueError(f"Distribution point / Shelter ID '{dpid}' does not exist.")

            w = self.warehouse_stocks[wid]
            pt = self.point_demands[dpid]

            for item, requested_qty in [
                ("water_litres", req_sup.water_litres),
                ("food_rations", req_sup.food_rations),
                ("medical_kits", req_sup.medical_kits),
            ]:
                if requested_qty <= 0:
                    continue

                available = w["available"][item]
                if requested_qty > available:
                    raise ValueError(
                        f"Insufficient inventory in warehouse '{w['name']}' ({wid}) for {item}. "
                        f"Requested: {requested_qty}, Available: {available}."
                    )

                w["available"][item] -= requested_qty
                w["allocated"][item] += requested_qty
                pt["allocated"][item] += requested_qty

        self.verify_invariants()

        # Recalculate routes if step_zones_state provided
        step_zones = step_zones_state if step_zones_state is not None else []
        sol_result = self.solve_supply_distribution(step_zones, auto_allocate=False)

        # Filter updated routes: ensure updated_supply_routes contains ONLY 100% flood-free truck routes!
        updated_truck_routes = []
        updated_rescue_routes = []
        for f in planned_routes:
            mode = f.get("properties", {}).get("transport_mode", "truck")
            geom = f.get("geometry", {})
            raw_coords = geom.get("coordinates", [])
            latlon_coords = [[c[1], c[0]] for c in raw_coords]

            if mode == "truck":
                if self.is_route_safe(latlon_coords, step_zones, depth_threshold_m=0.30):
                    updated_truck_routes.append(f)
                else:
                    # Reroute to helicopter airlift rescue route
                    f["properties"]["transport_mode"] = "helicopter"
                    f["properties"]["vehicle_type"] = "Relief Helicopter (Airlift Reroute)"
                    f["properties"]["wading_depth_clearance_m"] = 99.0
                    updated_rescue_routes.append(f)
            else:
                updated_rescue_routes.append(f)

        return {
            "success": True,
            "message": "Supplies allocated successfully.",
            "updated_inventory": sol_result["inventory_status"],
            "updated_supply_routes": updated_truck_routes,
            "updated_rescue_routes": updated_rescue_routes,
            "ledger": sol_result["ledger"],
            "warnings": warnings,
        }

    def get_ledger_snapshot(self) -> Dict[str, Any]:
        """Returns structured warehouse and distribution point ledger."""
        wh_list = []
        for wid, w in self.warehouse_stocks.items():
            wh_list.append({
                "warehouse_id": wid,
                "name": w["name"],
                "total_stock": w["total"],
                "allocated_stock": w["allocated"],
                "available_stock": w["available"],
            })

        dp_list = []
        for dpid, pt in self.point_demands.items():
            deficit = {
                k: max(0, pt["demand"][k] - pt["allocated"][k])
                for k in ["water_litres", "food_rations", "medical_kits"]
            }
            dp_list.append({
                "distribution_point_id": dpid,
                "name": pt["name"],
                "target_ward": pt["target_ward"],
                "assigned_evacuees": pt["assigned_evacuees"],
                "demand": pt["demand"],
                "allocated": pt["allocated"],
                "deficit": deficit,
                "status": pt["status"],
                "prediction_metadata": pt.get("prediction_metadata"),
            })

        return deepcopy({
            "warehouses": wh_list,
            "distribution_points": [p for p in dp_list if p["distribution_point_id"] in {d["id"] for d in self.distribution_points_baseline}],
            "shelters": [p for p in dp_list if p["distribution_point_id"] in {s["id"] for s in self.shelter_destinations}],
        })

    @staticmethod
    def compute_sphere_standard_relief_needs(
        population: int, duration_days: int = 1, severity: str = "moderate"
    ) -> Dict[str, Any]:
        """
        Calculates relief material quotas based on Sphere Humanitarian Standards:
        - Water: 3.0 L/person/day basic survival; 7.5 - 15.0 L/person/day for full hygiene.
        - Food: 2,100 kcal / ration packet / person / day.
        - Medical kits: 1 basic primary care / trauma / cholera prevention kit per 50 people.
        - Hygiene kits: 1 family kit per 5 people.
        """
        pop = max(0, int(population))
        days = max(1, int(duration_days))

        # Scaling factor based on flood severity
        sev_multiplier = {"low": 1.0, "moderate": 1.2, "severe": 1.5, "catastrophic": 2.0}.get(severity.lower(), 1.2)

        water_l = int(pop * 3.0 * days * sev_multiplier)
        food_rations = int(pop * 3.0 * days)
        med_kits = max(5, int(math.ceil(pop * 0.02 * days * sev_multiplier)))
        hygiene_kits = int(math.ceil(pop / 5.0))

        return {
            "population": pop,
            "duration_days": days,
            "severity": severity,
            "standard": "Sphere Humanitarian Charter (2018)",
            "water_litres": water_l,
            "food_rations": food_rations,
            "medical_kits": med_kits,
            "hygiene_family_kits": hygiene_kits,
        }

    @staticmethod
    def evaluate_vehicle_traversability(
        water_depth_m: float, flow_velocity_m_s: float = 0.0, vehicle_mode: str = "truck"
    ) -> Dict[str, Any]:
        """
        Evaluates physical hydrodynamic traversability and stability limits:
        Vehicle instability occurs when depth or hydrodynamic momentum (D x V) exceeds stability limits.
        - Utility Van: Depth < 0.15m, D x V < 0.15 m^2/s
        - 6x6 Heavy All-Terrain Truck: Depth < 0.30m (wading 0.40m max), D x V < 0.30 m^2/s
        - Amphibious Boat: Depth >= 0.30m, Velocity < 2.5 m/s
        - Helicopter: All water depths, velocity independent
        """
        depth = max(0.0, float(water_depth_m))
        v = max(0.0, float(flow_velocity_m_s))
        dv_product = round(depth * v, 3)

        if vehicle_mode == "helicopter":
            return {"passable": True, "recommended_mode": "helicopter", "reason": "Air transit unaffected by surface water"}

        if vehicle_mode == "amphibious":
            passable = depth >= 0.15 and v < 3.0
            return {
                "passable": passable,
                "recommended_mode": "amphibious",
                "reason": "Sufficient water depth for watercraft hull" if passable else "Water too shallow or flow too rapid",
            }

        # Standard ground transport
        truck_safe = (depth < 0.30) and (dv_product < 0.30)
        van_safe = (depth < 0.15) and (dv_product < 0.15)

        if van_safe:
            rec = "Rapid Logistics Utility Van"
        elif truck_safe:
            rec = "Heavy All-Terrain Truck (6x6)"
        elif depth < 1.50:
            rec = "Amphibious Rescue Boat"
        else:
            rec = "Tactical Air Delivery / Helicopter"

        return {
            "passable": truck_safe,
            "water_depth_m": depth,
            "flow_velocity_m_s": v,
            "dv_product_m2_s": dv_product,
            "recommended_vehicle": rec,
            "hydrodynamic_hazard": "high" if dv_product >= 0.30 else ("moderate" if dv_product >= 0.15 else "low"),
        }
