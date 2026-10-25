"""Validate portable JSON snapshots before allowing them into the local archive.

Validation checks the display contract, not the scientific truth of imported results.
The original JSON is retained without coercion or recomputation.
"""
import json
import math
from datetime import datetime
from backend.app.models.disaster import DisasterParameters, FloodZoneInput, SimulationRequest

MAX_IMPORT_BYTES = 10 * 1024 * 1024


def fields(names, kind=float):
    return dict.fromkeys(names.split(), kind)


def check(value, schema, path='snapshot'):
    if isinstance(schema, dict):
        if not isinstance(value, dict):
            raise ValueError(f'{path} must be an object')
        for key, child in schema.items():
            if key not in value:
                raise ValueError(f'{path}.{key} is missing')
            check(value[key], child, f'{path}.{key}')
    elif isinstance(schema, list):
        if not isinstance(value, list):
            raise ValueError(f'{path} must be an array')
        for i, item in enumerate(value):
            check(item, schema[0], f'{path}[{i}]')
    elif schema is float:
        if type(value) not in (int, float) or not math.isfinite(value):
            raise ValueError(f'{path} must be a finite number')
    elif type(value) is not schema:
        raise ValueError(f'{path} has the wrong type')


STOCK = fields('water_litres food_rations medical_kits')
ENTITY = fields('id name', str) | {'location': [float]}
COLLECTION = {'type': str, 'features': [{'type': str, 'geometry': dict, 'properties': dict}]}
ALLOCATION = fields('shelter_id name status', str) | fields('allocated_evacuees remaining_capacity total_capacity current_occupancy occupancy_pct')
METRICS = fields('total_flooded_area_sq_km total_affected_population total_evacuated_population unassigned_stranded_population severed_roads_count active_routes_count')
INVENTORY = fields(' '.join(f'{prefix}_{unit}' for prefix in ('total', 'allocated', 'available') for unit in STOCK))
FLEET = fields('planning_window_minutes snapshot_demand provisionally_served still_needing_support safe_shelter_spaces_before safe_shelter_spaces_after') | {
    'semantics': str, 'limitations': [str],
    'vehicles': [fields('vehicle_id mode status_at_window_end', str) | fields('seats trips available_at_minutes')],
    'trips': [fields('vehicle_id mode cluster_id shelter_id destination_name feasibility', str) | fields('people depart_minutes dropoff_minutes return_available_minutes distance_km')],
    'unserved': [fields('cluster_id name reason', str) | fields('people')],
}
ADVICE = {
    'summary': {'overall_severity': str} | fields('peak_inundation_observed_m critical_wards_count total_stranded_citizens'),
    'bilingual_emergency_broadcasts': fields('siren_broadcast_english siren_broadcast_tamil', str),
    'casualty_prevention_indicators': {
        'chokepoints_and_bottlenecks': [dict],
        'stranded_population_traps': [{'name': str} | fields('trapped_population water_depth_m')],
    },
    'ward_vulnerability_index': [fields('zone_id zone_name', str) | fields('vulnerability_index population peak_flood_depth_m')],
}


def coordinate(value, geojson=False):
    check(value, [float], 'coordinate')
    if len(value) != 2:
        raise ValueError('Coordinates must contain exactly two numbers')
    lat, lon = value[::-1] if geojson else value
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        raise ValueError('Coordinates are outside geographic bounds')


def collection(value, geometry, properties=None):
    check(value, COLLECTION)
    if value['type'] != 'FeatureCollection':
        raise ValueError('Expected a GeoJSON FeatureCollection')
    for feature in value['features']:
        if properties:
            check(feature['properties'], properties)
        geom = feature['geometry']
        if feature['type'] != 'Feature' or geom.get('type') != geometry:
            raise ValueError('Unsupported snapshot geometry')
        points = geom.get('coordinates')
        if not isinstance(points, list) or not points:
            raise ValueError('GeoJSON coordinates are missing')
        if geometry == 'Polygon':
            for ring in points:
                if not isinstance(ring, list) or len(ring) < 4 or ring[0] != ring[-1]:
                    raise ValueError('Polygon rings must be closed and contain at least four points')
                for point in ring:
                    coordinate(point, True)
        else:
            if len(points) < 2:
                raise ValueError('Routes need at least two points')
            for point in points:
                coordinate(point, True)


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('Duplicate JSON object keys are not supported')
        result[key] = value
    return result


def parse_snapshot(raw):
    if len(raw) > MAX_IMPORT_BYTES:
        raise ValueError('Snapshot files must be 10 MB or smaller')
    data = json.loads(raw.decode('utf-8-sig'), object_pairs_hook=unique_object)
    # Bound nesting and reject nonstandard numeric values anywhere, including evidence.
    def finite_tree(value, depth=0):
        if depth > 60:
            raise ValueError('Snapshot nesting exceeds the supported limit')
        if isinstance(value, float) and not math.isfinite(value):
            raise ValueError('Snapshot contains a non-finite number')
        for child in value.values() if isinstance(value, dict) else value if isinstance(value, list) else ():
            finite_tree(child, depth + 1)
    finite_tree(data)
    check(data, {'schema_version': int, 'name': str, 'result': dict, 'map_data': dict, 'view': dict, 'evidence': dict})
    if data['schema_version'] != 1:
        raise ValueError('Unsupported snapshot version; use a version 1 full snapshot export')
    name = data['name'].strip()
    if not name or len(name) > 80:
        raise ValueError('Snapshot name must contain 1 to 80 characters')
    result = data['result']
    check(result, fields('simulation_id computed_at status', str) | {'scenario': dict, 'summary': dict, 'timeline': [dict]})
    if not result['simulation_id'] or len(result['simulation_id']) > 100 or result['status'] != 'completed':
        raise ValueError('Only complete simulation snapshots can be imported')
    datetime.fromisoformat(result['computed_at'].replace('Z', '+00:00'))
    SimulationRequest.model_validate(result['scenario'])
    if result['scenario'].get('parameters') is None:
        raise ValueError('Original physical scenario parameters are missing')
    if not 1 <= len(result['timeline']) <= 97:
        raise ValueError('A snapshot must contain 1 to 97 timeline steps')
    check(result['summary'], fields('total_affected_population total_evacuated stranded_requiring_rescue peak_inundation_hour max_flooded_area_sq_km shelter_overall_utilization_pct'))
    previous_hour = -1
    for step in result['timeline']:
        check(step, fields('time_step hour') | {'metrics': METRICS, 'inventory_status': INVENTORY,
              'shelter_allocations': [ALLOCATION], 'isolated_clusters': [fields('cluster_id name', str) | {'location': [float], 'trapped_population': float, 'requires_airlift': bool}]})
        if not 0 <= step['hour'] <= 24 or step['hour'] <= previous_hour:
            raise ValueError('Timeline hours must increase within 0 to 24 hours')
        previous_hour = step['hour']
        for cluster in step['isolated_clusters']:
            coordinate(cluster['location'])
        for key, geometry in [('flood_polygons', 'Polygon'), ('evacuation_routes', 'LineString'), ('supply_routes', 'LineString')]:
            if key not in step:
                raise ValueError(f'Timeline {key} is missing')
            props = ({'zone_id': str, 'severity': str, 'fill_color': str, 'stroke_color': str} | fields('water_depth_m fill_opacity') if key == 'flood_polygons'
                     else fields('route_id source_cluster_id source_name destination_shelter_id destination_name status', str) | fields('evacuee_count distance_km estimated_time_min') if key == 'evacuation_routes'
                     else fields('route_id warehouse_id warehouse_name destination_id destination_name status', str) | fields('distance_km transit_time_min') | {'cargo': STOCK})
            collection(step[key], geometry, props)
        if step.get('rescue_fleet_plan') is not None:
            fleet = step['rescue_fleet_plan']
            check(fleet, FLEET)
            if fleet.get('mode') == 'continuous':
                check(fleet, fields('snapshot_time_minutes decision_end_minutes playback_start_minutes playback_end_minutes cumulative_rescued committed_not_arrived cumulative_committed newly_planned_people newly_completed_people new_vehicle_trips') |
                      {'new_journey_ids': [str], 'shelter_reservations': [fields('shelter_id', str) | fields('reserved arrived pending')],
                       'shelter_warnings': [fields('shelter_id name message', str) | fields('people')]})
                if (not 0 <= fleet['playback_start_minutes'] <= fleet['playback_end_minutes']
                        or fleet['cumulative_committed'] != fleet['cumulative_rescued']+fleet['committed_not_arrived']):
                    raise ValueError('Invalid continuous rescue totals or playback times')
                for vehicle in fleet['vehicles']:
                    check(vehicle, {'activity_at_snapshot': str, 'location': [float]})
                    coordinate(vehicle['location'])
            for trip in fleet['trips']:
                for line in [trip['geometry']] if 'geometry' in trip else []:
                    collection({'type': 'FeatureCollection', 'features': [{'type': 'Feature', 'geometry': line, 'properties': {}}]}, 'LineString')
                if 'phases' in trip:
                    check(trip['phases'], [fields('status', str) | fields('start_minutes end_minutes') | {'geometry': dict}])
                    for phase in trip['phases']:
                        if not 0 <= phase['start_minutes'] <= phase['end_minutes']:
                            raise ValueError('Fleet phase times must be nonnegative and ordered')
                        collection({'type': 'FeatureCollection', 'features': [{'type': 'Feature', 'geometry': phase['geometry'], 'properties': {}}]}, 'LineString')
            if 'transfer_points' in fleet:
                check(fleet['transfer_points'], [fields('id name access', str) | fields('depth_m') | {'location': [float]}])
                for point in fleet['transfer_points']:
                    coordinate(point['location'])
            if 'journeys' in fleet:
                check(fleet['journeys'], [fields('journey_id kind cluster_id shelter_id', str) | fields('people completed_minutes') | {'vehicle_ids': [str]}])
            if 'recommendations' in fleet:
                check(fleet['recommendations'], [fields('kind title message', str)])
    if result.get('ai_advisory') is not None:
        check(result['ai_advisory'], ADVICE)
    if result.get('diagnostics') is not None:
        check(result['diagnostics'], fields('compute_time_ms time_steps ml_predictions rule_predictions') | {'demand_model': {'name': str}})
    if result.get('inventory_ledger') is not None:
        check(result['inventory_ledger'], dict)
        for key in ('distribution_points', 'shelters'):
            if key in result['inventory_ledger']:
                check(result['inventory_ledger'][key], [{'name': str, 'deficit': STOCK}])
    map_data = data['map_data']
    check(map_data, {'center': [float], 'bounds': [[float]],
        'shelters': [ENTITY | fields('neighborhood', str) | fields('capacity current_occupancy') | {'amenities': [str]}],
        'warehouses': [ENTITY | {'supplies': STOCK}], 'distribution_points': [ENTITY | {'target_ward': str, 'demand': STOCK}],
        'population_clusters': [ENTITY | fields('estimated_population density_per_sq_km') | {'risk_level': str}],
        'presets': [dict]})
    coordinate(map_data['center'])
    if len(map_data['bounds']) != 2:
        raise ValueError('Map bounds need two corners')
    for point in map_data['bounds']:
        coordinate(point)
    for key in ('shelters', 'warehouses', 'distribution_points', 'population_clusters'):
        for entity in map_data[key]:
            coordinate(entity['location'])
    for preset in map_data['presets']:
        check(preset, fields('id name description', str) | {'center': [float], 'radius_meters': float})
        coordinate(preset['center'])
    check(data['view'], {'parameters': dict, 'zones': [dict]})
    check(data['view']['parameters'], fields('rainfall_intensity_mm_hr flood_depth_meters spread_rate_meters_hr duration_hours'))
    DisasterParameters.model_validate(data['view']['parameters'])
    for zone in data['view']['zones']:
        check(zone, {'id': str, 'type': str, 'coordinates': [[float]]})
        if zone['type'] not in ('circle', 'polygon'):
            raise ValueError('Saved display zones must be circles or polygons')
        FloodZoneInput.model_validate(zone)
        for point in zone['coordinates']:
            coordinate(point)
    # Discard archive envelope IDs so imports cannot overwrite or spoof local records.
    snapshot = {key: data[key] for key in ('schema_version', 'result', 'map_data', 'view', 'evidence')}
    snapshot['imported_from'] = {'name': name, 'notice': 'Imported file; results and evidence were not independently verified.'}
    return name, snapshot
