"""
Evacuation Planning & Capacity-Constrained Shelter Allocation Solver.
Calculates shortest safe paths on the dynamic inundated road graph using Dijkstra/A*,
allocates evacuees to nearest available shelters without exceeding 100% capacity,
and flags isolated/submerged clusters requiring airlift/boat rescue.
STRICT CONSTRAINT: No SciPy dependencies.
"""
import json
import os
from time import perf_counter
from collections import deque
from typing import List, Dict, Any, Tuple, Optional
import networkx as nx

from backend.app.services.geometry import haversine, point_in_polygon
from backend.app.services.road_network import RoadNetworkEngine
from backend.app.services.flood_engine import FloodSimulationEngine
from backend.app.services.assignment_optimizer import optimize_assignments


class EvacuationSolver:
    def __init__(
        self,
        road_engine: RoadNetworkEngine,
        data_dir: Optional[str] = None
    ):
        self.road_engine = road_engine
        if data_dir is None:
            data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
        self.data_dir = data_dir
        self.shelters: List[Dict[str, Any]] = []
        self.population_clusters: List[Dict[str, Any]] = []
        self._load_data()

    def _load_data(self):
        shelters_path = os.path.join(self.data_dir, "shelters.json")
        if os.path.exists(shelters_path):
            with open(shelters_path, "r", encoding="utf-8") as f:
                self.shelters = json.load(f)

        clusters_path = os.path.join(self.data_dir, "population_clusters.json")
        if os.path.exists(clusters_path):
            with open(clusters_path, "r", encoding="utf-8") as f:
                self.population_clusters = json.load(f)

    def _paths_to_shelters(self, graph, source, shelters):
        # Search only actual destinations instead of materializing paths to
        # every street in the city on every assignment iteration.
        paths = {}
        for shelter in shelters.values():
            target = shelter['nearest_node']
            if shelter['is_compromised'] or shelter['remaining_capacity'] <= 0 or not target:
                continue
            path = self.road_engine.find_astar_path(graph, source, target)
            if path is not None:
                paths[target] = path
        return paths

    def solve_evacuation(
        self,
        dynamic_graph: nx.DiGraph,
        step_zones_state: List[Dict[str, Any]],
        flood_engine: FloodSimulationEngine,
        selected_shelter_ids: Optional[List[str]] = None,
        planning_strategy: str = 'min_cost_flow',
        compare_baseline: bool = True,
        rescue_committed_by_cluster=None,
        rescue_reserved_by_shelter=None,
        rescue_arrived_by_shelter=None,
    ) -> Dict[str, Any]:
        """
        Solves capacity-constrained evacuee assignment and safe pathfinding.
        Returns:
            - evacuation_routes_geojson: FeatureCollection of LineStrings
            - shelter_allocations: List of shelter status objects
            - isolated_clusters: List of cut-off clusters requiring airlift
            - summary: evacuee numbers and metrics
        """
        baseline = None
        if planning_strategy == 'min_cost_flow' and compare_baseline:
            baseline = self.solve_evacuation(dynamic_graph.copy(), step_zones_state, flood_engine,
                                            selected_shelter_ids, 'greedy', False,
                                            rescue_committed_by_cluster, rescue_reserved_by_shelter, rescue_arrived_by_shelter)
        started = perf_counter()
        # Filter available shelters
        active_shelters = [
            dict(s) for s in self.shelters
            if selected_shelter_ids is None or s["id"] in selected_shelter_ids
        ]

        # Initialize shelter capacity tracking
        shelter_state = {}
        for s in active_shelters:
            sid = s["id"]
            lat, lon = s["location"]
            # Check if shelter itself is inundated
            s_depth = flood_engine.get_point_depth(lat, lon, step_zones_state)
            nearest_node = self.road_engine.find_nearest_node(lat, lon, mode="foot")
            is_compromised = (s_depth >= 0.50 or not nearest_node or not dynamic_graph.has_node(nearest_node) or dynamic_graph.degree(nearest_node) == 0
                or flood_engine.get_edge_depth(lat,lon,self.road_engine.nodes_data[nearest_node]["lat"],self.road_engine.nodes_data[nearest_node]["lon"],step_zones_state) >= .50)
            
            max_cap = s.get("capacity", 1000)
            baseline_occupied = min(max_cap, max(0, s.get("current_occupancy", 0)))
            reserved = (rescue_reserved_by_shelter or {}).get(sid, 0)
            arrived = (rescue_arrived_by_shelter or {}).get(sid, 0)
            avail_cap = max(0, max_cap - baseline_occupied - reserved)

            shelter_state[sid] = {
                "id": sid,
                "name": s["name"],
                "neighborhood": s.get("neighborhood", ""),
                "location": s["location"],
                "total_capacity": max_cap,
                "baseline_occupied": baseline_occupied,
                "rescue_reserved": reserved,
                "rescue_arrived": arrived,
                "newly_allocated": 0,
                "remaining_capacity": avail_cap,
                "is_compromised": is_compromised,
                "nearest_node": nearest_node,
                "status": "compromised" if is_compromised else "available",
            }

        # Initialize flow and base_time on dynamic graph for iterative assignment
        for u, v, d in dynamic_graph.edges(data=True):
            d["base_time"] = d.get("weight", 1.0)
            d["flow"] = 0.0

        evacuation_routes = []
        isolated_clusters = []
        total_affected_pop = 0
        total_evacuated_pop = 0

        # Process each population cluster
        active_demands = []
        completed_demands = []
        for c in self.population_clusters:
            cid = c["id"]
            c_name = c["name"]
            c_lat, c_lon = c["location"]
            total_pop = c["estimated_population"]

            # Determine flood depth at cluster centroid
            c_depth = flood_engine.get_point_depth(c_lat, c_lon, step_zones_state)

            # Evacuation demand rule
            if c_depth < 0.15:
                # No forced evacuation needed at this time step
                continue

            total_affected_pop += total_pop

            if c_depth >= 0.80:
                evac_ratio = 1.00
            elif c_depth >= 0.40:
                evac_ratio = 0.75
            else:
                evac_ratio = 0.35

            demand = max(0, int(total_pop * evac_ratio) - (rescue_committed_by_cluster or {}).get(cid, 0))
            if demand <= 0:
                continue

            c_node = self.road_engine.find_nearest_node(c_lat, c_lon, mode="foot")
            if (not c_node or not dynamic_graph.has_node(c_node) or dynamic_graph.degree(c_node) == 0
                or c_depth >= .50
                or flood_engine.get_edge_depth(c_lat,c_lon,self.road_engine.nodes_data[c_node]["lat"],self.road_engine.nodes_data[c_node]["lon"],step_zones_state) >= .50):
                # Cluster node is completely cut off from road network
                isolated_clusters.append({
                    "cluster_id": cid,
                    "name": c_name,
                    "location": [c_lat, c_lon],
                    "trapped_population": demand,
                    "requires_airlift": True,
                    "reason_code": "no_ground_access",
                    "reason": f"Cluster access road severed by deep flood {c_depth:.2f}m (requires boat/airlift rescue)",
                })
                continue

            req = {
                "cid": cid, "c_name": c_name, "c_lat": c_lat, "c_lon": c_lon,
                "c_node": c_node, "unassigned": demand, "c_depth": c_depth,
                "urgency_score": round(c_depth * 2.5 + (demand / 5000.0), 3),
                "route_agg": {}
            }
            active_demands.append(req)
            completed_demands.append(req)

        # Sort initial demands by Urgency Score descending (deepest flood & highest density first)
        active_demands.sort(key=lambda r: r["urgency_score"], reverse=True)

        quotas = None
        planner = {'algorithm': 'urgency_round_robin_greedy'}
        if planning_strategy == 'min_cost_flow':
            candidate_pairs = {}
            for demand in active_demands:
                paths = self._paths_to_shelters(dynamic_graph, demand['c_node'], shelter_state)
                options = []
                for sid, shelter in shelter_state.items():
                    if shelter['is_compromised'] or shelter['remaining_capacity'] <= 0 or shelter['nearest_node'] not in paths:
                        continue
                    path = paths[shelter['nearest_node']]
                    _, minutes = self.road_engine.get_route_metrics(dynamic_graph, path)
                    depth = max((dynamic_graph[u][v].get('water_depth_m', 0) for u, v in zip(path, path[1:])), default=0)
                    options.append({'shelter_id': sid, 'cost': max(0, round(minutes * 100 + depth * 2000))})
                candidate_pairs[demand['cid']] = options
            quotas, planner = optimize_assignments(active_demands, shelter_state, candidate_pairs)

        # Iterative assignment: dynamically re-route chunks to avoid congestion
        chunk_size = 2000
        active_demands = deque(active_demands)
        while active_demands:
            req = active_demands.popleft()

            # Find reachable shelters with available capacity dynamically based on updated weights
            candidates = []
            # Single-source search reaches all reachable shelters from req["c_node"]
            paths = self._paths_to_shelters(dynamic_graph, req["c_node"], shelter_state)
            for sid, s_info in shelter_state.items():
                if quotas is not None and quotas.get((req['cid'], sid), 0) <= 0:
                    continue
                if s_info["remaining_capacity"] <= 0 or s_info["status"] == "compromised":
                    continue

                s_node = s_info["nearest_node"]
                if not s_node or not dynamic_graph.has_node(s_node):
                    continue

                try:
                    if s_node not in paths:
                        continue
                    path = paths[s_node]
                    dist_km, time_min = self.road_engine.get_route_metrics(dynamic_graph, path)
                    candidates.append({
                        "shelter_id": sid,
                        "node_path": path,
                        "distance_km": dist_km,
                        "travel_time_min": time_min,
                    })
                except (nx.NetworkXNoPath, nx.NodeNotFound):
                    continue

            if not candidates:
                has_space = any(not s['is_compromised'] and s['remaining_capacity'] > 0 for s in shelter_state.values())
                isolated_clusters.append({
                    "cluster_id": req["cid"],
                    "name": req["c_name"],
                    "location": [req["c_lat"], req["c_lon"]],
                    "trapped_population": req["unassigned"],
                    "requires_airlift": True,
                    "reason_code": "no_reachable_shelter" if has_space else "no_safe_shelter_space",
                    "reason": "Remaining shelter spaces cannot be reached on modeled open roads." if has_space else "No dry, accessible shelter has remaining space.",
                })
                req["unassigned"] = 0
                continue

            # Sort by travel time ascending
            candidates.sort(key=lambda x: x["travel_time_min"])
            best_cand = candidates[0]

            sid = best_cand["shelter_id"]
            s_info = shelter_state[sid]
            alloc = min(req["unassigned"], s_info["remaining_capacity"], chunk_size)
            if quotas is not None:
                alloc = min(alloc, quotas[(req['cid'], sid)])
                quotas[(req['cid'], sid)] -= alloc

            if alloc <= 0:
                continue

            s_info["newly_allocated"] += alloc
            s_info["remaining_capacity"] -= alloc
            req["unassigned"] -= alloc
            total_evacuated_pop += alloc

            route_key = (sid, tuple(best_cand["node_path"]))
            if route_key not in req["route_agg"]:
                req["route_agg"][route_key] = {
                    "shelter_id": sid,
                    "node_path": best_cand["node_path"],
                    "distance_km": best_cand["distance_km"],
                    "travel_time_min": best_cand["travel_time_min"],
                    "alloc": 0,
                    "route_congested_time": best_cand["travel_time_min"]
                }
            
            req["route_agg"][route_key]["alloc"] += alloc

            # Iterative assignment: update graph flow and edge weights dynamically
            route_congested_time = 0.0
            for i in range(len(best_cand["node_path"]) - 1):
                u = best_cand["node_path"][i]
                v = best_cand["node_path"][i+1]
                if dynamic_graph.has_edge(u, v):
                    dynamic_graph.graph.setdefault("congested_edges",set()).add((u,v))
                    dynamic_graph[u][v]["flow"] += alloc
                    f = dynamic_graph[u][v]["flow"]
                    cap = dynamic_graph[u][v].get("capacity", 8000.0)
                    v_c_ratio = f / cap
                    bpr = min(5.0, 1.0 + 0.15 * (v_c_ratio ** 4))
                    dynamic_graph[u][v]["bpr_delay_factor"] = bpr
                    dynamic_graph[u][v]["weight"] = dynamic_graph[u][v]["base_time"] * bpr
                    route_congested_time += dynamic_graph[u][v]["weight"]

            if route_congested_time > 0:
                req["route_agg"][route_key]["route_congested_time"] = route_congested_time

            if req["unassigned"] > 0:
                active_demands.append(req)

        # Generate route objects for the aggregated paths
        route_idx = 1
        for req in completed_demands:
            cid = req["cid"]
            c_name = req["c_name"]
            c_lat = req["c_lat"]
            c_lon = req["c_lon"]
            c_depth = req["c_depth"]
            cluster_route_agg = req["route_agg"]

            for route_key, agg in cluster_route_agg.items():
                sid = agg["shelter_id"]
                s_info = shelter_state[sid]
                
                route_coords = self.road_engine.get_route_coordinates(agg["node_path"], dynamic_graph)
                raw_pts = route_coords + [s_info["location"]]
                if c_depth < 0.50:
                    raw_pts = [[c_lat, c_lon]] + raw_pts
                full_coords = []
                for pt in raw_pts:
                    if not full_coords or haversine(full_coords[-1][0], full_coords[-1][1], pt[0], pt[1]) > 0.000001:
                        full_coords.append(pt)

                # Differentiate ID if multiple paths to same shelter
                route_id = f"EVAC-{cid}-{sid}"
                if len([k for k in cluster_route_agg.keys() if k[0] == sid]) > 1:
                    route_id += f"-P{route_idx}"
                    route_idx += 1
                
                route_status = "rerouted" if c_depth >= 0.50 else ("warning" if c_depth >= 0.30 else "clear")
                bpr_delay_factor = round(agg["route_congested_time"] / max(0.1, agg["travel_time_min"]), 2)
                congested_time_min = round(agg["route_congested_time"], 1)

                evacuation_routes.append({
                    "route_id": route_id,
                    "source_cluster_id": cid,
                    "source_name": c_name,
                    "destination_shelter_id": sid,
                    "destination_name": s_info["name"],
                    "evacuee_count": agg["alloc"],
                    "distance_km": round(sum(haversine(*a,*b) for a,b in zip(full_coords,full_coords[1:])),3),
                    "estimated_time_min": round(agg["travel_time_min"] + sum(self.road_engine.route_provenance(route_coords,[c_lat,c_lon],s_info["location"])["access_connectors_m"])/1000/5*60,1),
                    "congested_time_min": congested_time_min,
                    "congestion_delay_factor": bpr_delay_factor,
                    "urgency_level": "critical" if c_depth >= 0.80 else ("high" if c_depth >= 0.40 else "moderate"),
                    "status": route_status,
                    "coordinates": full_coords,
                    "road_provenance": self.road_engine.route_provenance(route_coords, [c_lat,c_lon], s_info["location"]),
                })

        # Format shelter allocations response
        allocations_output = []
        for sid, s_info in shelter_state.items():
            alloc_evac = s_info["newly_allocated"]
            max_cap = s_info["total_capacity"]
            total_occupancy = s_info["baseline_occupied"] + alloc_evac + s_info['rescue_arrived']
            rem_cap = max(0, max_cap - s_info['baseline_occupied'] - alloc_evac - s_info['rescue_reserved'])
            utilization = total_occupancy / max(1, max_cap)

            if s_info["is_compromised"]:
                status = "compromised"
            elif utilization >= 1.0 or rem_cap == 0:
                status = "full"
            elif utilization >= 0.80:
                status = "near_capacity"
            else:
                status = "available"

            allocations_output.append({
                "shelter_id": sid,
                "id": sid,
                "name": s_info["name"],
                "neighborhood": s_info["neighborhood"],
                "location": s_info["location"],
                "total_capacity": max_cap,
                # Legacy aliases describe capacity available to this scenario.
                # total_capacity includes baseline residents; occupancy is separate.
                "capacity": max_cap - s_info["baseline_occupied"],
                "max_capacity": max_cap - s_info["baseline_occupied"],
                "allocated_evacuees": alloc_evac,
                "assigned_evacuees": alloc_evac,
                "total_occupancy": total_occupancy,
                "current_occupancy": s_info["baseline_occupied"] + s_info['rescue_arrived'],
                "rescue_arrived_population": s_info['rescue_arrived'],
                "rescue_pending_reservations": s_info['rescue_reserved'] - s_info['rescue_arrived'],
                "occupancy_pct": round(utilization * 100, 1),
                "occupancy": alloc_evac,
                "remaining_capacity": rem_cap,
                "status": status,
            })

        # Format GeoJSON FeatureCollection
        features = []
        for r in evacuation_routes:
            # Standard GeoJSON format: coordinates are [lon, lat]
            geojson_line = [[round(pt[1], 6), round(pt[0], 6)] for pt in r["coordinates"]]
            features.append({
                "type": "Feature",
                "id": r["route_id"],
                "geometry": {
                    "type": "LineString",
                    "coordinates": geojson_line,
                },
                "properties": {
                    **r.get("road_provenance", {}),
                    "route_id": r["route_id"],
                    "source_cluster_id": r["source_cluster_id"],
                    "source_name": r["source_name"],
                    "destination_shelter_id": r["destination_shelter_id"],
                    "shelter_id": r["destination_shelter_id"],
                    "assigned_shelter_id": r["destination_shelter_id"],
                    "destination_id": r["destination_shelter_id"],
                    "destination_name": r["destination_name"],
                    "evacuee_count": r["evacuee_count"],
                    "distance_km": r["distance_km"],
                    "estimated_time_min": r["estimated_time_min"],
                    "congested_time_min": r.get("congested_time_min", r["estimated_time_min"]),
                    "congestion_delay_factor": r.get("congestion_delay_factor", 1.0),
                    "urgency_level": r.get("urgency_level", "moderate"),
                    "status": r["status"],
                },
            })

        routes_geojson = {
            "type": "FeatureCollection",
            "features": features,
        }

        total_trapped = sum(ic["trapped_population"] for ic in isolated_clusters)
        total_person_km = sum(r["evacuee_count"] * r["distance_km"] for r in evacuation_routes)
        weighted_time = sum(r["evacuee_count"] * r["congested_time_min"] for r in evacuation_routes)
        avg_time_min = round(weighted_time / max(1, total_evacuated_pop), 1) if total_evacuated_pop > 0 else 0.0
        avg_bpr = round(
            sum(r["evacuee_count"] * r.get("congestion_delay_factor", 1.0) for r in evacuation_routes)
            / max(1, total_evacuated_pop), 2
        ) if total_evacuated_pop > 0 else 1.0
        compute_time_ms = round((perf_counter() - started) * 1000, 3)
        demand_population = total_evacuated_pop + total_trapped

        return {
            'planner': planner,
            'planner_comparison': None if baseline is None else {
                'baseline': baseline['metrics'],
                'optimized': {'total_evacuated_population': total_evacuated_pop,
                              'trapped_requiring_rescue': total_trapped,
                              'avg_travel_time_min': avg_time_min,
                              'total_person_km': round(total_person_km, 1),
                              'compute_time_ms': compute_time_ms},
                'baseline_method': 'Urgency-first greedy',
                'optimized_method': 'Capacity optimization (minimum-cost flow)',
                'scope': 'Same hour, flood-screened road graph, population demand, selected shelters and starting capacities. Supply allocations and rescue fleet are excluded.',
                'limitations': 'Fixed candidate paths; congestion is assessed after assignment. Lower travel cost and faster computation are not guaranteed. Timings are single-run solver measurements, excluding the other method and flood/supply calculations.',
                'additional_people_assigned': total_evacuated_pop - baseline['metrics']['total_evacuated_population'],
                'travel_time_change_min': round(avg_time_min - baseline['metrics']['avg_travel_time_min'], 2),
            },
            "evacuation_routes": routes_geojson,
            "shelter_allocations": allocations_output,
            "isolated_clusters": isolated_clusters,
            "metrics": {
                "total_affected_population": total_affected_pop,
                "evacuation_demand_population": demand_population,
                "not_requiring_evacuation_population": max(0, total_affected_pop - demand_population),
                "compute_time_ms": compute_time_ms,
                "total_evacuated_population": total_evacuated_pop,
                "trapped_requiring_rescue": total_trapped,
                "evacuation_efficiency_pct": round((total_evacuated_pop / max(1, total_affected_pop)) * 100.0, 1),
                "total_person_km": round(total_person_km, 1),
                "avg_travel_time_min": avg_time_min,
                "network_bpr_congestion_index": avg_bpr,
            },
        }
