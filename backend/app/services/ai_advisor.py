"""
AI Decision Support Service for Chennai Disaster Management.
Computes:
1. Critical Ward Vulnerability Index (ranking Chennai wards by multidimensional risk).
2. Casualty prevention & bottleneck warning indicators.
3. Optimal airlift drop zone coordinates for stranded/isolated clusters.
4. Real-time emergency broadcast advisories (Tamil & English bilingual alert bulletins).
Integrates MLPredictor gracefully with calibrated fallbacks.
STRICT CONSTRAINT: No SciPy dependencies. Pure Python mathematical algorithms.
"""
import math
import os
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime, timezone

from backend.app.services.geometry import (
    haversine,
    haversine_meters,
    point_in_polygon,
    segment_intersects_polygon,
)

# Chennai Greater Corporation (GCC) 15 Administrative Zones with hydrological metadata
CHENNAI_GCC_ZONES = [
    {
        "zone_number": 1,
        "zone_id": "GCC-ZONE-01",
        "name": "Zone 1 - Thiruvottiyur",
        "key_localities": ["Thiruvottiyur", "Wimco Nagar", "Tollgate", "Ernavoor"],
        "centroid": [13.1610, 80.3015],
        "base_elevation_m": 3.0,
        "runoff_coefficient": 0.75,
        "drainage_basin": "Buckingham Canal North & Bay Coast",
        "population": 290000,
        "density_per_sqkm": 14500,
        "baseline_vulnerability": 1.2,
    },
    {
        "zone_number": 2,
        "zone_id": "GCC-ZONE-02",
        "name": "Zone 2 - Manali",
        "key_localities": ["Manali", "Mathur", "CPCL Industrial Belt", "Kosapur"],
        "centroid": [13.1690, 80.2600],
        "base_elevation_m": 3.5,
        "runoff_coefficient": 0.70,
        "drainage_basin": "Kosasthalaiyar River Lower Basin",
        "population": 160000,
        "density_per_sqkm": 8000,
        "baseline_vulnerability": 1.5,
    },
    {
        "zone_number": 3,
        "zone_id": "GCC-ZONE-03",
        "name": "Zone 3 - Madhavaram",
        "key_localities": ["Madhavaram", "Puzhal Lake Perimeter", "Retteri North"],
        "centroid": [13.1480, 80.2310],
        "base_elevation_m": 4.5,
        "runoff_coefficient": 0.65,
        "drainage_basin": "Puzhal Surplus Channel",
        "population": 280000,
        "density_per_sqkm": 11000,
        "baseline_vulnerability": 1.3,
    },
    {
        "zone_number": 4,
        "zone_id": "GCC-ZONE-04",
        "name": "Zone 4 - Tondiarpet",
        "key_localities": ["Tondiarpet", "Korukkupet", "Vyasarpadi Lowlands"],
        "centroid": [13.1250, 80.2880],
        "base_elevation_m": 2.8,
        "runoff_coefficient": 0.85,
        "drainage_basin": "Captain Cotton Canal",
        "population": 410000,
        "density_per_sqkm": 28000,
        "baseline_vulnerability": 1.6,
    },
    {
        "zone_number": 5,
        "zone_id": "GCC-ZONE-05",
        "name": "Zone 5 - Royapuram",
        "key_localities": ["Royapuram", "George Town", "Central Station Area", "Harbor"],
        "centroid": [13.1050, 80.2920],
        "base_elevation_m": 2.5,
        "runoff_coefficient": 0.90,
        "drainage_basin": "Port Coastline & Central Nullahs",
        "population": 360000,
        "density_per_sqkm": 32000,
        "baseline_vulnerability": 1.4,
    },
    {
        "zone_number": 6,
        "zone_id": "GCC-ZONE-06",
        "name": "Zone 6 - Thiru Vi Ka Nagar",
        "key_localities": ["Perambur", "Jamalia", "Otteri", "Pattalam"],
        "centroid": [13.1075, 80.2435],
        "base_elevation_m": 3.8,
        "runoff_coefficient": 0.85,
        "drainage_basin": "Otteri Nullah Catchment",
        "population": 460000,
        "density_per_sqkm": 26000,
        "baseline_vulnerability": 1.5,
    },
    {
        "zone_number": 7,
        "zone_id": "GCC-ZONE-07",
        "name": "Zone 7 - Ambattur",
        "key_localities": ["Ambattur", "Padi", "Korattur Lake Basin", "Industrial Estate"],
        "centroid": [13.1140, 80.1550],
        "base_elevation_m": 7.5,
        "runoff_coefficient": 0.75,
        "drainage_basin": "Korattur Lake Overflow Channel",
        "population": 480000,
        "density_per_sqkm": 16000,
        "baseline_vulnerability": 1.1,
    },
    {
        "zone_number": 8,
        "zone_id": "GCC-ZONE-08",
        "name": "Zone 8 - Anna Nagar",
        "key_localities": ["Anna Nagar", "Koyambedu", "Arumbakkam", "Shenoy Nagar"],
        "centroid": [13.0850, 80.2150],
        "base_elevation_m": 8.0,
        "runoff_coefficient": 0.80,
        "drainage_basin": "Cooum River Central Corridor",
        "population": 440000,
        "density_per_sqkm": 22000,
        "baseline_vulnerability": 1.2,
    },
    {
        "zone_number": 9,
        "zone_id": "GCC-ZONE-09",
        "name": "Zone 9 - Teynampet / T. Nagar",
        "key_localities": ["T. Nagar", "Teynampet", "Mylapore", "Alwarpet", "Panagal Park"],
        "centroid": [13.0418, 80.2341],
        "base_elevation_m": 9.0,
        "runoff_coefficient": 0.90,
        "drainage_basin": "Mambalam Canal & Buckingham Canal",
        "population": 450000,
        "density_per_sqkm": 30000,
        "baseline_vulnerability": 1.7,
    },
    {
        "zone_number": 10,
        "zone_id": "GCC-ZONE-10",
        "name": "Zone 10 - Kodambakkam",
        "key_localities": ["Kodambakkam", "Vadapalani", "Ashok Nagar", "K.K. Nagar"],
        "centroid": [13.0480, 80.2180],
        "base_elevation_m": 7.0,
        "runoff_coefficient": 0.85,
        "drainage_basin": "Virugambakkam Canal & Adyar North",
        "population": 430000,
        "density_per_sqkm": 24000,
        "baseline_vulnerability": 1.4,
    },
    {
        "zone_number": 11,
        "zone_id": "GCC-ZONE-11",
        "name": "Zone 11 - Valasaravakkam",
        "key_localities": ["Valasaravakkam", "Porur", "Ramapuram", "Alapakkam"],
        "centroid": [13.0400, 80.1700],
        "base_elevation_m": 6.0,
        "runoff_coefficient": 0.70,
        "drainage_basin": "Porur Lake Surplus Channel",
        "population": 290000,
        "density_per_sqkm": 14000,
        "baseline_vulnerability": 1.3,
    },
    {
        "zone_number": 12,
        "zone_id": "GCC-ZONE-12",
        "name": "Zone 12 - Alandur / St. Thomas Mount",
        "key_localities": ["Alandur", "St. Thomas Mount", "Nanganallur", "Kathipara"],
        "centroid": [13.0030, 80.2010],
        "base_elevation_m": 12.0,
        "runoff_coefficient": 0.65,
        "drainage_basin": "Upper Adyar Basin",
        "population": 260000,
        "density_per_sqkm": 13000,
        "baseline_vulnerability": 1.1,
    },
    {
        "zone_number": 13,
        "zone_id": "GCC-ZONE-13",
        "name": "Zone 13 - Adyar / Kotturpuram",
        "key_localities": ["Saidapet", "Kotturpuram", "Adyar", "Gandhi Nagar", "Besant Nagar"],
        "centroid": [13.0158, 80.2224],
        "base_elevation_m": 4.0,
        "runoff_coefficient": 0.85,
        "drainage_basin": "Adyar River Estuary & Maraimalai Adigal Bridge",
        "population": 380000,
        "density_per_sqkm": 21000,
        "baseline_vulnerability": 1.9,
    },
    {
        "zone_number": 14,
        "zone_id": "GCC-ZONE-14",
        "name": "Zone 14 - Perungudi / Velachery",
        "key_localities": ["Velachery", "Perungudi", "Madipakkam", "Taramani"],
        "centroid": [12.9796, 80.2185],
        "base_elevation_m": 3.0,
        "runoff_coefficient": 0.80,
        "drainage_basin": "Velachery Lake Sink & Pallikaranai Outlet",
        "population": 390000,
        "density_per_sqkm": 19000,
        "baseline_vulnerability": 1.8,
    },
    {
        "zone_number": 15,
        "zone_id": "GCC-ZONE-15",
        "name": "Zone 15 - Sholinganallur / Pallikaranai",
        "key_localities": ["Pallikaranai Marsh", "Sholinganallur", "Medavakkam", "Semmancheri"],
        "centroid": [12.9050, 80.2250],
        "base_elevation_m": 2.2,
        "runoff_coefficient": 0.40,
        "drainage_basin": "Pallikaranai Wetland & Buckingham Canal South",
        "population": 320000,
        "density_per_sqkm": 9500,
        "baseline_vulnerability": 1.9,
    },
]

# Chennai Critical Infrastructure Nodes
CHENNAI_CRITICAL_INFRASTRUCTURE = [
    {
        "id": "INFRA-01",
        "name": "Rajiv Gandhi Govt General Hospital (RGGGH)",
        "type": "Apex Trauma Hospital",
        "location": [13.0805, 80.2790],
        "elevation_m": 4.2,
        "criticality": "Vital",
    },
    {
        "id": "INFRA-02",
        "name": "Adyar Cancer Institute & Relief Staging",
        "type": "Specialty Hospital",
        "location": [13.0067, 80.2450],
        "elevation_m": 3.8,
        "criticality": "Vital",
    },
    {
        "id": "INFRA-03",
        "name": "Saidapet Maraimalai Adigal Bridge",
        "type": "Arterial River Crossing",
        "location": [13.0150, 80.2220],
        "elevation_m": 4.5,
        "criticality": "Critical Chokepoint",
    },
    {
        "id": "INFRA-04",
        "name": "Kotturpuram River Bridge",
        "type": "Arterial River Crossing",
        "location": [13.0230, 80.2420],
        "elevation_m": 4.1,
        "criticality": "Critical Chokepoint",
    },
    {
        "id": "INFRA-05",
        "name": "Kathipara Grade Separator (Cloverleaf)",
        "type": "Strategic Highway Junction",
        "location": [13.0060, 80.2030],
        "elevation_m": 12.5,
        "criticality": "High Flow Corridor",
    },
    {
        "id": "INFRA-06",
        "name": "TANGEDCO 230kV Koyambedu Transmission Substation",
        "type": "Power Grid Substation",
        "location": [13.0670, 80.1900],
        "elevation_m": 7.0,
        "criticality": "Grid Backbone",
    },
    {
        "id": "INFRA-07",
        "name": "TANGEDCO 110kV Velachery GIS Substation",
        "type": "Power Grid Substation",
        "location": [12.9810, 80.2170],
        "elevation_m": 3.2,
        "criticality": "Grid Node (Flood Vulnerable)",
    },
]

# Designated High-Elevation / Clear Air Rescue Drop Zones across Chennai
CHENNAI_AIRLIFT_DROP_ZONES = [
    {
        "id": "AIR-DZ-01",
        "name": "Anna University Central Grounds / CEG Pavilion",
        "neighborhood": "Guindy / Adyar",
        "coordinates": [13.0125, 80.2355],
        "ground_elevation_m": 14.5,
        "clear_radius_m": 85.0,
        "landing_type": "Touchdown Landing Feasible",
        "suitability": "Primary Heavy Helicopter (Mi-17 / ALH Dhruv)",
    },
    {
        "id": "AIR-DZ-02",
        "name": "Jawaharlal Nehru Stadium Arena Pitch",
        "neighborhood": "Periamet / Central",
        "coordinates": [13.0838, 80.2764],
        "ground_elevation_m": 8.2,
        "clear_radius_m": 110.0,
        "landing_type": "Touchdown Landing Feasible",
        "suitability": "Primary Multi-Helicopter Hub",
    },
    {
        "id": "AIR-DZ-03",
        "name": "St. Thomas Mount Ridge Peak Grounds",
        "neighborhood": "Alandur / Mount",
        "coordinates": [13.0020, 80.1980],
        "ground_elevation_m": 24.0,
        "clear_radius_m": 65.0,
        "landing_type": "Touchdown Landing Feasible",
        "suitability": "High Elevation Storm-Free Helipad",
    },
    {
        "id": "AIR-DZ-04",
        "name": "IIT Madras Oval Field",
        "neighborhood": "Adyar / Guindy",
        "coordinates": [12.9915, 80.2337],
        "ground_elevation_m": 12.0,
        "clear_radius_m": 90.0,
        "landing_type": "Touchdown Landing Feasible",
        "suitability": "South Chennai Medical Airlift Center",
    },
    {
        "id": "AIR-DZ-05",
        "name": "Loyola College Cricket Grounds",
        "neighborhood": "Nungambakkam",
        "coordinates": [13.0645, 80.2338],
        "ground_elevation_m": 11.0,
        "clear_radius_m": 75.0,
        "landing_type": "Touchdown Landing Feasible",
        "suitability": "Central Chennai Emergency Heli-Drop",
    },
    {
        "id": "AIR-DZ-06",
        "name": "Tambaram Air Force Station (AFS) Apron",
        "neighborhood": "Tambaram / Mudichur",
        "coordinates": [12.9249, 80.1190],
        "ground_elevation_m": 18.0,
        "clear_radius_m": 160.0,
        "landing_type": "Touchdown Landing Feasible",
        "suitability": "IAF Master Staging Base",
    },
    {
        "id": "AIR-DZ-07",
        "name": "Velachery MRTS Elevated Station Concourse Roof",
        "neighborhood": "Velachery Basin",
        "coordinates": [12.9796, 80.2185],
        "ground_elevation_m": 16.5,
        "clear_radius_m": 35.0,
        "landing_type": "Winch Extraction / Drop Only",
        "suitability": "Direct Flood Inundation Aerial Winch",
    },
    {
        "id": "AIR-DZ-08",
        "name": "Retteri Elevated Junction Plaza",
        "neighborhood": "Kolathur / Retteri",
        "coordinates": [13.1235, 80.2085],
        "ground_elevation_m": 10.5,
        "clear_radius_m": 45.0,
        "landing_type": "Winch Extraction / Drop Only",
        "suitability": "North Chennai Aerial Winch Platform",
    },
    {
        "id": "AIR-DZ-09",
        "name": "Madras Race Course Center Green",
        "neighborhood": "Guindy Elevated",
        "coordinates": [13.0100, 80.2150],
        "ground_elevation_m": 12.0,
        "clear_radius_m": 130.0,
        "landing_type": "Touchdown Landing Feasible",
        "suitability": "Mass Casualty Air Evacuation Ground",
    },
]


class AIAdvisorService:
    """
    Production-grade AI Decision Support Engine for Chennai Disaster Operations.
    """

    def __init__(self, ml_predictor=None):
        self.ml_predictor = ml_predictor

    def compute_ward_vulnerability_index(
        self,
        step_zones_state: List[Dict[str, Any]],
        flood_engine,
        road_engine=None,
    ) -> List[Dict[str, Any]]:
        """
        Computes the Critical Ward Vulnerability Index (0-100) for all 15 Chennai GCC Zones.
        Ranks wards in descending order of risk using hydrologic depth, terrain elevation,
        impervious runoff coefficients, population density, and baseline vulnerability.
        """
        ranked_wards = []

        for z in CHENNAI_GCC_ZONES:
            c_lat, c_lon = z["centroid"]
            base_elev = z["base_elevation_m"]
            runoff = z["runoff_coefficient"]
            pop_density = z["density_per_sqkm"]
            base_vuln = z["baseline_vulnerability"]

            # Sample 5 spatial probes across the zone (centroid + 4 cardinal offsets ~800m)
            delta = 0.007  # approx 780m
            sample_points = [
                [c_lat, c_lon],
                [c_lat + delta, c_lon],
                [c_lat - delta, c_lon],
                [c_lat, c_lon + delta],
                [c_lat, c_lon - delta],
            ]

            depths = [flood_engine.get_point_depth(pt[0], pt[1], step_zones_state) for pt in sample_points]
            mean_depth = sum(depths) / len(depths)
            peak_depth = max(depths)

            # Hydrologic depth factor: (depth / 2.0m) * 45 points max
            d_score = min(45.0, (peak_depth / 2.0) * 45.0)

            # Topographic elevation penalty: lower ground (< 4m) gets higher risk (up to 15 points)
            elev_score = max(0.0, (15.0 - base_elev) * 1.0)
            elev_score = min(15.0, elev_score)

            # Impervious surface & runoff factor (up to 15 points)
            runoff_score = (runoff / 0.90) * 15.0

            # Density & base vulnerability factor (up to 25 points)
            pop_score = min(25.0, ((pop_density / 30000.0) * 15.0) + (base_vuln * 5.0))

            composite_index = round(min(100.0, d_score + elev_score + runoff_score + pop_score), 1)

            # Categorize Risk Level
            if composite_index >= 75.0 or peak_depth >= 1.20:
                risk_tier = "CRITICAL"
                badge_color = "#DC2626"
            elif composite_index >= 50.0 or peak_depth >= 0.60:
                risk_tier = "HIGH"
                badge_color = "#EA580C"
            elif composite_index >= 25.0 or peak_depth >= 0.20:
                risk_tier = "MODERATE"
                badge_color = "#CA8A04"
            else:
                risk_tier = "LOW"
                badge_color = "#16A34A"

            # Tactical recommendation
            if risk_tier == "CRITICAL":
                rec_en = f"Mandatory immediate vertical/boat evacuation. Water level peaked at {peak_depth:.2f}m. Pre-position NDRF boat teams and deploy drone life-buoy drops."
                rec_ta = f"உடனடி கட்டாய வெளியேற்றம் தேவை. நீர்மட்டம் {peak_depth:.2f}மீ எட்டியுள்ளது. NDRF படகு மீட்புக் குழுக்கள் உடனடியாக களம் இறக்கப்பட வேண்டும்."
            elif risk_tier == "HIGH":
                rec_en = f"High alert. Deep water encroachment ({peak_depth:.2f}m). Reroute surface traffic away from low-lying arterial bridges and mobilize relief staging."
                rec_ta = f"உயர் எச்சரிக்கை. நீர்மட்டம் {peak_depth:.2f}மீ. தாழ்வான பாலங்களில் போக்குவரத்தை மாற்றி நிவாரண முகாம்களை தயார் நிலையில் வைக்கவும்."
            elif risk_tier == "MODERATE":
                rec_en = f"Water logging alert ({peak_depth:.2f}m). Deploy high-capacity dewatering diesel pumps and clear storm-water drain clogs."
                rec_ta = f"நீர் தேக்க எச்சரிக்கை ({peak_depth:.2f}மீ). அதிக திறன் கொண்ட டீசல் மோட்டார்கள் மூலம் மழைநீர் வடிகால் தடைகளை அகற்றவும்."
            else:
                rec_en = f"Normal vigilance ({peak_depth:.2f}m). Monitor upstream lake surplus discharge corridors."
                rec_ta = f"இயல்பு கண்காணிப்பு ({peak_depth:.2f}மீ). ஏரி உபரி நீர் கால்வாய் போக்கினை தொடர்ந்து கண்காணிக்கவும்."

            ranked_wards.append({
                "zone_number": z["zone_number"],
                "zone_id": z["zone_id"],
                "zone_name": z["name"],
                "key_localities": z["key_localities"],
                "centroid": z["centroid"],
                "ground_elevation_m": base_elev,
                "runoff_coefficient": runoff,
                "drainage_basin": z["drainage_basin"],
                "population": z["population"],
                "density_per_sqkm": pop_density,
                "peak_flood_depth_m": round(peak_depth, 2),
                "mean_flood_depth_m": round(mean_depth, 2),
                "vulnerability_index": composite_index,
                "risk_tier": risk_tier,
                "badge_color": badge_color,
                "recommendation_en": rec_en,
                "recommendation_ta": rec_ta,
            })

        # Calculate TOPSIS Multi-Criteria Decision Analysis scores across the 15 wards
        topsis_matrix = []
        for w in ranked_wards:
            topsis_matrix.append([
                w["peak_flood_depth_m"],
                w["mean_flood_depth_m"],
                w["density_per_sqkm"],
                w["runoff_coefficient"],
                w["ground_elevation_m"],
            ])
        # Criteria weights: [Peak Depth: 0.35, Mean Depth: 0.20, Density: 0.20, Runoff: 0.15, Elevation: 0.10]
        weights = [0.35, 0.20, 0.20, 0.15, 0.10]
        # Benefit criteria (True) vs Cost criteria (False: lower elevation = higher hazard)
        is_benefit = [True, True, True, True, False]
        topsis_scores = self.compute_topsis_scores(topsis_matrix, weights, is_benefit)
        for idx, score in enumerate(topsis_scores):
            ranked_wards[idx]["topsis_closeness_score"] = score

        # Sort descending by vulnerability index
        ranked_wards.sort(key=lambda x: x["vulnerability_index"], reverse=True)
        for idx, item in enumerate(ranked_wards):
            item["vulnerability_rank"] = idx + 1

        return ranked_wards

    @staticmethod
    def compute_topsis_scores(
        matrix: List[List[float]],
        weights: List[float],
        is_benefit: List[bool],
    ) -> List[float]:
        """
        Technique for Order of Preference by Similarity to Ideal Solution (TOPSIS).
        Pure Python multi-criteria decision making algorithm.
        Returns closeness coefficient C_i in [0.0, 1.0] for each alternative.
        """
        if not matrix or not matrix[0]:
            return []

        m = len(matrix)
        n = len(weights)

        # 1. Vector normalization
        col_norms = []
        for j in range(n):
            sum_sq = sum(matrix[i][j] ** 2 for i in range(m))
            col_norms.append(math.sqrt(sum_sq) if sum_sq > 0 else 1.0)

        # 2. Weighted normalized matrix
        v = [[(matrix[i][j] / col_norms[j]) * weights[j] for j in range(n)] for i in range(m)]

        # 3. Determine ideal positive (A+) and ideal negative (A-) solutions
        a_pos = []
        a_neg = []
        for j in range(n):
            vals = [v[i][j] for i in range(m)]
            if is_benefit[j]:
                a_pos.append(max(vals))
                a_neg.append(min(vals))
            else:
                a_pos.append(min(vals))
                a_neg.append(max(vals))

        # 4. Calculate Euclidean distances to ideal solutions and closeness coefficient
        closeness_scores = []
        for i in range(m):
            d_pos = math.sqrt(sum((v[i][j] - a_pos[j]) ** 2 for j in range(n)))
            d_neg = math.sqrt(sum((v[i][j] - a_neg[j]) ** 2 for j in range(n)))
            total_d = d_pos + d_neg
            c_i = (d_neg / total_d) if total_d > 0 else 0.5
            closeness_scores.append(round(c_i, 3))

        return closeness_scores

    def compute_casualty_prevention_indicators(
        self,
        dynamic_graph,
        step_zones_state: List[Dict[str, Any]],
        isolated_clusters: List[Dict[str, Any]],
        shelter_allocations: List[Dict[str, Any]],
        flood_engine,
    ) -> Dict[str, Any]:
        """
        Evaluates active system bottlenecks, critical infrastructure threats,
        and stranded population traps to generate life-saving casualty prevention directives.
        """
        bottleneck_roads = []
        infrastructure_threats = []
        stranded_traps = []

        # 1. Critical Infrastructure Vulnerability Checks
        for infra in CHENNAI_CRITICAL_INFRASTRUCTURE:
            i_lat, i_lon = infra["location"]
            water_depth = flood_engine.get_point_depth(i_lat, i_lon, step_zones_state)

            if water_depth >= 0.15:
                status = "COMPROMISED" if water_depth >= 0.60 else "THREATENED"
                infrastructure_threats.append({
                    "id": infra["id"],
                    "name": infra["name"],
                    "type": infra["type"],
                    "location": infra["location"],
                    "water_depth_m": round(water_depth, 2),
                    "status": status,
                    "mitigation": (
                        f"Deploy mobile generator dykes and sandbag barriers. "
                        f"Water depth {water_depth:.2f}m threatens critical backup utilities."
                    ),
                })

        # 2. Road Network Bottlenecks
        if dynamic_graph:
            for u, v, d in dynamic_graph.edges(data=True):
                depth = d.get("water_depth_m", 0.0)
                bpr = d.get("bpr_delay_factor", 1.0)
                flow = d.get("flow", 0.0)
                if (depth >= 0.20 and depth < 0.50) or bpr >= 1.8:
                    bottleneck_roads.append({
                        "source_node": u,
                        "target_node": v,
                        "water_depth_m": depth,
                        "delay_factor": round(bpr, 2),
                        "estimated_flow_evacuees": int(flow),
                        "directive": "Immediate traffic diversion required to prevent vehicle stalling and gridlock.",
                    })

        # Limit bottleneck roads to top 5 most severe
        bottleneck_roads.sort(key=lambda x: (x["water_depth_m"], x["delay_factor"]), reverse=True)
        bottleneck_roads = bottleneck_roads[:5]

        # 3. Stranded Population Traps
        total_trapped = 0
        for ic in isolated_clusters:
            pop = ic.get("trapped_population", 0)
            loc = ic.get("location", [13.0, 80.2])
            depth = flood_engine.get_point_depth(loc[0], loc[1], step_zones_state)
            total_trapped += pop

            urgency = "CRITICAL" if depth >= 0.80 else ("HIGH" if depth >= 0.40 else "MODERATE")
            stranded_traps.append({
                "cluster_id": ic.get("cluster_id", "UNK"),
                "name": ic.get("name", "Unknown Area"),
                "location": loc,
                "trapped_population": pop,
                "water_depth_m": round(depth, 2),
                "urgency": urgency,
                "time_to_criticality_hours": round(max(1.0, 8.0 - (depth * 3.0)), 1),
                "rescue_protocol": (
                    "Immediate Helicopter Winch / Amphibious Boat Rescue Required"
                    if depth >= 0.50
                    else "High-Axle Truck Convoy with NDRF escort"
                ),
            })

        # 4. Master Directives for Command Center
        directives = [
            {
                "priority": "P1 - CRITICAL",
                "action": "Immediate Vertical Evacuation Order",
                "details": f"Move {total_trapped:,} stranded residents across {len(isolated_clusters)} isolated basins to upper floors and designated helipads.",
            },
            {
                "priority": "P2 - HIGH",
                "action": "Infrastructure Sandbag Ring Deployment",
                "details": f"Shield {len(infrastructure_threats)} threatened hospitals and power stations with portable flood dams.",
            },
            {
                "priority": "P3 - MEDIUM",
                "action": "Dynamic Traffic Chokepoint Diversion",
                "details": f"Divert civilian traffic around {len(bottleneck_roads)} flooded arterial road sections.",
            },
        ]
        directives = [directive for directive, relevant in zip(
            directives, (total_trapped > 0, bool(infrastructure_threats), bool(bottleneck_roads))
        ) if relevant]

        return {
            "total_stranded_citizens": total_trapped,
            "isolated_zones_count": len(isolated_clusters),
            "threatened_infrastructure_count": len(infrastructure_threats),
            "infrastructure_threats": infrastructure_threats,
            "chokepoints_and_bottlenecks": bottleneck_roads,
            "stranded_population_traps": stranded_traps,
            "preventative_directives": directives,
        }

    def compute_optimal_airlift_drop_zones(
        self,
        isolated_clusters: List[Dict[str, Any]],
        step_zones_state: List[Dict[str, Any]],
        flood_engine,
    ) -> List[Dict[str, Any]]:
        """
        Computes optimal airlift drop zones for all stranded/isolated clusters.
        Selects highest-elevation, unflooded drop coordinates with exact GPS coordinates,
        payload cargo recommendations, and helicopter landing feasibility.
        """
        assigned_airlifts = []

        for cluster in isolated_clusters:
            c_lat, c_lon = cluster["location"]
            trapped_pop = cluster.get("trapped_population", 1000)

            best_dz = None
            min_dist_km = float("inf")

            for dz in CHENNAI_AIRLIFT_DROP_ZONES:
                dz_lat, dz_lon = dz["coordinates"]
                # Check if drop zone itself is dry
                dz_flood_depth = flood_engine.get_point_depth(dz_lat, dz_lon, step_zones_state)
                if dz_flood_depth >= 0.10:
                    continue  # Submerged drop zone rejected

                d_km = haversine(c_lat, c_lon, dz_lat, dz_lon)
                if d_km < min_dist_km:
                    min_dist_km = d_km
                    best_dz = dz

            # Never recommend a submerged site just because it is elevated.
            if not best_dz:
                assigned_airlifts.append({
                    "cluster_id": cluster.get("cluster_id", "UNK"),
                    "cluster_name": cluster.get("name", "Unknown Area"),
                    "stranded_population": trapped_pop,
                    "assigned_drop_zone_id": None,
                    "drop_zone_coordinates": None,
                    "status": "no_safe_drop_zone",
                    "reason": "All modeled drop zones are inundated; field assessment is required.",
                })
                continue

            flight_time_min = round((min_dist_km / 140.0) * 60.0 + 3.0, 1)  # 140 km/h cruising + 3 min hover

            # Determine payload kit
            water_bottles = trapped_pop * 4  # 4L emergency water
            mre_rations = trapped_pop * 2    # 2 high-calorie MRE packs
            trauma_kits = max(10, int(trapped_pop * 0.03))

            assigned_airlifts.append({
                "status": "modeled_option",
                "cluster_id": cluster.get("cluster_id", "UNK"),
                "cluster_name": cluster.get("name", "Unknown Area"),
                "cluster_location": [c_lat, c_lon],
                "stranded_population": trapped_pop,
                "assigned_drop_zone_id": best_dz["id"],
                "drop_zone_name": best_dz["name"],
                "drop_zone_coordinates": best_dz["coordinates"],
                "ground_elevation_m": best_dz["ground_elevation_m"],
                "distance_km": round(min_dist_km, 2),
                "estimated_flight_transit_min": flight_time_min,
                "landing_type": best_dz["landing_type"],
                "air_asset_suitability": best_dz["suitability"],
                "recommended_air_payload": {
                    "water_litres": water_bottles,
                    "emergency_mre_rations": mre_rations,
                    "trauma_medical_kits": trauma_kits,
                    "satellite_comm_radios": max(2, int(trapped_pop / 1500)),
                },
                "sortie_frequency_hours": 2 if trapped_pop > 5000 else 4,
            })

        return assigned_airlifts

    def generate_bilingual_emergency_broadcasts(
        self,
        overall_severity: str,
        top_vulnerable_wards: List[Dict[str, Any]],
        peak_observed_depth: float,
        total_stranded: int,
    ) -> Dict[str, Any]:
        """
        Generates authentic Tamil (தமிழ்) and English bilingual alert bulletins
        formatted for public warning sirens, mobile cell broadcasts, and news tickers.
        """
        now_str = datetime.now(timezone.utc).strftime("%d-%b-%Y %H:%M UTC")

        if overall_severity in ("None", "Advisory"):
            en = f"SIMULATION ONLY ({now_str}): {overall_severity} scenario. Modeled peak depth {peak_observed_depth:.2f}m. No emergency warning is issued by this application."
            ta = f"மாதிரி உருவகப்படுத்தல் மட்டும் ({now_str}): கணிக்கப்பட்ட நீர்மட்டம் {peak_observed_depth:.2f} மீ. இது அதிகாரப்பூர்வ அவசர எச்சரிக்கை அல்ல."
            return {
                "siren_broadcast_english": en, "siren_broadcast_tamil": ta,
                "mobile_sms_alert_english": en, "mobile_sms_alert_tamil": ta,
                "press_bulletin_english": {"headline": en, "timestamp": now_str, "issued_by": "Chennai Flood Lab simulation"},
                "press_bulletin_tamil": {"headline": ta, "timestamp": now_str, "issued_by": "Chennai Flood Lab simulation"},
            }

        critical_ward_names_en = [w["zone_name"] for w in top_vulnerable_wards[:3]]
        critical_ward_names_ta = [
            w["zone_name"].replace("Zone", "மண்டலம்").replace("-", "").strip()
            for w in top_vulnerable_wards[:3]
        ]
        ward_str_en = ", ".join(critical_ward_names_en) if critical_ward_names_en else "Low-lying coastal corridors"
        ward_str_ta = ", ".join(critical_ward_names_ta) if critical_ward_names_ta else "தாழ்வான கடலோர பகுதிகள்"

        # 1. Public Address Warning Siren Broadcast (Audio Script)
        siren_en = (
            f"EMERGENCY FLOOD WARNING! Greater Chennai Corporation Siren Alert at {now_str}. "
            f"Severe inundation up to {peak_observed_depth:.2f} meters observed in {ward_str_en}. "
            f"All residents in ground floors must immediately evacuate to designated relief shelters "
            f"or proceed to upper floors. Do not drive through flooded waters or touch power cables. "
            f"For emergency rescue, call Chennai Disaster Helpline 1913 or State Emergency 1070."
        )

        siren_ta = (
            f"அவசர பெருவெள்ள எச்சரிக்கை! பெருநகர சென்னை மாநகராட்சி சைரன் அறிவிப்பு ({now_str}). "
            f"{ward_str_ta} பகுதிகளில் நீர்மட்டம் {peak_observed_depth:.2f} மீட்டரை எட்டியுள்ளது. "
            f"தரைத்தளத்தில் உள்ள பொதுமக்கள் உடனடியாக மாநகராட்சி நிவாரண முகாம்களுக்கு செல்லவும் "
            f"அல்லது உயரமான மாடி பகுதிகளுக்கு செல்லவும். தேங்கிய நீரில் செல்லாதீர்கள்; மின்கம்பங்களை தொடாதீர்கள். "
            f"அவசர உதவிக்கு மாநகராட்சி உதவி எண் 1913 அல்லது மாநில கட்டுப்பாட்டு அறை 1070-ஐ அழைக்கவும்."
        )

        # 2. Citizen Cell Broadcast (SMS / NDMA Flash Alert)
        sms_en = (
            f"[GCC-DISASTER ALERT]: FLASH FLOOD RED ALERT for Chennai. "
            f"Peak depth {peak_observed_depth:.2f}m in {ward_str_en}. "
            f"Evacuate low-lying areas. Rescue Helplines: 1913, 1070, 1077. Follow NDRF instructions."
        )

        sms_ta = (
            f"[சென்னை மாநகராட்சி பேரிடர் எச்சரிக்கை]: சென்னைக்கு அதிதீவிர வெள்ள எச்சரிக்கை (RED ALERT). "
            f"{ward_str_ta} பகுதிகளில் கடும் வெள்ளப்பெருக்கு. "
            f"தாழ்வான பகுதிகளை உடனே காலி செய்யவும். அவசர உதவி எண்கள்: 1913, 1070, 1077."
        )

        # 3. Press & Media Broadcast Bulletin
        bulletin_en = {
            "headline": f"CHENNAI FLOOD ADVISORY BULLETIN: {overall_severity.upper()} LEVEL INUNDATION",
            "timestamp": now_str,
            "issued_by": "Chennai Flood Lab — sample simulation bulletin",
            "critical_sectors": critical_ward_names_en,
            "peak_depth_meters": round(peak_observed_depth, 2),
            "citizens_isolated_count": total_stranded,
            "public_instructions": [
                "Switch off domestic main power circuit breakers if flood water enters premises.",
                "Boil all drinking water or consume official chlorinated emergency relief supplies.",
                "Keep emergency go-bags with medicines, essential documents, and flashlights accessible.",
                "Cooperate fully with Indian Coast Guard and NDRF boat rescue flotillas.",
            ],
            "official_helplines": {
                "gcc_flood_helpline": "1913",
                "state_emergency_center": "1070",
                "district_control_room": "1077",
                "police_emergency": "100",
                "ambulance_service": "108",
            },
        }

        bulletin_ta = {
            "headline": f"சென்னை வெள்ள அபாய அறிக்கை: {overall_severity.upper()} நிலை வெள்ளப்பெருக்கு",
            "timestamp": now_str,
            "issued_by": "Chennai Flood Lab — மாதிரி அறிக்கை",
            "critical_sectors": critical_ward_names_ta,
            "peak_depth_meters": round(peak_observed_depth, 2),
            "citizens_isolated_count": total_stranded,
            "public_instructions": [
                "வீட்டிற்குள் வெள்ளநீர் புகுந்தால் மின் இணைப்பை உடனடியாக துண்டிக்கவும்.",
                "குடிநீரை நன்றாக காய்ச்சி பருகவும் அல்லது அரசு வழங்கும் நிவாரண நீரை அருந்தவும்.",
                "அத்தியாவசிய மருந்துகள், ஆவணங்கள் மற்றும் டார்ச் விளக்குகளை பாதுகாப்பாக வைக்கவும்.",
                "NDRF மற்றும் தீயணைப்பு மீட்புக் குழுவினருக்கு முழு ஒத்துழைப்பு வழங்கவும்.",
            ],
            "official_helplines": {
                "மாநகராட்சி_உதவி_எண்": "1913",
                "மாநில_அவசர_மையம்": "1070",
                "மாவட்ட_கட்டுப்பாட்டு_அறை": "1077",
                "காவல்துறை": "100",
                "ஆம்புலன்ஸ்": "108",
            },
        }

        return {
            "siren_broadcast_english": "SIMULATION ONLY — SAMPLE BULLETIN. " + siren_en,
            "siren_broadcast_tamil": "மாதிரி உருவகப்படுத்தல் மட்டும். " + siren_ta,
            "mobile_sms_alert_english": "SIMULATION ONLY. " + sms_en,
            "mobile_sms_alert_tamil": "மாதிரி உருவகப்படுத்தல் மட்டும். " + sms_ta,
            "press_bulletin_english": bulletin_en,
            "press_bulletin_tamil": bulletin_ta,
        }

    def compute_mcdm_topsis_rankings(
        self,
        ward_rankings: List[Dict[str, Any]],
        casualty_data: Dict[str, Any],
        isolated_clusters: List[Dict[str, Any]],
        shelter_allocations: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        IEEE Multi-Criteria Decision Making (MCDM) using TOPSIS
        (Technique for Order of Preference by Similarity to Ideal Solution).
        Ranks zones / sectors for emergency relief convoy and rescue deployment.

        Criteria:
        1. Flood Inundation Depth (Benefit: higher depth = more critical, weight 0.25)
        2. Stranded / Vulnerable Population (Benefit: more citizens = more critical, weight 0.30)
        3. Road Inaccessibility / Isolation Score (Benefit: higher isolation = more critical, weight 0.20)
        4. Elevation Vulnerability (Cost: lower elevation = higher water accumulation risk, weight 0.15)
        5. Baseline Vulnerability Multiplier (Benefit: historical drainage vulnerability, weight 0.10)
        """
        weights = [0.25, 0.30, 0.20, 0.15, 0.10]
        criteria_types = ["benefit", "benefit", "benefit", "cost", "benefit"]

        # Map ward_rankings by zone_number or zone_id
        ward_map = {w["zone_number"]: w for w in ward_rankings}

        # Identify isolated clusters count per zone (by nearest locality match)
        isolated_count = len(isolated_clusters)

        matrix = []
        zone_entries = []

        for z in CHENNAI_GCC_ZONES:
            zn = z["zone_number"]
            w_info = ward_map.get(zn, {})

            flood_depth = float(w_info.get("peak_flood_depth_m", 0.0))
            stranded_pop = float(w_info.get("estimated_affected_population", 0.0))
            if stranded_pop == 0.0 and flood_depth > 0.0:
                stranded_pop = float(z["population"]) * min(1.0, flood_depth / 2.0)

            # Isolation factor: presence of severed routes or critical status
            is_critical = w_info.get("risk_tier") == "CRITICAL"
            is_high = w_info.get("risk_tier") == "HIGH"
            isolation = 1.0 if is_critical else (0.6 if is_high else (0.2 if flood_depth > 0 else 0.05))

            elevation = max(1.0, float(z.get("base_elevation_m", 3.0)))
            baseline_v = float(z.get("baseline_vulnerability", 1.0))

            row = [flood_depth, stranded_pop, isolation, elevation, baseline_v]
            matrix.append(row)
            zone_entries.append({
                "zone_number": zn,
                "zone_id": z["zone_id"],
                "zone_name": z["name"],
                "key_localities": z["key_localities"],
                "drainage_basin": z["drainage_basin"],
                "centroid": z["centroid"],
                "raw_metrics": {
                    "flood_depth_m": round(flood_depth, 2),
                    "affected_population": int(stranded_pop),
                    "isolation_factor": isolation,
                    "elevation_m": elevation,
                    "baseline_vulnerability": baseline_v,
                },
            })

        num_zones = len(matrix)
        num_crit = len(weights)

        # Step 1: Calculate vector norm denominator for each criterion
        norm_denoms = []
        for j in range(num_crit):
            ss = sum(matrix[i][j] ** 2 for i in range(num_zones))
            norm_denoms.append(math.sqrt(ss) if ss > 1e-9 else 1.0)

        # Step 2: Normalized weighted matrix
        v_matrix = []
        for i in range(num_zones):
            v_row = []
            for j in range(num_crit):
                r_ij = matrix[i][j] / norm_denoms[j]
                v_row.append(r_ij * weights[j])
            v_matrix.append(v_row)

        # Step 3: Determine positive-ideal (v_plus) and negative-ideal (v_minus)
        v_plus = []
        v_minus = []
        for j in range(num_crit):
            col_vals = [v_matrix[i][j] for i in range(num_zones)]
            if criteria_types[j] == "benefit":
                v_plus.append(max(col_vals))
                v_minus.append(min(col_vals))
            else:  # cost criterion
                v_plus.append(min(col_vals))
                v_minus.append(max(col_vals))

        # Step 4: Compute Euclidean separation distances and closeness coefficient
        ranked_zones = []
        for i in range(num_zones):
            d_plus = math.sqrt(sum((v_matrix[i][j] - v_plus[j]) ** 2 for j in range(num_crit)))
            d_minus = math.sqrt(sum((v_matrix[i][j] - v_minus[j]) ** 2 for j in range(num_crit)))

            denom = d_plus + d_minus
            closeness = (d_minus / denom) if denom > 1e-9 else 0.50

            # Priority tier classification
            if closeness >= 0.65:
                tier = "P1_IMMEDIATE_DISPATCH"
                action = "Deploy NDRF swift-water rescue teams & direct heavy supply convoys immediately."
            elif closeness >= 0.45:
                tier = "P2_HIGH_PRIORITY"
                action = "Pre-position relief rations, pumps, and utility vans at edge depot."
            elif closeness >= 0.25:
                tier = "P3_MODERATE_STANDBY"
                action = "Monitor drainage channels; alert volunteer teams and medical centers."
            else:
                tier = "P4_ROUTINE_MONITORING"
                action = "Normal precautionary surveillance; storm drains functional."

            entry = zone_entries[i]
            entry["topsis_score"] = round(closeness, 4)
            entry["relative_closeness_pct"] = round(closeness * 100.0, 1)
            entry["distance_to_ideal"] = round(d_plus, 4)
            entry["distance_to_anti_ideal"] = round(d_minus, 4)
            entry["priority_tier"] = tier
            entry["recommended_action"] = action
            ranked_zones.append(entry)

        # Sort descending by TOPSIS score
        ranked_zones.sort(key=lambda z: z["topsis_score"], reverse=True)
        for rank_idx, item in enumerate(ranked_zones, 1):
            item["dispatch_rank"] = rank_idx

        return {
            "methodology": "IEEE TOPSIS (Technique for Order Preference by Similarity to Ideal Solution)",
            "criteria_weights": {
                "inundation_depth": weights[0],
                "stranded_population": weights[1],
                "road_isolation": weights[2],
                "elevation_risk": weights[3],
                "baseline_vulnerability": weights[4],
            },
            "total_ranked_zones": len(ranked_zones),
            "p1_critical_count": sum(1 for z in ranked_zones if z["priority_tier"] == "P1_IMMEDIATE_DISPATCH"),
            "p2_high_count": sum(1 for z in ranked_zones if z["priority_tier"] == "P2_HIGH_PRIORITY"),
            "rankings": ranked_zones,
        }

    def generate_comprehensive_advisory(
        self,
        step_zones_state: List[Dict[str, Any]],
        dynamic_graph,
        isolated_clusters: List[Dict[str, Any]],
        shelter_allocations: List[Dict[str, Any]],
        flood_engine,
        simulation_summary: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Master synthesizer that creates the production-grade AI Decision Support Report.
        """
        # 1. Ward Vulnerability Index
        ward_rankings = self.compute_ward_vulnerability_index(step_zones_state, flood_engine)

        # 2. Casualty Prevention & Chokepoint Indicators
        casualty_data = self.compute_casualty_prevention_indicators(
            dynamic_graph, step_zones_state, isolated_clusters, shelter_allocations, flood_engine
        )

        # 3. Optimal Airlift Drop Zones
        airlift_assignments = self.compute_optimal_airlift_drop_zones(
            isolated_clusters, step_zones_state, flood_engine
        )

        # 4. Bilingual Emergency Broadcasts
        peak_depth = max([w["peak_flood_depth_m"] for w in ward_rankings]
                         + [z.get("peak_depth", 0.0) for z in step_zones_state] + [0.0])
        total_trapped = casualty_data["total_stranded_citizens"]

        overall_severity = ("Catastrophic" if peak_depth >= 1.20 else "Severe" if peak_depth >= 0.60
                            else "Moderate" if peak_depth >= 0.15 else "Advisory" if peak_depth > 0 else "None")
        broadcasts = self.generate_bilingual_emergency_broadcasts(
            overall_severity, ward_rankings, peak_depth, total_trapped
        )

        # 5. IEEE TOPSIS Multi-Criteria Decision Making (MCDM) Priority Dispatch
        mcdm_rankings = self.compute_mcdm_topsis_rankings(
            ward_rankings, casualty_data, isolated_clusters, shelter_allocations
        )

        # ML Ensemble Demand Predictor status check
        ml_status = {
            "is_available": bool(self.ml_predictor and getattr(self.ml_predictor, "is_loaded", False)),
            "model_type": self.ml_predictor.metadata()["name"] if hasattr(self.ml_predictor, "metadata") else "Legacy ensemble or planning rules",
            "explainability": "Scenario rules; demand model intervals available in inventory ledger",
        }

        return {
            "status": "success",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "summary": {
                "overall_severity": overall_severity,
                "peak_inundation_observed_m": round(peak_depth, 2),
                "critical_wards_count": len([w for w in ward_rankings if w["risk_tier"] == "CRITICAL"]),
                "high_risk_wards_count": len([w for w in ward_rankings if w["risk_tier"] == "HIGH"]),
                "total_stranded_citizens": total_trapped,
                "airlift_sorties_required": sum(a["assigned_drop_zone_id"] is not None for a in airlift_assignments),
                "clusters_without_safe_drop_zone": sum(a["assigned_drop_zone_id"] is None for a in airlift_assignments),
                "p1_mcdm_dispatch_zones": mcdm_rankings["p1_critical_count"],
            },
            "ward_vulnerability_index": ward_rankings,
            "casualty_prevention_indicators": casualty_data,
            "optimal_airlift_drop_zones": airlift_assignments,
            "mcdm_topsis_rankings": mcdm_rankings,
            "bilingual_emergency_broadcasts": broadcasts,
            "ml_decision_engine": ml_status,
        }
