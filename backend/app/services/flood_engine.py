"""
Spatio-Temporal Flood Spreading Engine.
Computes multi-stage radial buffer dilation, water depth decay,
and color-coded severity classification over time steps t=0..T (dt=1 hr).
Pure Python implementation without SciPy.
"""
import json
import os
from functools import lru_cache
from typing import List, Dict, Any, Tuple, Optional
from backend.app.services.geometry import (
    haversine_meters,
    point_in_polygon,
    segment_intersects_polygon,
    point_to_segment_distance_meters,
    create_circle_polygon,
    dilate_polygon,
    latlon_to_meters,
    meters_to_latlon,
)
from backend.app.models.disaster import FloodZoneInput, DisasterParameters

# Color styling constants according to specification
SEVERITY_STYLES = {
    "advisory": {
        "depth_min": 0.05,
        "depth_max": 0.30,
        "fill_color": "#FACC15",
        "stroke_color": "#CA8A04",
        "fill_opacity": 0.40,
    },
    "moderate": {
        "depth_min": 0.30,
        "depth_max": 0.60,
        "fill_color": "#FB923C",
        "stroke_color": "#EA580C",
        "fill_opacity": 0.55,
    },
    "severe": {
        "depth_min": 0.60,
        "depth_max": 1.20,
        "fill_color": "#EF4444",
        "stroke_color": "#B91C1C",
        "fill_opacity": 0.70,
    },
    "catastrophic": {
        "depth_min": 1.20,
        "depth_max": 99.0,
        "fill_color": "#7F1D1D",
        "stroke_color": "#450A0A",
        "fill_opacity": 0.85,
    },
}

# Real-world Chennai topography anchors (lat, lon, ground_elevation_m, runoff_coeff, basin_name)
CHENNAI_TOPOGRAPHIC_ANCHORS = [
    (13.0500, 80.2820, 2.0, 0.70, "Marina Coastline"),
    (13.0012, 80.2565, 2.5, 0.45, "Adyar Estuary"),
    (12.9796, 80.2185, 3.0, 0.80, "Velachery Lake Sink"),
    (12.9350, 80.2150, 2.2, 0.35, "Pallikaranai Marshland"),
    (13.0158, 80.2224, 4.5, 0.85, "Saidapet Adyar Basin"),
    (13.0220, 80.2410, 4.0, 0.80, "Kotturpuram Basin"),
    (12.9100, 80.0800, 4.8, 0.65, "Mudichur Flood Plain"),
    (13.1075, 80.2435, 3.8, 0.85, "Perambur North Basin"),
    (13.1235, 80.2085, 4.2, 0.75, "Retteri Lake Basin"),
    (13.0418, 80.2341, 9.0, 0.90, "T. Nagar High Density"),
    (13.0600, 80.2400, 10.5, 0.85, "Nungambakkam Commercial"),
    (13.0067, 80.2206, 14.0, 0.50, "Guindy Elevated Ridge"),
    (13.0020, 80.1980, 22.0, 0.60, "St. Thomas Mount Ridge"),
]

# Major drainage channel segments [[lat1, lon1], [lat2, lon2], channel_name]
CHENNAI_DRAINAGE_CORRIDORS = [
    ([12.980, 80.050], [13.005, 80.140], "Adyar River Upper"),
    ([13.005, 80.140], [13.0158, 80.2224], "Adyar River Saidapet"),
    ([13.0158, 80.2224], [13.022, 80.241], "Adyar River Kotturpuram"),
    ([13.022, 80.241], [13.001, 80.2565], "Adyar River Estuary"),
    ([13.065, 80.120], [13.072, 80.180], "Cooum River West"),
    ([13.072, 80.180], [13.078, 80.230], "Cooum River Central"),
    ([13.078, 80.230], [13.068, 80.285], "Cooum River Mouth"),
    ([13.200, 80.300], [13.100, 80.285], "Buckingham Canal North"),
    ([13.100, 80.285], [13.040, 80.270], "Buckingham Canal Central"),
    ([13.040, 80.270], [12.900, 80.235], "Buckingham Canal South"),
]


@lru_cache(maxsize=32768)
def get_topographic_context(lat: float, lon: float) -> Tuple[float, float, str, float]:
    """
    Inverse-distance weighted topographic interpolation for any Chennai location:
    Returns (elevation_m, runoff_coefficient, nearest_basin, distance_to_drainage_m)
    """
    total_w = 0.0
    weighted_elev = 0.0
    weighted_runoff = 0.0
    closest_basin = "General GCC Watershed"
    min_anchor_dist = float("inf")

    for a_lat, a_lon, elev, runoff, basin in CHENNAI_TOPOGRAPHIC_ANCHORS:
        d_m = haversine_meters(lat, lon, a_lat, a_lon)
        if d_m < min_anchor_dist:
            min_anchor_dist = d_m
            closest_basin = basin
        w = 1.0 / max(50.0, d_m) ** 1.5
        total_w += w
        weighted_elev += elev * w
        weighted_runoff += runoff * w

    interp_elev = round(weighted_elev / max(1e-6, total_w), 1)
    interp_runoff = round(weighted_runoff / max(1e-6, total_w), 2)

    # Calculate distance to nearest river or drainage corridor
    min_channel_dist = float("inf")
    for pt1, pt2, _ in CHENNAI_DRAINAGE_CORRIDORS:
        dist_seg = point_to_segment_distance_meters(lat, lon, pt1[0], pt1[1], pt2[0], pt2[1])
        if dist_seg < min_channel_dist:
            min_channel_dist = dist_seg

    return interp_elev, interp_runoff, closest_basin, round(min_channel_dist, 1)


def classify_severity(depth_m: float) -> Tuple[str, str, str, float]:
    """Returns (severity_level, fill_color, stroke_color, fill_opacity)."""
    if depth_m >= 1.20:
        sev = "catastrophic"
    elif depth_m >= 0.60:
        sev = "severe"
    elif depth_m >= 0.30:
        sev = "moderate"
    else:
        sev = "advisory"

    style = SEVERITY_STYLES[sev]
    return sev, style["fill_color"], style["stroke_color"], style["fill_opacity"]


class FloodSimulationEngine:
    def __init__(self, data_dir: Optional[str] = None):
        if data_dir is None:
            data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
        self.data_dir = data_dir
        self.presets: Dict[str, Dict[str, Any]] = {}
        self._load_presets()

    def _load_presets(self):
        presets_path = os.path.join(self.data_dir, "presets.json")
        if os.path.exists(presets_path):
            with open(presets_path, "r", encoding="utf-8") as f:
                items = json.load(f)
                for item in items:
                    self.presets[item["id"]] = item

    def resolve_flood_zones(
        self, raw_zones: List[FloodZoneInput], default_params: DisasterParameters
    ) -> List[Dict[str, Any]]:
        """
        Normalizes circle, polygon, and preset zones into concrete spatial descriptors.
        """
        resolved = []
        for idx, z in enumerate(raw_zones):
            zone_id = z.id or f"FZ-{idx+1:02d}"
            zone_type = z.type

            # Determine center if provided directly or within coordinates
            center = z.center
            if not center and z.coordinates:
                if len(z.coordinates) == 1 and isinstance(z.coordinates[0], (list, tuple)):
                    center = [float(z.coordinates[0][0]), float(z.coordinates[0][1])]
                elif len(z.coordinates) >= 2 and isinstance(z.coordinates[0], (int, float)):
                    center = [float(z.coordinates[0]), float(z.coordinates[1])]
                elif len(z.coordinates) >= 1 and zone_type == "circle":
                    center = [float(z.coordinates[0][0]), float(z.coordinates[0][1])]

            target_depth = z.initial_depth_m if z.initial_depth_m is not None else default_params.flood_depth_meters

            if zone_type == "preset" and z.preset_key and z.preset_key in self.presets:
                preset = self.presets[z.preset_key]
                resolved.append({
                    "id": zone_id,
                    "type": "circle",
                    "center": preset["center"],
                    "initial_radius": preset["radius_meters"],
                    "initial_depth": z.initial_depth_m if z.initial_depth_m is not None else preset["flood_depth_meters"],
                    "spread_rate": preset.get("spread_rate_meters_hr", default_params.spread_rate_meters_hr),
                })
            elif (zone_type == "circle" or (not zone_type and center)) and center:
                resolved.append({
                    "id": zone_id,
                    "type": "circle",
                    "center": center,
                    "initial_radius": z.radius_meters or 1500.0,
                    "initial_depth": target_depth,
                    "spread_rate": default_params.spread_rate_meters_hr,
                })
            elif zone_type == "polygon" and z.coordinates and len(z.coordinates) >= 3:
                # Calculate centroid
                coords = z.coordinates
                avg_lat = sum(c[0] for c in coords) / len(coords)
                avg_lon = sum(c[1] for c in coords) / len(coords)
                # Approximate initial radius as max distance to vertex
                max_r = max(haversine_meters(avg_lat, avg_lon, c[0], c[1]) for c in coords)
                resolved.append({
                    "id": zone_id,
                    "type": "polygon",
                    "center": [avg_lat, avg_lon],
                    "initial_coordinates": coords,
                    "initial_radius": max_r,
                    "initial_depth": target_depth,
                    "spread_rate": default_params.spread_rate_meters_hr,
                })
            elif center:  # Fallback if circle coordinates given
                resolved.append({
                    "id": zone_id,
                    "type": "circle",
                    "center": center,
                    "initial_radius": z.radius_meters or 1500.0,
                    "initial_depth": target_depth,
                    "spread_rate": default_params.spread_rate_meters_hr,
                })

        return resolved

    def compute_timeline(
        self,
        raw_zones: List[FloodZoneInput],
        params: DisasterParameters
    ) -> List[Dict[str, Any]]:
        """
        Computes flood progression across discrete time steps t=0..duration_hours.
        Returns list of time step descriptors with GeoJSON features and depth models.
        """
        resolved_zones = self.resolve_flood_zones(raw_zones, params)
        timeline = []
        elapsed = [i * params.time_step_hours for i in range(int(params.duration_hours / params.time_step_hours) + 1)]
        if elapsed[-1] < params.duration_hours:
            elapsed.append(float(params.duration_hours))

        for step, t_hours in enumerate(elapsed):
            features = []
            step_zones_state = []

            for rz in resolved_zones:
                # Dilation expansion distance
                # d_exp = v_spread * t * (intensity / 3.0)
                intensity_factor = max(0.5, params.rainfall_intensity_mm_hr / 65.0)
                d_exp = rz["spread_rate"] * t_hours * intensity_factor
                current_radius = rz["initial_radius"] + d_exp

                # Depth progression over time:
                # Begin at 10% of peak to include the early evacuation window.
                # Peak is reached at 60% of the modeled scenario duration.
                t_peak = max(1.0, params.duration_hours * 0.6)
                f_time = min(1.0, 0.1 + 0.9 * (t_hours / t_peak))
                peak_depth = rz["initial_depth"] * f_time

                # Generate multi-tier severity polygons matching hydrologic depth decay
                tiers = []
                # Full extent (advisory)
                tiers.append({
                    "sev": "advisory",
                    "depth": round(min(peak_depth, 0.25), 2),
                    "radius": current_radius,
                })

                # Moderate tier (>= 0.30m)
                if peak_depth >= 0.30:
                    r_mod = current_radius * max(0.35, 1.0 - (0.30 / peak_depth))
                    tiers.append({
                        "sev": "moderate",
                        "depth": round(min(peak_depth, 0.45), 2),
                        "radius": r_mod,
                    })

                # Severe tier (>= 0.60m)
                if peak_depth >= 0.60:
                    r_sev = current_radius * max(0.25, 1.0 - (0.50 / peak_depth))
                    tiers.append({
                        "sev": "severe",
                        "depth": round(min(peak_depth, 0.95), 2),
                        "radius": r_sev,
                    })

                # Catastrophic tier (>= 1.20m)
                if peak_depth >= 1.20:
                    r_cat = current_radius * max(0.15, 1.0 - (1.0 / peak_depth))
                    tiers.append({
                        "sev": "catastrophic",
                        "depth": round(peak_depth, 2),
                        "radius": r_cat,
                    })

                for tier_info in tiers:
                    if peak_depth <= 0:
                        continue
                    # Drawn polygons use a conservative uniform interior depth,
                    # exactly as routing does; terrain rays would distort this boundary.
                    if rz["type"] == "polygon":
                        if tier_info is not tiers[0]:
                            continue
                        severity, _, _, _ = classify_severity(peak_depth)
                        tier_info = {**tier_info, "sev": severity, "depth": round(peak_depth, 2)}
                    t_sev = tier_info["sev"]
                    t_depth = tier_info["depth"]
                    t_radius = tier_info["radius"]

                    # Topographic contouring
                    c_lat, c_lon = rz["center"]
                    c_elev, _, _, _ = get_topographic_context(c_lat, c_lon)
                    poly_latlon = []

                    if rz["type"] == "circle":
                        base_points = create_circle_polygon(c_lat, c_lon, t_radius, num_points=32)[:-1]
                    else:
                        d_exp_tier = max(0.0, d_exp * (t_radius / max(1.0, current_radius)))
                        base_points = dilate_polygon(rz["initial_coordinates"], d_exp_tier)[:-1]

                    import math
                    for pt in base_points if rz["type"] == "circle" else []:
                        # Ray from center to this nominal point
                        d_nominal = haversine_meters(c_lat, c_lon, pt[0], pt[1])
                        if d_nominal < 1.0:
                            poly_latlon.append(pt)
                            continue
                            
                        # Find the actual extent along this ray where depth >= t_depth
                        low = 0.0
                        high = d_nominal * 2.0  # Allow some expansion if terrain is low
                        best_lat, best_lon = c_lat, c_lon
                        
                        # Calculate angle
                        dx, dy = latlon_to_meters(pt[0], pt[1], c_lat, c_lon)
                        theta = math.atan2(dy, dx)
                        
                        for _ in range(8):
                            mid = (low + high) / 2.0
                            mdx = mid * math.cos(theta)
                            mdy = mid * math.sin(theta)
                            mlat, mlon = meters_to_latlon(mdx, mdy, c_lat, c_lon)
                            pt_elev, _, _, _ = get_topographic_context(mlat, mlon)
                            
                            decay = max(0.1, 1.0 - (mid / (current_radius + 1.0)))
                            base_depth = peak_depth * decay
                            d_r = max(0.0, base_depth + c_elev - pt_elev)
                            
                            if d_r >= t_depth:
                                best_lat, best_lon = mlat, mlon
                                low = mid
                            else:
                                high = mid
                                
                        poly_latlon.append([round(best_lat, 6), round(best_lon, 6)])
                    
                    if rz["type"] == "polygon":
                        poly_latlon = dilate_polygon(rz["initial_coordinates"], d_exp)
                    else:
                        poly_latlon.append(poly_latlon[0])  # Close ring

                    sev_style = SEVERITY_STYLES[t_sev]
                    geojson_coords = [[[round(pt[1], 6), round(pt[0], 6)] for pt in poly_latlon]]

                    elev_m, runoff_c, basin_n, dist_ch = get_topographic_context(rz["center"][0], rz["center"][1])
                    scs_runoff_mm = self.compute_scs_curve_number_runoff(
                        rainfall_mm=params.rainfall_intensity_mm_hr * max(1.0, t_hours),
                        curve_number=min(95.0, 70.0 + runoff_c * 25.0)
                    )
                    # Terrain slope estimated toward sea level (0m) over distance to drainage/coast
                    terrain_slope = max(0.0005, min(0.02, elev_m / max(500.0, dist_ch)))
                    velocity_ms = self.compute_mannings_flow_velocity(t_depth, slope_m_per_m=terrain_slope)
                    hazard_val, hazard_cat = self.compute_hazard_rating(t_depth, velocity_ms, is_urban=True)

                    features.append({
                        "type": "Feature",
                        "id": f"{rz['id']}_t{step}_{t_sev}",
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": geojson_coords,
                        },
                        "properties": {
                            "zone_id": rz["id"],
                            "time_step": step,
                            "time_elapsed_hours": t_hours,
                            "water_depth_m": t_depth,
                            "water_depth": t_depth,
                            "depth_meters": t_depth,
                            "depth": t_depth,
                            "radius_meters": round(t_radius, 1),
                            "severity": t_sev,
                            "severity_level": t_sev,
                            "ground_elevation_m": elev_m,
                            "runoff_coefficient": runoff_c,
                            "drainage_basin": basin_n,
                            "drainage_distance_m": dist_ch,
                            "scs_runoff_depth_mm": round(scs_runoff_mm, 1),
                            "flow_velocity_m_s": round(velocity_ms, 2),
                            "hazard_rating": round(hazard_val, 2),
                            "hazard_category": hazard_cat,
                            "fill_color": sev_style["fill_color"],
                            "stroke_color": sev_style["stroke_color"],
                            "fill_opacity": sev_style["fill_opacity"],
                        },
                    })

                step_zones_state.append({
                    "id": rz["id"],
                    "type": rz["type"],
                    "center": rz["center"],
                    "current_radius": current_radius,
                    "peak_depth": peak_depth,
                    "polygon_latlon": create_circle_polygon(rz["center"][0], rz["center"][1], current_radius, num_points=32) if rz["type"] == "circle" else dilate_polygon(rz["initial_coordinates"], d_exp),
                })

            timeline.append({
                "time_step": step,
                "time_elapsed_hours": t_hours,
                "flood_polygons": {
                    "type": "FeatureCollection",
                    "features": features,
                },
                "zones_state": step_zones_state,
            })

        return timeline

    def get_point_depth(self, lat: float, lon: float, step_zones_state: List[Dict[str, Any]]) -> float:
        """
        Calculates maximum flood depth at coordinate (lat, lon) given zones state at time step.
        Properly checks polygon boundaries and interiors so points inside or on polygons
        receive the full inundated flood depth.
        """
        max_depth = 0.0
        for z in step_zones_state:
            # Handle GeoJSON Feature representation
            if isinstance(z, dict) and "geometry" in z:
                feat_depth = float(z.get("properties", {}).get("depth_meters", z.get("properties", {}).get("water_depth_m", 0.0)))
                poly = z["geometry"].get("coordinates", [])
                if point_in_polygon(lat, lon, poly):
                    if feat_depth > max_depth:
                        max_depth = feat_depth
                continue

            peak_depth = float(z.get("peak_depth", z.get("water_depth_m", z.get("initial_depth", 0.0))))
            if peak_depth <= 0:
                continue
            poly = z.get("polygon_latlon")

            # Check polygon interior and boundary directly
            if z.get("type") != "circle" and poly:
                if point_in_polygon(lat, lon, poly):
                    max_depth = max(max_depth, peak_depth)
                continue

            # Radial distance check for circular zones or fallback
            c = z.get("center")
            if c:
                radius_m = float(z.get("current_radius", z.get("initial_radius", 0.0)))
                dist_m = haversine_meters(lat, lon, c[0], c[1])
                if dist_m <= radius_m:
                    decay = max(0.1, 1.0 - (dist_m / (radius_m + 1.0)))
                    center_elev, _, _, _ = get_topographic_context(c[0], c[1])
                    point_elev, _, _, _ = get_topographic_context(lat, lon)
                    depth = max(0.0, peak_depth * decay + center_elev - point_elev)
                    if depth > max_depth:
                        max_depth = depth

        return round(max_depth, 2)

    def get_edge_depth(
        self,
        lat1: float, lon1: float,
        lat2: float, lon2: float,
        step_zones_state: List[Dict[str, Any]],
        is_elevated: bool = False
    ) -> float:
        """
        Calculates maximum water depth along road edge (lat1, lon1) -> (lat2, lon2).
        Properly checks polygon boundaries and interiors using analytical segment-polygon
        intersection, so roads inside or intersecting polygons receive the full inundated flood depth.
        If road is elevated (e.g. flyover), surface flood < 1.5m is ignored.
        """
        max_edge_depth = 0.0
        mid_lat = (lat1 + lat2) / 2.0
        mid_lon = (lon1 + lon2) / 2.0

        for z in step_zones_state:
            # Handle GeoJSON Feature
            if isinstance(z, dict) and "geometry" in z:
                feat_depth = float(z.get("properties", {}).get("depth_meters", z.get("properties", {}).get("water_depth_m", 0.0)))
                poly = z["geometry"].get("coordinates", [])
                if segment_intersects_polygon([lat1, lon1], [lat2, lon2], poly):
                    if feat_depth > max_edge_depth:
                        max_edge_depth = feat_depth
                continue

            peak_depth = float(z.get("peak_depth", z.get("water_depth_m", z.get("initial_depth", 0.0))))
            poly = z.get("polygon_latlon")

            # Analytical segment-polygon intersection check
            if z.get("type") != "circle" and poly:
                if segment_intersects_polygon([lat1, lon1], [lat2, lon2], poly):
                    max_edge_depth = max(max_edge_depth, peak_depth)
                continue

            # Check point depths at endpoints and midpoint
            d1 = self.get_point_depth(lat1, lon1, [z])
            d2 = self.get_point_depth(lat2, lon2, [z])
            d_mid = self.get_point_depth(mid_lat, mid_lon, [z])
            point_max = max(d1, d2, d_mid)
            if point_max > max_edge_depth:
                max_edge_depth = point_max

            # Radial distance to center fallback
            c = z.get("center")
            if c:
                radius_m = float(z.get("current_radius", z.get("initial_radius", 0.0)))
                dist_to_seg = point_to_segment_distance_meters(
                    c[0], c[1], lat1, lon1, lat2, lon2
                )
                if dist_to_seg <= radius_m:
                    decay = max(0.1, 1.0 - (dist_to_seg / (radius_m + 1.0)))
                    depth = peak_depth * decay
                    if depth > max_edge_depth:
                        max_edge_depth = depth

        if is_elevated and max_edge_depth < 1.5:
            return 0.0

        return round(max_edge_depth, 2)

    @staticmethod
    def compute_scs_curve_number_runoff(
        rainfall_mm: float, curve_number: float = 85.0
    ) -> float:
        """
        Calculates direct surface runoff (Q in mm) using the USDA Soil Conservation
        Service Curve Number (SCS-CN) method.
        S = (25400 / CN) - 254 (potential max retention in mm)
        Ia = 0.2 * S (initial abstraction in mm)
        Q = (P - Ia)^2 / (P - Ia + S) for P > Ia, else 0
        """
        if rainfall_mm <= 0.0 or curve_number <= 0.0:
            return 0.0
        cn = max(30.0, min(98.0, curve_number))
        s_mm = (25400.0 / cn) - 254.0
        ia_mm = 0.2 * s_mm
        if rainfall_mm <= ia_mm:
            return 0.0
        runoff_mm = ((rainfall_mm - ia_mm) ** 2) / (rainfall_mm - ia_mm + s_mm)
        return round(max(0.0, runoff_mm), 2)

    @staticmethod
    def compute_mannings_flow_velocity(
        depth_m: float,
        slope_m_per_m: float = 0.001,
        manning_n: float = 0.030,
    ) -> float:
        """
        Estimates overland and street flow velocity (m/s) using Manning's equation:
        v = (1 / n) * (Rh)^(2/3) * (S_0)^(1/2)
        For wide shallow floodplains, hydraulic radius Rh ~= depth_m.
        """
        if depth_m <= 0.001 or slope_m_per_m <= 0.0:
            return 0.0
        n = max(0.015, min(0.08, manning_n))
        s = max(0.0001, min(0.10, slope_m_per_m))
        rh = depth_m
        v = (1.0 / n) * (rh ** (2.0 / 3.0)) * (s ** 0.5)
        # Cap realistic urban flood surge speed between 0.05 and 4.0 m/s
        return round(min(4.0, max(0.02, v)), 3)

    @staticmethod
    def compute_hazard_rating(
        depth_m: float,
        velocity_m_s: float,
        is_urban: bool = True,
    ) -> Tuple[float, str]:
        """
        Computes flood hazard rating (HR) and classification according to
        UK Defra / Environment Agency FD2320 guidelines:
        HR = d * (v + 0.5) + DF
        where DF (debris factor) = 0.5 (d <= 0.25m) or 1.0 (d > 0.25m) in urban areas.
        Returns: (hazard_rating_score, hazard_category)
        Categories:
          - 'low': Caution / Wading safe
          - 'moderate': Dangerous for some (children, elderly)
          - 'significant': Dangerous for most (people and vehicles)
          - 'extreme': Dangerous for all (life threat, building damage)
        """
        if depth_m <= 0.02:
            return 0.0, "safe"
        df = 1.0 if (is_urban and depth_m > 0.25) else (0.5 if depth_m > 0.1 else 0.0)
        hr = depth_m * (velocity_m_s + 0.5) + df
        if hr < 0.75:
            category = "low"
        elif hr < 1.25:
            category = "moderate"
        elif hr < 2.0:
            category = "significant"
        else:
            category = "extreme"
        return round(hr, 2), category

    def compute_hydrodynamic_hazard_context(
        self,
        lat: float,
        lon: float,
        depth_m: float,
        rainfall_intensity_mm_hr: float = 65.0,
    ) -> Dict[str, Any]:
        """
        Provides comprehensive hydrodynamic hazard evaluation for a coordinate.
        """
        elev, runoff_c, basin, dist_ch = get_topographic_context(lat, lon)
        slope = max(0.0005, min(0.02, elev / max(500.0, dist_ch)))
        v = self.compute_mannings_flow_velocity(depth_m, slope_m_per_m=slope)
        hr, cat = self.compute_hazard_rating(depth_m, v, is_urban=True)
        scs_q = self.compute_scs_curve_number_runoff(
            rainfall_mm=rainfall_intensity_mm_hr,
            curve_number=min(95.0, 70.0 + runoff_c * 25.0)
        )
        return {
            "ground_elevation_m": elev,
            "runoff_coefficient": runoff_c,
            "drainage_basin": basin,
            "drainage_distance_m": dist_ch,
            "estimated_slope": round(slope, 5),
            "flow_velocity_m_s": v,
            "scs_runoff_depth_mm": scs_q,
            "hazard_rating": hr,
            "hazard_category": cat,
        }
