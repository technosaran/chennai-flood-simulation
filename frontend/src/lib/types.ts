export type Coordinates = [number, number]; // [lat, lon]

export type SeverityLevel = 'advisory' | 'moderate' | 'severe' | 'catastrophic';

export type RouteStatus = 'clear' | 'rerouted' | 'caution' | 'impassable';

export type ShelterStatusType =
  'normal' | 'available' | 'near_capacity' | 'full' | 'compromised';

export interface FloodZoneInput {
  id: string;
  type: 'circle' | 'polygon';
  coordinates: Coordinates[]; // for polygon or [center] for circle
  radius_meters?: number; // for circle
  name?: string;
}

export interface DisasterParameters {
  rainfall_input_unit?: 'mm_per_hour' | 'legacy_level';
  rainfall_intensity_mm_hr: number; // 1 to 5 scale or direct mm/hr
  flood_depth_meters: number; // 0.1m to 3.0m
  spread_rate_meters_hr: number; // 50m/hr to 500m/hr
  duration_hours: number; // e.g. 6 or 12
}

export interface SimulationRequest {
  rescue_fleet?: RescueFleetConfig;
  flood_zones: FloodZoneInput[];
  parameters: DisasterParameters;
}

export interface RescueVehiclePool {
  count: number; seats: number; speed_kmh: number; handling_minutes: number; ready_after_minutes: number;
}
export interface RescueFleetConfig {
  continue_across_hours?: boolean;
  enable_intermodal_transfers?: boolean;
  destination_shelter_id?: string | null;
  planning_window_minutes: number;
  base_location: Coordinates;
  trucks: RescueVehiclePool; boats: RescueVehiclePool; helicopters: RescueVehiclePool;
}
export interface RescueFleetPlan {
  mode?: 'continuous'; snapshot_time_minutes?: number; decision_end_minutes?: number;
  playback_start_minutes?: number; playback_end_minutes?: number;
  cumulative_rescued?: number; committed_not_arrived?: number; cumulative_committed?: number;
  newly_planned_people?: number; newly_completed_people?: number; new_vehicle_trips?: number; new_journey_ids?: string[];
  shelter_reservations?: { shelter_id: string; reserved: number; arrived: number; pending: number }[];
  shelter_warnings?: { shelter_id: string; name: string; people: number; message: string }[];
  intermodal_served?: number;
  transfer_points?: { id: string; name: string; location: Coordinates; depth_m: number; access: string }[];
  journeys?: { journey_id: string; kind: 'direct' | 'boat_to_truck'; cluster_id: string; shelter_id: string; people: number; vehicle_ids: string[]; transfer_point_id?: string; completed_minutes: number; boat_unloaded_minutes?: number; truck_loading_minutes?: number }[];
  recommendations?: { kind: string; title: string; message: string; suggested_window_minutes?: number | null; estimated_additional_vehicles?: number; estimate_only?: boolean }[];
  planning_window_minutes: number; snapshot_demand: number; provisionally_served: number; still_needing_support: number;
  safe_shelter_spaces_before: number; safe_shelter_spaces_after: number;
  trips: { vehicle_id: string; mode: string; cluster_id: string; shelter_id: string; destination_name: string; people: number; depart_minutes: number; dropoff_minutes: number; return_available_minutes: number; distance_km: number; feasibility: string; geometry?: FleetLine; journey_id?: string; transfer_point_id?: string | null; counts_toward_served?: boolean; phases?: FleetPhase[] }[];
  vehicles: { vehicle_id: string; mode: string; seats: number; trips: number; available_at_minutes: number; status_at_window_end: string; allocation_reason?: string; earliest_dropoff_minutes?: number | null; location?: Coordinates; activity_at_snapshot?: string; new_trips?: number }[];
  unserved: { cluster_id: string; name: string; people: number; reason: string }[];
  semantics: string; limitations: string[];
}

export interface FleetLine { type: 'LineString'; coordinates: number[][] }
export interface FleetPhase { status: string; start_minutes: number; end_minutes: number; geometry: FleetLine }

export interface FloodPolygonFeature {
  type: 'Feature';
  properties: {
    zone_id: string;
    water_depth_m: number;
    severity: SeverityLevel;
    fill_color: string;
    stroke_color: string;
    fill_opacity: number;
    area_sq_km?: number;
  };
  geometry: {
    type: 'Polygon';
    coordinates: number[][][]; // GeoJSON format: [[ [lon, lat], ... ]]
  };
}

export interface EvacuationRouteFeature {
  type: 'Feature';
  properties: {
    route_id: string;
    source_cluster_id: string;
    source_name: string;
    destination_shelter_id: string;
    destination_name: string;
    evacuee_count: number;
    distance_km: number;
    estimated_time_min: number;
    status: RouteStatus;
    color: string;
    transport_mode?: 'foot' | 'truck' | 'amphibious' | 'helicopter';
    vehicle_type?: string;
    convoy_vehicle_count?: number;
    water_clearance_depth_m?: number;
    depth_profile?: number[];
    manifest?: {
      water_litres?: number;
      food_rations?: number;
      medical_kits?: number;
      life_jackets?: number;
    };
  };
  geometry: {
    type: 'LineString';
    coordinates: number[][]; // GeoJSON format: [ [lon, lat], ... ]
  };
}

export interface SupplyRouteFeature {
  type: 'Feature';
  properties: {
    route_id: string;
    transport_mode?: 'truck' | 'amphibious' | 'helicopter';
    vehicle_type?: string;
    convoy_vehicle_count?: number;
    water_clearance_depth_m?: number;
    depth_profile?: number[];
    warehouse_id: string;
    warehouse_name: string;
    destination_id: string;
    destination_name: string;
    distance_km: number;
    transit_time_min: number;
    cargo: {
      water_litres: number;
      food_rations: number;
      medical_kits: number;
      life_jackets?: number;
      satellite_phones?: number;
    };
    status: 'active' | 'completed' | 'blocked';
    color: string;
  };
  geometry: {
    type: 'LineString';
    coordinates: number[][]; // GeoJSON format: [ [lon, lat], ... ]
  };
}

export interface ShelterAllocation {
  shelter_id: string;
  name: string;
  neighborhood?: string;
  coordinates?: Coordinates;
  allocated_evacuees: number;
  remaining_capacity: number;
  total_capacity: number;
  current_occupancy: number;
  occupancy_pct: number;
  status: ShelterStatusType;
  amenities?: string[];
  demand?: {
    water_litres: number;
    food_rations: number;
    medical_kits: number;
    is_ai_predicted?: boolean;
  };
  allocated_supplies?: {
    water_litres: number;
    food_rations: number;
    medical_kits: number;
  };
  supply_status?: string;
  is_ai_predicted?: boolean;
  prediction_metadata?: Record<string, any>;
}

export interface InventoryStatus {
  total_water_litres: number;
  allocated_water_litres: number;
  available_water_litres: number;
  total_food_rations: number;
  allocated_food_rations: number;
  available_food_rations: number;
  total_medical_kits: number;
  allocated_medical_kits: number;
  available_medical_kits: number;
}

export interface IsolatedCluster {
  cluster_id: string;
  name: string;
  location: Coordinates;
  trapped_population: number;
  requires_airlift: boolean;
  reason?: string;
  reason_code?: string;
}

export interface PlannerMetrics {
  total_evacuated_population: number;
  trapped_requiring_rescue: number;
  avg_travel_time_min: number;
  total_person_km: number;
  compute_time_ms?: number;
}

export interface PlannerComparison {
  baseline: PlannerMetrics;
  optimized: PlannerMetrics;
  baseline_method?: string;
  optimized_method?: string;
  scope?: string;
  limitations?: string;
  additional_people_assigned: number;
  travel_time_change_min: number;
}

export interface TimelineStep {
  planner_comparison?: PlannerComparison | null;
  rescue_fleet_plan?: RescueFleetPlan | null;
  time_step: number; // hour index 0..T
  hour: number;
  description?: string;
  flood_polygons: {
    type: 'FeatureCollection';
    features: FloodPolygonFeature[];
  };
  evacuation_routes: {
    type: 'FeatureCollection';
    features: EvacuationRouteFeature[];
  };
  supply_routes: {
    type: 'FeatureCollection';
    features: SupplyRouteFeature[];
  };
  shelter_allocations: ShelterAllocation[];
  inventory_status: InventoryStatus;
  isolated_clusters: IsolatedCluster[];
  metrics: {
    total_flooded_area_sq_km: number;
    total_affected_population: number;
    evacuation_demand_population?: number;
    not_requiring_evacuation_population?: number;
    total_evacuated_population: number;
    unassigned_stranded_population: number;
    severed_roads_count: number;
    active_routes_count: number;
  };
}

export interface SimulationResponse {
  archive_origin?: string;
  archived_evidence?: { demand?: unknown; weather?: unknown };
  archived_parameters?: DisasterParameters;
  scenario?: { rescue_fleet?: RescueFleetConfig | null; parameters?: DisasterParameters };
  ai_advisory?: Record<string, unknown> | null;
  inventory_ledger?: Record<string, unknown>;
  shelter_allocations?: ShelterAllocation[];
  supply_routes?: { type: 'FeatureCollection'; features: SupplyRouteFeature[] };
  rescue_routes?: { type: 'FeatureCollection'; features: SupplyRouteFeature[] };
  diagnostics?: {
    compute_time_ms: number;
    time_steps: number;
    ml_predictions: number;
    rule_predictions: number;
    demand_model: {
      name: string;
      training_data: string;
      validated_for_live_use: boolean;
    };
  };
  simulation_id: string;
  status: 'completed' | 'running' | 'error';
  computed_at: string;
  timeline: TimelineStep[];
  summary: {
    total_affected_population: number;
    total_evacuated: number;
    stranded_requiring_rescue: number;
    peak_inundation_hour: number;
    max_flooded_area_sq_km: number;
    shelter_overall_utilization_pct: number;
  };
}

export interface SavedSimulation {
  imported_from?: { name: string; notice: string };
  id: string; name: string; saved_at: string; read_only: true;
  result: SimulationResponse;
  map_data: MapInitResponse;
  view: { parameters: DisasterParameters; zones: FloodZoneInput[] };
  evidence: { demand?: unknown; weather?: unknown };
}

export interface ShelterEntity {
  id: string;
  name: string;
  location: Coordinates;
  neighborhood: string;
  capacity: number;
  current_occupancy: number;
  amenities: string[];
}

export interface WarehouseEntity {
  id: string;
  name: string;
  location: Coordinates;
  address: string;
  supplies: {
    water_litres: number;
    food_rations: number;
    medical_kits: number;
  };
}

export interface DistributionPointEntity {
  id: string;
  name: string;
  location: Coordinates;
  target_ward: string;
  demand: {
    water_litres: number;
    food_rations: number;
    medical_kits: number;
    is_ai_predicted?: boolean;
    ai_explanation?: { feature: string; impact_pct: number }[];
  };
  assigned_evacuees: number;
  current_stock: {
    water_litres: number;
    food_rations: number;
    medical_kits: number;
  };
}

export interface PopulationClusterEntity {
  id: string;
  name: string;
  location: Coordinates;
  estimated_population: number;
  density_per_sq_km: number;
  risk_level: 'low' | 'moderate' | 'high' | 'extreme';
}

export interface PresetScenario {
  id: string;
  name: string;
  description: string;
  center: Coordinates;
  radius_meters: number;
  polygon_coordinates?: Coordinates[];
  default_rainfall: number;
  default_depth: number;
  default_spread: number;
}

export interface MapInitResponse {
  center: Coordinates;
  bounds: [Coordinates, Coordinates];
  shelters: ShelterEntity[];
  warehouses: WarehouseEntity[];
  distribution_points: DistributionPointEntity[];
  population_clusters: PopulationClusterEntity[];
  presets: PresetScenario[];
}

export interface ResourceAllocateRequest {
  simulation_id?: string;
  shelter_or_point_id: string;
  supplies: {
    water_litres: number;
    food_rations: number;
    medical_kits: number;
  };
  warehouse_id?: string;
}

export interface ResourceAllocateResponse {
  ledger?: Record<string, unknown>;
  success: boolean;
  updated_supply_routes?: SupplyRouteFeature[];
  updated_rescue_routes?: SupplyRouteFeature[];
  message?: string;
  updated_inventory: InventoryStatus;
  allocation_details: {
    target_id: string;
    allocated_water_litres: number;
    allocated_food_rations: number;
    allocated_medical_kits: number;
    deficit_remaining: {
      water_litres: number;
      food_rations: number;
      medical_kits: number;
    };
  };
}

export interface StagingBaseEntity {
  id: string;
  name: string;
  type: 'helicopter_base' | 'amphibious_base';
  location: Coordinates;
  callsign: string;
  stationed_assets: string;
  operational_radius_km: number;
  readiness_status: 'operational' | 'standby' | 'deployed';
}

export interface RouteInspectionData {
  network_source?: string;
  network_timestamp?: string;
  access_connectors_m?: number[];
  access_note?: string;
  geometry_kind?: string;
  route_id: string;
  route_name: string;
  route_category: 'evacuation' | 'supply' | 'airlift';
  transport_mode: 'truck' | 'amphibious' | 'helicopter' | 'foot';
  vehicle_type: string;
  source_name: string;
  destination_name: string;
  distance_km: number;
  transit_time_min: number;
  convoy_vehicle_count: number;
  water_clearance_depth_m: number;
  max_water_depth_m: number;
  depth_profile: {
    step_km: number;
    depth_m: number;
    elevation_m: number;
    status: 'clear' | 'caution' | 'submerged';
  }[];
  evacuee_or_capacity_count: number;
  manifest: {
    water_litres: number;
    food_rations: number;
    medical_kits: number;
    life_jackets?: number;
    satellite_radios?: number;
  };
  status:
    | 'clear'
    | 'rerouted'
    | 'caution'
    | 'impassable'
    | 'active'
    | 'airlift_deployed'
    | 'completed'
    | 'blocked';
  recommendation: string;
}

export interface AIAdvisorData {
  snapshot_hour?: number;
  risk_radar_level:
    | 'DEFCON 4 (ADVISORY)'
    | 'DEFCON 3 (ELEVATED)'
    | 'DEFCON 2 (SEVERE)'
    | 'DEFCON 1 (CRITICAL)';
  radar_score: number;
  tactical_summary: string;
  evacuation_advice: {
    id: string;
    priority: 'CRITICAL' | 'URGENT' | 'MONITOR';
    title: string;
    details: string;
    affected_ward: string;
    target_shelter: string;
    mode_suggested:
      'Amphibious Zodiac' | 'IAF Chetak Sortie' | 'High-Clearance 6x6 Truck';
  }[];
  broadcast: {
    english: string;
    tamil: string;
    timestamp: string;
    code: string;
    alert_level: 'No modeled flood' | 'Red Alert' | 'Orange Alert' | 'Emergency Evacuation';
  };
  bottlenecks: {
    id: string;
    corridor_name: string;
    zone: string;
    water_depth_m: number;
    traffic_choke_status:
      'SEVERED' | 'HIGH IMPEDANCE' | 'SUBMERGED BRIDGE' | 'RESTRICTED';
    suggested_detour: string;
  }[];
  mcdm_topsis_rankings?: {
    methodology: string;
    criteria_weights: Record<string, number>;
    total_ranked_zones: number;
    p1_critical_count: number;
    p2_high_count: number;
    rankings: Array<{
      zone_number: number;
      zone_id: string;
      zone_name: string;
      key_localities: string[];
      drainage_basin: string;
      centroid: [number, number];
      topsis_score: number;
      relative_closeness_pct: number;
      priority_tier: string;
      recommended_action: string;
      dispatch_rank: number;
      raw_metrics: {
        flood_depth_m: number;
        affected_population: number;
        isolation_factor: number;
        elevation_m: number;
        baseline_vulnerability: number;
      };
    }>;
  };
  ward_rankings: {
    ward_id: string;
    ward_name: string;
    risk_index: number;
    vulnerable_population: number;
    water_depth_m: number;
    trend: 'rising' | 'peaking' | 'receding';
  }[];
}
