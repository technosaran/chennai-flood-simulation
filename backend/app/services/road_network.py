"""
Chennai Road Network Graph Engine.
Loads offline road network into NetworkX, builds pure-Python spatial index,
and dynamically calculates flood impedance penalties and edge closures.
STRICT CONSTRAINT: No SciPy dependencies.
"""
import json
import gzip
import os
import math
from typing import Dict, Any, List, Tuple, Optional
import networkx as nx

from backend.app.services.geometry import (
    haversine,
    haversine_meters,
    SpatialGridIndex,
)
from backend.app.services.flood_engine import FloodSimulationEngine


class RoadNetworkEngine:
    def __init__(self, data_path: Optional[str] = None):
        if data_path is None:
            directory = os.path.join(os.path.dirname(__file__), "..", "data")
            imported = os.path.join(directory, "chennai_osm_roads.json.gz")
            use_osm = os.environ.get("USE_OSM_ROADS", "0") == "1"
            data_path = imported if (use_osm and os.path.exists(imported)) else os.path.join(directory, "chennai_roads.json")
        self.data_path = data_path
        self.base_graph = nx.DiGraph()
        self.nodes_data: Dict[str, Dict[str, Any]] = {}
        self.edges_data: Dict[str, Dict[str, Any]] = {}
        self.spatial_index = SpatialGridIndex(cell_size_km=2.0)
        self.flood_engine = FloodSimulationEngine()
        self._depth_signature = None
        self._edge_depths = {}
        self._snap_cache = {}
        self.metadata = {}
        self._graph_cache = {}
        self.load_network()

    def load_network(self):
        """Loads nodes and edges into NetworkX and spatial index."""
        if not os.path.exists(self.data_path):
            raise FileNotFoundError(f"Road network data file not found: {self.data_path}")

        opener = gzip.open if str(self.data_path).endswith('.gz') else open
        with opener(self.data_path, "rt", encoding="utf-8") as f:
            data = json.load(f)
        self.base_graph.clear()
        self.nodes_data.clear()
        self.edges_data.clear()
        self.spatial_index = SpatialGridIndex(cell_size_km=0.5)
        self._snap_cache.clear()
        self._graph_cache.clear()
        self._depth_signature = None
        self.metadata = data.get('metadata', {'source': 'Legacy simplified planning graph'})

        for node in data.get("nodes", []):
            nid = node["id"]
            self.nodes_data[nid] = node
            self.base_graph.add_node(nid, **node)
            self.spatial_index.insert(nid, node["lat"], node["lon"], node)

        for edge in data.get("edges", []):
            eid = edge["id"]
            src = edge["source"]
            tgt = edge["target"]
            dist_km = edge["distance_km"]
            speed_kmh = max(5, edge.get("speed_kmh", 40))
            # Base free-flow travel time in minutes
            base_time_min = (dist_km / speed_kmh) * 60.0

            edge_attr = {
                **edge,
                "base_time_min": base_time_min,
                "weight": base_time_min,
                "water_depth_m": 0.0,
                "is_closed": False,
            }
            coords = edge.get('geometry') or [[self.nodes_data[n]['lat'], self.nodes_data[n]['lon']] for n in (src,tgt)]
            edge_attr['geometry'] = coords
            edge_attr['bounds'] = (min(p[0] for p in coords), min(p[1] for p in coords), max(p[0] for p in coords), max(p[1] for p in coords))
            self.edges_data[eid] = edge_attr
            # Retain parallel OSM ways as alternatives instead of silently
            # overwriting a vehicle road with a footpath (or the reverse).
            old = self.base_graph.get_edge_data(src,tgt)
            variants = old['alternatives'] + [edge_attr] if old else [edge_attr]
            best = min(variants,key=lambda e:e['base_time_min'])
            self.base_graph.add_edge(src, tgt, **best, alternatives=variants)

    def find_nearest_node(self, lat: float, lon: float, mode: Optional[str] = None) -> Optional[str]:
        """Finds nearest road network node ID to (lat, lon)."""
        if self.metadata.get('osm_timestamp'):
            key = (lat,lon,mode)
            if key in self._snap_cache:return self._snap_cache[key]
            # A 3x3 search on 0.5 km cells contains the full 300 m snap disk
            # at Chennai's latitude. Never snap across kilometres of missing data.
            cell=self.spatial_index._get_key(lat,lon)
            candidates=[]
            for dx in (-1,0,1):
                for dy in (-1,0,1):
                    for item in self.spatial_index.cells.get((cell[0]+dx,cell[1]+dy),[]):
                        nid=item['id']
                        if nid not in self.base_graph:continue
                        if mode and not any(any(v.get(mode+'_allowed',True) for v in e.get('alternatives',[e]))
                                            for _,_,e in list(self.base_graph.out_edges(nid,data=True))+list(self.base_graph.in_edges(nid,data=True))):continue
                        dist=haversine_meters(lat,lon,item['lat'],item['lon'])
                        if dist<=300:candidates.append((dist,nid))
            result=min(candidates)[1] if candidates else None
            self._snap_cache[key]=result
            return result
        nearest = self.spatial_index.find_nearest(lat, lon)
        if nearest and nearest["id"] in self.nodes_data:
            return nearest["id"]
        # A replaced/subset graph must not route through stale spatial-index nodes.
        if self.nodes_data:
            return min(self.nodes_data, key=lambda nid: haversine_meters(
                lat, lon, self.nodes_data[nid]["lat"], self.nodes_data[nid]["lon"]
            ))
        return None

    def get_node(self, node_id: str) -> Optional[Dict[str, Any]]:
        return self.nodes_data.get(node_id)

    def get_route_coordinates(self, node_path: List[str], graph: Optional[nx.DiGraph] = None) -> List[List[float]]:
        """Expand the selected edges' surveyed map geometry, preserving curves."""
        graph = self.base_graph if graph is None else graph
        coords = []
        if len(node_path)==1:
            node=self.nodes_data[node_path[0]];return [[node['lat'],node['lon']]]
        for u,v in zip(node_path,node_path[1:]):
            if not graph.has_edge(u,v):raise ValueError(f'Route uses missing road edge {u} to {v}')
            edge=graph[u][v]
            points=edge.get('geometry') or [[self.nodes_data[n]['lat'],self.nodes_data[n]['lon']] for n in (u,v)]
            for point in points:
                if not coords or coords[-1]!=point:coords.append(list(point))
        return coords

    def route_provenance(self, coords, source, destination, mode='foot'):
        gaps=[haversine(*source,*coords[0])*1000,haversine(*coords[-1],*destination)*1000] if coords else []
        return {'network_source':self.metadata.get('source','Legacy simplified planning graph'),
                'network_timestamp':self.metadata.get('osm_timestamp'),
                'geometry_kind':'osm_streets' if self.metadata.get('osm_timestamp') else 'simplified_graph',
                'access_connectors_m':[round(x,1) for x in gaps],
                'access_note':'Straight access links to mapped streets are unverified; turn restrictions and live traffic are not modeled.'}

    def get_route_metrics(self, G: nx.DiGraph, node_path: List[str]) -> Tuple[float, float]:
        """Computes (total_distance_km, total_travel_time_min) along node path."""
        total_dist = 0.0
        total_time = 0.0
        for i in range(len(node_path) - 1):
            u, v = node_path[i], node_path[i + 1]
            if G.has_edge(u, v):
                edge_data = G[u][v]
                total_dist += edge_data.get("distance_km", 0.0)
                total_time += edge_data.get("weight", 0.0)
            else:
                raise ValueError(f'Cannot measure route through missing road edge {u} to {v}')
        return round(total_dist, 2), round(total_time, 1)

    def build_dynamic_graph(
        self,
        step_zones_state: List[Dict[str, Any]],
        closure_threshold_m: float = 0.50,
        slowdown_threshold_m: float = 0.10,
        is_amphibious: bool = False,
        mode: str = 'foot',
    ) -> nx.DiGraph:
        """
        Constructs a transient dynamic NetworkX graph with flood impedance weights.
        Roads with depth >= closure_threshold_m are marked closed (weight = inf or removed).
        Roads with slowdown_threshold_m <= depth < closure_threshold_m are penalized:
            weight = base_time * (1.0 + 8.0 * depth)
        Amphibious vehicles maintain steady pace in water.
        """
        # Keep separate mutable graphs for walking, trucks and amphibious
        # planning. Reuse their topology across timeline steps, resetting every
        # selected edge's weights so congestion never leaks into the next hour.
        cache_key = (mode,closure_threshold_m,slowdown_threshold_m,is_amphibious)
        G = self._graph_cache.get(cache_key)
        cached = G is not None
        if G is None:
            G = nx.DiGraph()
            G.add_nodes_from(self.base_graph.nodes(data=True))
            self._graph_cache[cache_key] = G
        for u,v in G.graph.pop('congested_edges',set()):
            if G.has_edge(u,v):G[u][v]['weight']=G[u][v].get('base_time',G[u][v]['weight'])
        signature = json.dumps(step_zones_state, sort_keys=True)
        if signature != self._depth_signature:
            self._depth_signature = signature
            self._edge_depths = {}

        zone_bounds=[]
        for z in step_zones_state:
            pts=z.get('polygon_latlon')
            if not pts and z.get('geometry'):
                pts=[[p[1],p[0]] for p in z['geometry'].get('coordinates',[[]])[0]]
            if pts:zone_bounds.append((min(p[0] for p in pts),min(p[1] for p in pts),max(p[0] for p in pts),max(p[1] for p in pts)))
            elif z.get('center'):
                lat,lon=z['center'];radius=float(z.get('current_radius',z.get('initial_radius',0)))/110000
                zone_bounds.append((lat-radius,lon-radius/math.cos(math.radians(lat)),lat+radius,lon+radius/math.cos(math.radians(lat))))
        eligible_count = G.graph.get('eligible_edges',0) if cached else 0
        previous_affected = G.graph.get('affected_edges',set())
        affected = set()
        if cached and not zone_bounds and not previous_affected:
            return G.copy().copy()
        for u, v, original in self.base_graph.edges(data=True):
          variants = original.get('alternatives',[original])
          overlaps = any(e.get('bounds',(-90,-180,90,180))[0]<=b[2] and e.get('bounds',(-90,-180,90,180))[2]>=b[0] and e.get('bounds',(-90,-180,90,180))[1]<=b[3] and e.get('bounds',(-90,-180,90,180))[3]>=b[1] for e in variants for b in zone_bounds)
          if overlaps:affected.add((u,v))
          if cached and not overlaps and (u,v) not in previous_affected:continue
          eligible=[]
          if not cached and any(v.get(mode+'_allowed',True) for v in variants):eligible_count += 1
          for variant in original.get('alternatives',[original]):
            if not variant.get(mode+'_allowed',True):continue
            data=dict(variant)
            coords=data.get('geometry') or [[self.nodes_data[n]['lat'],self.nodes_data[n]['lon']] for n in (u,v)]
            key=data.get('id') or (u,v,tuple(map(tuple,coords)))
            if key not in self._edge_depths:
                bounds=data.get('bounds') or (min(p[0] for p in coords),min(p[1] for p in coords),max(p[0] for p in coords),max(p[1] for p in coords))
                overlaps=any(bounds[0]<=b[2] and bounds[2]>=b[0] and bounds[1]<=b[3] and bounds[3]>=b[1] for b in zone_bounds)
                self._edge_depths[key]=max((self.flood_engine.get_edge_depth(*a,*b,step_zones_state,is_elevated=data.get('is_elevated',False)) for a,b in zip(coords,coords[1:])),default=0.0) if overlaps else 0.0
            depth=self._edge_depths[key]
            base_time = data.get("base_time_min", 1.0)
            if self.metadata.get('osm_timestamp') and mode=='foot':base_time=data['distance_km']/5*60
            data['base_time_min']=base_time
            data["water_depth_m"] = round(depth, 2)

            if depth >= closure_threshold_m:
                data["is_closed"] = True
                data["weight"] = float("inf")
                # Remove edge from reachable routing graph
                continue
            elif depth >= slowdown_threshold_m:
                data["is_closed"] = False
                if is_amphibious:
                    data["weight"] = base_time * 1.5
                else:
                    data["weight"] = base_time * (1.0 + 8.0 * depth)
            else:
                data["is_closed"] = False
                data["weight"] = base_time if not is_amphibious else base_time * 1.5
            eligible.append(data)
          if eligible:G.add_edge(u,v,**min(eligible,key=lambda e:e['weight']))
          elif G.has_edge(u,v):G.remove_edge(u,v)

        G.graph['flood_closed_edges'] = eligible_count - G.number_of_edges()
        G.graph['eligible_edges'] = eligible_count
        G.graph['affected_edges'] = affected
        G.graph['mode'] = mode
        return G.copy()

    def get_severed_roads_count(self, dynamic_graph: nx.DiGraph) -> int:
        """Returns number of road segments closed due to inundation."""
        return dynamic_graph.graph.get('flood_closed_edges', self.base_graph.number_of_edges() - dynamic_graph.number_of_edges())

    def find_astar_path(
        self, dynamic_graph: nx.DiGraph, source: str, target: str
    ) -> Optional[List[str]]:
        """
        Calculates exact shortest safe path using A* search with an admissible
        and consistent Haversine geographic heuristic (max assumed speed = 80 km/h).
        Guarantees optimal route with significantly fewer expanded nodes than Dijkstra.
        """
        if not dynamic_graph.has_node(source) or not dynamic_graph.has_node(target):
            return None

        target_node = self.nodes_data.get(target)
        if not target_node:
            return None
        t_lat, t_lon = target_node["lat"], target_node["lon"]
        max_speed_km_per_min = (5.0 if self.metadata.get('osm_timestamp') and dynamic_graph.graph.get('mode') == 'foot' else 80.0) / 60.0

        def heuristic(u: str, _v: str) -> float:
            u_node = self.nodes_data.get(u)
            if not u_node:
                return 0.0
            dist_km = haversine(u_node["lat"], u_node["lon"], t_lat, t_lon)
            return dist_km / max_speed_km_per_min

        try:
            return nx.astar_path(dynamic_graph, source, target, heuristic=heuristic, weight="weight")
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return None

    @staticmethod
    def compute_bpr_travel_time(
        base_time_min: float,
        flow: float,
        capacity: float = 8000.0,
        alpha: float = 0.15,
        beta: float = 4.0,
    ) -> float:
        """
        Bureau of Public Roads (BPR) volume-delay formulation:
        t = t_0 * (1 + alpha * (V / C)^beta)
        Models non-linear traffic congestion build-up on evacuation corridors.
        """
        if capacity <= 0:
            return base_time_min
        vc_ratio = max(0.0, flow / capacity)
        delay_factor = min(5.0, 1.0 + alpha * (vc_ratio ** beta))
        return base_time_min * delay_factor

    def find_critical_bridges(self, dynamic_graph: Optional[nx.DiGraph] = None) -> List[Tuple[str, str, Dict[str, Any]]]:
        """
        Detects topological bridge edges whose inundation disconnects the road network
        using Tarjan's bridge-finding algorithm on the undirected projection.
        """
        g = (dynamic_graph or self.base_graph).to_undirected()
        bridges = list(nx.bridges(g))
        critical_bridges = []
        for u, v in bridges:
            edge_attr = self.base_graph.get_edge_data(u, v, {})
            u_data = self.nodes_data.get(u, {})
            v_data = self.nodes_data.get(v, {})
            critical_bridges.append((u, v, {
                **edge_attr,
                "source_node": u_data,
                "target_node": v_data,
            }))
        return critical_bridges

    def detect_isolated_components(self, dynamic_graph: nx.DiGraph) -> List[List[str]]:
        """
        Identifies disconnected subgraphs / isolated island components
        in the dynamic flood road network.
        """
        undirected = dynamic_graph.to_undirected()
        return [list(c) for c in nx.connected_components(undirected)]
