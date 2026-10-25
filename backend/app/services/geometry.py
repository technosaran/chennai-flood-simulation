"""
Pure-Python Geospatial and Geometric Algorithms.
STRICT CONSTRAINT: No SciPy or GDAL dependencies.
All calculations use pure Python math and analytical geometry.
"""
import math
from typing import List, Tuple, Dict, Any, Optional

EARTH_RADIUS_KM = 6371.0
EARTH_RADIUS_M = 6371000.0
METERS_PER_DEGREE_LAT = 111320.0


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates geodesic distance between two points in kilometers."""
    if lat1 == lat2 and lon1 == lon2:
        return 0.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (math.sin(delta_phi / 2.0) ** 2 +
         math.cos(phi1) * math.cos(phi2) *
         math.sin(delta_lambda / 2.0) ** 2)
    c = 2.0 * math.atan2(math.sqrt(min(1.0, a)), math.sqrt(max(0.0, 1.0 - a)))
    return EARTH_RADIUS_KM * c


def haversine_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates geodesic distance between two points in meters."""
    return haversine(lat1, lon1, lat2, lon2) * 1000.0


def latlon_to_meters(lat: float, lon: float, ref_lat: float, ref_lon: float) -> Tuple[float, float]:
    """Projects lat/lon to local Cartesian meters relative to ref point."""
    y = (lat - ref_lat) * METERS_PER_DEGREE_LAT
    x = (lon - ref_lon) * METERS_PER_DEGREE_LAT * math.cos(math.radians(ref_lat))
    return x, y


def meters_to_latlon(x: float, y: float, ref_lat: float, ref_lon: float) -> Tuple[float, float]:
    """Converts local Cartesian meters back to lat/lon relative to ref point."""
    lat = ref_lat + (y / METERS_PER_DEGREE_LAT)
    lon = ref_lon + (x / (METERS_PER_DEGREE_LAT * math.cos(math.radians(ref_lat))))
    return lat, lon


def normalize_coordinate(coord: Any) -> Tuple[float, float]:
    """
    Normalizes a coordinate to (lat, lon).
    Auto-detects [lon, lat] vs [lat, lon] using geographic bounds.
    """
    if isinstance(coord, dict):
        lat = coord.get("lat", coord.get("latitude"))
        lon = coord.get("lon", coord.get("lng", coord.get("longitude")))
        if lat is not None and lon is not None:
            return float(lat), float(lon)
    if isinstance(coord, (list, tuple)) and len(coord) >= 2:
        c0, c1 = float(coord[0]), float(coord[1])
        # Auto-detect [lon, lat] where longitude is ~70-90 and latitude is ~5-35
        if (70.0 <= c0 <= 90.0) and (5.0 <= c1 <= 35.0):
            return c1, c0
        return c0, c1
    raise ValueError(f"Invalid coordinate format: {coord}")


def normalize_polygon_rings(polygon: Any) -> List[List[Tuple[float, float]]]:
    """
    Extracts and normalizes one or more polygon rings into list of [(lat, lon), ...] rings.
    Handles GeoJSON Feature, FeatureCollection, Polygon geometry, MultiPolygon, or raw lists.
    """
    if not polygon:
        return []

    # If GeoJSON FeatureCollection
    if isinstance(polygon, dict) and polygon.get("type") == "FeatureCollection":
        rings = []
        for feat in polygon.get("features", []):
            rings.extend(normalize_polygon_rings(feat))
        return rings

    # If GeoJSON Feature
    if isinstance(polygon, dict) and "geometry" in polygon:
        return normalize_polygon_rings(polygon["geometry"])

    # If GeoJSON Geometry
    if isinstance(polygon, dict):
        gtype = polygon.get("type", "")
        coords = polygon.get("coordinates", [])
        if gtype == "Polygon":
            return [[normalize_coordinate(pt) for pt in coords[0]]] if coords else []
        elif gtype == "MultiPolygon":
            return [[normalize_coordinate(pt) for pt in poly[0]] for poly in coords if poly]
        elif "coordinates" in polygon:
            return normalize_polygon_rings(polygon["coordinates"])

    # If raw list
    if isinstance(polygon, (list, tuple)):
        if len(polygon) == 0:
            return []
        # MultiPolygon: [[[[x, y], ...]]]]
        if (
            isinstance(polygon[0], (list, tuple))
            and len(polygon[0]) > 0
            and isinstance(polygon[0][0], (list, tuple))
            and len(polygon[0][0]) > 0
            and isinstance(polygon[0][0][0], (list, tuple))
        ):
            rings = []
            for poly in polygon:
                rings.extend(normalize_polygon_rings(poly))
            return rings
        # Polygon with rings: [[[x, y], ...]]
        if (
            isinstance(polygon[0], (list, tuple))
            and len(polygon[0]) > 0
            and isinstance(polygon[0][0], (list, tuple))
        ):
            rings = []
            for ring in polygon:
                norm_ring = [normalize_coordinate(pt) for pt in ring]
                if len(norm_ring) >= 3:
                    rings.append(norm_ring)
            return rings
        # Single ring: [[x, y], ...]
        if isinstance(polygon[0], (list, tuple)) and len(polygon[0]) >= 2:
            norm_ring = [normalize_coordinate(pt) for pt in polygon]
            return [norm_ring] if len(norm_ring) >= 3 else []

    return []


def segments_intersect(
    a_lat: float, a_lon: float,
    b_lat: float, b_lon: float,
    c_lat: float, c_lon: float,
    d_lat: float, d_lon: float
) -> bool:
    """
    Checks if segment AB intersects segment CD using 2D cross products.
    """
    # Quick bounding box rejection
    if max(a_lat, b_lat) < min(c_lat, d_lat) or max(c_lat, d_lat) < min(a_lat, b_lat):
        return False
    if max(a_lon, b_lon) < min(c_lon, d_lon) or max(c_lon, d_lon) < min(a_lon, b_lon):
        return False

    def ccw(x1, y1, x2, y2, x3, y3):
        return (y3 - y1) * (x2 - x1) - (x3 - x1) * (y2 - y1)

    cp1 = ccw(a_lat, a_lon, b_lat, b_lon, c_lat, c_lon)
    cp2 = ccw(a_lat, a_lon, b_lat, b_lon, d_lat, d_lon)
    cp3 = ccw(c_lat, c_lon, d_lat, d_lon, a_lat, a_lon)
    cp4 = ccw(c_lat, c_lon, d_lat, d_lon, b_lat, b_lon)

    # General case: straddle check
    if ((cp1 > 1e-12 and cp2 < -1e-12) or (cp1 < -1e-12 and cp2 > 1e-12)) and \
       ((cp3 > 1e-12 and cp4 < -1e-12) or (cp3 < -1e-12 and cp4 > 1e-12)):
        return True

    # Collinear / point on segment cases
    def on_segment(px, py, qx, qy, rx, ry):
        return (min(px, rx) - 1e-9 <= qx <= max(px, rx) + 1e-9 and
                min(py, ry) - 1e-9 <= qy <= max(py, ry) + 1e-9)

    if abs(cp1) <= 1e-12 and on_segment(a_lat, a_lon, c_lat, c_lon, b_lat, b_lon):
        return True
    if abs(cp2) <= 1e-12 and on_segment(a_lat, a_lon, d_lat, d_lon, b_lat, b_lon):
        return True
    if abs(cp3) <= 1e-12 and on_segment(c_lat, c_lon, a_lat, a_lon, d_lat, d_lon):
        return True
    if abs(cp4) <= 1e-12 and on_segment(c_lat, c_lon, b_lat, b_lon, d_lat, d_lon):
        return True

    return False


def point_in_polygon(lat: float, lon: float, polygon: Any) -> bool:
    """
    Determines if point (lat, lon) is inside or on the boundary of a polygon.
    Robustly handles all coordinate representations:
      - Raw [[lat, lon], ...] or [[lon, lat], ...]
      - GeoJSON Polygon coordinates [[[lon, lat], ...]]
      - GeoJSON Feature / Geometry dicts
      - MultiPolygon structures
      - Closed (first == last) and open rings
    """
    try:
        p_lat, p_lon = normalize_coordinate([lat, lon])
    except Exception:
        p_lat, p_lon = float(lat), float(lon)

    rings = normalize_polygon_rings(polygon)
    if not rings:
        return False

    for ring in rings:
        # Strip duplicate closing point if present for ray casting
        r = ring[:-1] if (
            len(ring) > 1
            and math.isclose(ring[0][0], ring[-1][0], abs_tol=1e-7)
            and math.isclose(ring[0][1], ring[-1][1], abs_tol=1e-7)
        ) else ring
        n = len(r)
        if n < 3:
            continue

        # Bounding box check for fast rejection
        lats = [pt[0] for pt in r]
        lons = [pt[1] for pt in r]
        if not (min(lats) - 1e-5 <= p_lat <= max(lats) + 1e-5 and
                min(lons) - 1e-5 <= p_lon <= max(lons) + 1e-5):
            continue

        # Point on boundary / vertex check
        for i in range(n):
            p1 = r[i]
            p2 = r[(i + 1) % n]
            dist_m = point_to_segment_distance_meters(p_lat, p_lon, p1[0], p1[1], p2[0], p2[1])
            if dist_m <= 3.0:  # within 3 meters of edge -> inside/on boundary
                return True

        # Ray-casting algorithm
        inside = False
        p1_lat, p1_lon = r[0]
        for i in range(1, n + 1):
            p2_lat, p2_lon = r[i % n]
            if min(p1_lon, p2_lon) < p_lon <= max(p1_lon, p2_lon):
                if p_lat <= max(p1_lat, p2_lat):
                    if p1_lon != p2_lon:
                        x_inters = (p_lon - p1_lon) * (p2_lat - p1_lat) / (p2_lon - p1_lon) + p1_lat
                    else:
                        x_inters = p1_lat
                    if p1_lat == p2_lat or p_lat <= x_inters:
                        inside = not inside
            p1_lat, p1_lon = p2_lat, p2_lon

        if inside:
            return True

    return False


def segment_intersects_polygon(p1: Any, p2: Any, polygon: Any) -> bool:
    """
    Analytically detects if line segment p1 -> p2 intersects or lies within any flood polygon.
    Returns True if:
      - p1 or p2 is inside or on the polygon
      - The segment intersects any boundary edge of the polygon
      - Any intermediate point along the segment lies inside the polygon
    """
    try:
        p1_lat, p1_lon = normalize_coordinate(p1)
        p2_lat, p2_lon = normalize_coordinate(p2)
    except Exception:
        return False

    rings = normalize_polygon_rings(polygon)
    if not rings:
        return False

    # Check endpoints first
    if point_in_polygon(p1_lat, p1_lon, polygon):
        return True
    if point_in_polygon(p2_lat, p2_lon, polygon):
        return True

    # Check midpoint and quarter points (in case segment cuts into or through polygon)
    mid_lat = (p1_lat + p2_lat) / 2.0
    mid_lon = (p1_lon + p2_lon) / 2.0
    if point_in_polygon(mid_lat, mid_lon, polygon):
        return True

    q1_lat = p1_lat + 0.25 * (p2_lat - p1_lat)
    q1_lon = p1_lon + 0.25 * (p2_lon - p1_lon)
    if point_in_polygon(q1_lat, q1_lon, polygon):
        return True

    q3_lat = p1_lat + 0.75 * (p2_lat - p1_lat)
    q3_lon = p1_lon + 0.75 * (p2_lon - p1_lon)
    if point_in_polygon(q3_lat, q3_lon, polygon):
        return True

    # Check boundary intersections
    seg_min_lat = min(p1_lat, p2_lat)
    seg_max_lat = max(p1_lat, p2_lat)
    seg_min_lon = min(p1_lon, p2_lon)
    seg_max_lon = max(p1_lon, p2_lon)

    for ring in rings:
        r = ring[:-1] if (
            len(ring) > 1
            and math.isclose(ring[0][0], ring[-1][0], abs_tol=1e-7)
            and math.isclose(ring[0][1], ring[-1][1], abs_tol=1e-7)
        ) else ring
        n = len(r)
        if n < 3:
            continue

        # Ring bounding box check
        lats = [pt[0] for pt in r]
        lons = [pt[1] for pt in r]
        if seg_max_lat < min(lats) or max(lats) < seg_min_lat:
            continue
        if seg_max_lon < min(lons) or max(lons) < seg_min_lon:
            continue

        for i in range(n):
            v1 = r[i]
            v2 = r[(i + 1) % n]
            if segments_intersect(p1_lat, p1_lon, p2_lat, p2_lon, v1[0], v1[1], v2[0], v2[1]):
                return True

    return False


def point_to_segment_distance_meters(
    p_lat: float, p_lon: float,
    a_lat: float, a_lon: float,
    b_lat: float, b_lon: float
) -> float:
    """
    Computes shortest distance in meters from point P to line segment AB.
    """
    px, py = latlon_to_meters(p_lat, p_lon, a_lat, a_lon)
    ax, ay = 0.0, 0.0
    bx, by = latlon_to_meters(b_lat, b_lon, a_lat, a_lon)

    abx = bx - ax
    aby = by - ay
    seg_len_sq = abx * abx + aby * aby

    if seg_len_sq == 0.0:
        return math.sqrt(px * px + py * py)

    # Project point onto segment
    t = max(0.0, min(1.0, (px * abx + py * aby) / seg_len_sq))
    proj_x = ax + t * abx
    proj_y = ay + t * aby

    dx = px - proj_x
    dy = py - proj_y
    return math.sqrt(dx * dx + dy * dy)


def create_circle_polygon(
    center_lat: float, center_lon: float, radius_meters: float, num_points: int = 32
) -> List[List[float]]:
    """
    Generates a regular N-sided polygon approximation of a circle.
    Returns list of [lat, lon] coordinates (closed ring: first == last).
    """
    points = []
    for i in range(num_points):
        theta = (2.0 * math.pi * i) / num_points
        dx = radius_meters * math.cos(theta)
        dy = radius_meters * math.sin(theta)
        lat, lon = meters_to_latlon(dx, dy, center_lat, center_lon)
        points.append([round(lat, 6), round(lon, 6)])
    points.append(points[0])  # Close ring
    return points


def dilate_polygon(polygon: List[List[float]], buffer_meters: float) -> List[List[float]]:
    """
    Expands a polygon outwards by buffer_meters.
    Coordinates are [[lat, lon], ...].
    Uses vertex outward displacement from polygon centroid.
    """
    if buffer_meters <= 0.0 or len(polygon) < 3:
        return [list(p) for p in polygon]

    # Remove duplicate closing point if present
    ring = polygon[:-1] if polygon[0] == polygon[-1] and len(polygon) > 1 else polygon[:]
    n = len(ring)
    if n < 3:
        return [list(p) for p in polygon]

    # Calculate centroid
    avg_lat = sum(p[0] for p in ring) / n
    avg_lon = sum(p[1] for p in ring) / n

    dilated_ring = []
    for p in ring:
        lat, lon = p[0], p[1]
        dist_from_center = haversine_meters(avg_lat, avg_lon, lat, lon)
        if dist_from_center < 1.0:
            # Fallback for degenerate vertex at centroid
            new_lat, new_lon = meters_to_latlon(buffer_meters, 0.0, lat, lon)
        else:
            scale = (dist_from_center + buffer_meters) / dist_from_center
            # Cartesian displacement relative to centroid
            x, y = latlon_to_meters(lat, lon, avg_lat, avg_lon)
            new_x = x * scale
            new_y = y * scale
            new_lat, new_lon = meters_to_latlon(new_x, new_y, avg_lat, avg_lon)
        dilated_ring.append([round(new_lat, 6), round(new_lon, 6)])

    dilated_ring.append(dilated_ring[0])  # Close ring
    return dilated_ring


class SpatialGridIndex:
    """
    Pure-Python Spatial Grid Index for sub-millisecond nearest neighbor search.
    Partitions the bounding box into grid cells.
    """
    def __init__(self, cell_size_km: float = 2.0):
        self.cell_size_deg = cell_size_km / 111.0
        self.cells: Dict[Tuple[int, int], List[Dict[str, Any]]] = {}
        self.all_items: List[Dict[str, Any]] = []

    def _get_key(self, lat: float, lon: float) -> Tuple[int, int]:
        return int(math.floor(lat / self.cell_size_deg)), int(math.floor(lon / self.cell_size_deg))

    def insert(self, item_id: str, lat: float, lon: float, data: Optional[Dict[str, Any]] = None):
        item = {
            "id": item_id,
            "lat": lat,
            "lon": lon,
            "data": data or {}
        }
        self.all_items.append(item)
        key = self._get_key(lat, lon)
        if key not in self.cells:
            self.cells[key] = []
        self.cells[key].append(item)

    def find_nearest(self, lat: float, lon: float) -> Optional[Dict[str, Any]]:
        """Finds the item with minimum Haversine distance to (lat, lon)."""
        if not self.all_items:
            return None

        key = self._get_key(lat, lon)
        best_item = None
        min_dist = float("inf")

        # Search neighboring grid cells: radius 1, then expand if empty
        search_radius = 1
        max_radius = 6

        while search_radius <= max_radius:
            candidates = []
            for dx in range(-search_radius, search_radius + 1):
                for dy in range(-search_radius, search_radius + 1):
                    cell_key = (key[0] + dx, key[1] + dy)
                    if cell_key in self.cells:
                        candidates.extend(self.cells[cell_key])

            if candidates:
                for candidate in candidates:
                    d = haversine(lat, lon, candidate["lat"], candidate["lon"])
                    if d < min_dist:
                        min_dist = d
                        best_item = candidate
                if best_item is not None:
                    return best_item

            search_radius += 1

        # Fallback to exhaustive linear search if outside indexed cells
        for item in self.all_items:
            d = haversine(lat, lon, item["lat"], item["lon"])
            if d < min_dist:
                min_dist = d
                best_item = item

        return best_item


def simplify_polyline_douglas_peucker(
    coords: List[List[float]], tolerance_meters: float = 5.0
) -> List[List[float]]:
    """
    Douglas-Peucker line simplification algorithm.
    Recursively decimates intermediate points that deviate less than tolerance_meters
    from the chord connecting the endpoints.
    """
    if len(coords) <= 2:
        return list(coords)

    # Find the point with the maximum perpendicular distance from the line segment
    first = coords[0]
    last = coords[-1]
    max_dist = 0.0
    index = 0

    for i in range(1, len(coords) - 1):
        pt = coords[i]
        d = point_to_segment_distance_meters(pt[0], pt[1], first[0], first[1], last[0], last[1])
        if d > max_dist:
            max_dist = d
            index = i

    # If max distance is greater than epsilon, recursively simplify
    if max_dist > tolerance_meters:
        left_simplified = simplify_polyline_douglas_peucker(coords[: index + 1], tolerance_meters)
        right_simplified = simplify_polyline_douglas_peucker(coords[index:], tolerance_meters)
        return left_simplified[:-1] + right_simplified
    else:
        return [first, last]


def compute_convex_hull(points: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
    """
    Computes the 2D Convex Hull of a set of points using Andrew's Monotone Chain algorithm.
    Time complexity: O(N log N). Returns vertices in counter-clockwise order.
    """
    pts = sorted(set(points))
    if len(pts) <= 2:
        return list(pts)

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    # Build lower hull
    lower = []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)

    # Build upper hull
    upper = []
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)

    # Concatenate lower and upper hulls (excluding duplicates at boundaries)
    return lower[:-1] + upper[:-1]


def polygon_area_sq_meters(coords: List[List[float]]) -> float:
    """
    Calculates spherical/planar projected area of a polygon ring using Green's Theorem / Shoelace Formula.
    Returns area in square meters.
    """
    if not coords or len(coords) < 3:
        return 0.0

    # Project to Cartesian meters relative to the first vertex
    ref_lat, ref_lon = coords[0][0], coords[0][1]
    projected = [latlon_to_meters(pt[0], pt[1], ref_lat, ref_lon) for pt in coords]

    area = 0.0
    n = len(projected)
    for i in range(n):
        j = (i + 1) % n
        area += projected[i][0] * projected[j][1] - projected[j][0] * projected[i][1]

    return abs(area) / 2.0


def polygon_centroid(coords: List[List[float]]) -> Tuple[float, float]:
    """
    Calculates center of mass / geometric centroid of a polygon ring.
    Returns (lat, lon).
    """
    if not coords:
        return (0.0, 0.0)
    if len(coords) < 3:
        return (coords[0][0], coords[0][1])

    ref_lat, ref_lon = coords[0][0], coords[0][1]
    projected = [latlon_to_meters(pt[0], pt[1], ref_lat, ref_lon) for pt in coords]

    signed_area = 0.0
    cx = 0.0
    cy = 0.0
    n = len(projected)

    for i in range(n):
        j = (i + 1) % n
        factor = (projected[i][0] * projected[j][1] - projected[j][0] * projected[i][1])
        signed_area += factor
        cx += (projected[i][0] + projected[j][0]) * factor
        cy += (projected[i][1] + projected[j][1]) * factor

    if abs(signed_area) < 1e-9:
        # Collinear or degenerate fallback: arithmetic mean
        return (sum(pt[0] for pt in coords) / n, sum(pt[1] for pt in coords) / n)

    signed_area *= 0.5
    cx /= (6.0 * signed_area)
    cy /= (6.0 * signed_area)

    return meters_to_latlon(cx, cy, ref_lat, ref_lon)
