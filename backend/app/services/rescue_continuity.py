"""Run-local rolling rescue schedule. No shared mutable state between simulations."""
from collections import Counter
from copy import deepcopy
from backend.app.services.geometry import haversine
from backend.app.services.rescue_fleet import plan_rescue_fleet


def point_on_phase(phase, minute):
    points = phase['geometry']['coordinates']
    fraction = min(1, max(0, (minute-phase['start_minutes'])/max(1e-9, phase['end_minutes']-phase['start_minutes'])))
    lengths = [haversine(a[1], a[0], b[1], b[0]) for a, b in zip(points, points[1:])]
    remaining = fraction*sum(lengths)
    for i, length in enumerate(lengths):
        if length > 0 and remaining <= length:
            ratio = remaining/length
            return [points[i][1]+(points[i+1][1]-points[i][1])*ratio,
                    points[i][0]+(points[i+1][0]-points[i][0])*ratio]
        remaining -= length
    return [points[-1][1], points[-1][0]]


class ContinuousRescuePlanner:
    def __init__(self, config, timeline=None):
        self.config = config
        self.timeline = timeline or []
        from backend.app.services.road_forecast import RoadForecast
        self.forecast = RoadForecast(self.timeline) if self.timeline and config.anticipate_road_closures and config.trucks.count else None
        self.route_events = []
        self.blocked_returns = set()
        self.trips, self.journeys, self.points = [], [], {}
        self.available = {}
        self.last_minute = -1e-6
        for mode in ('trucks', 'boats', 'helicopters'):
            pool = getattr(config, mode)
            for i in range(pool.count):
                self.available[f'{mode.upper()}-{i+1:02d}'] = pool.ready_after_minutes

    def update_routes(self, minute, road, flood, zones):
        if not self.forecast:
            return
        from backend.app.services.road_forecast import screen_line
        context = self.forecast.context(minute, minute+self.config.planning_window_minutes, road, flood, zones)
        for index, old in enumerate(self.trips):
            if old['mode'] != 'trucks' or not old['depart_minutes'] <= minute < old['return_available_minutes']:
                continue
            phase_index = next((i for i,p in enumerate(old['phases']) if p['start_minutes'] <= minute < p['end_minutes']), None)
            if phase_index is None or old['phases'][phase_index]['status'] not in ('returning','waiting_for_safe_road'):
                continue
            phase = old['phases'][phase_index]
            point = point_on_phase(phase, minute)
            # Retain the actually traversed prefix when replacing the remaining
            # return route. Previous timeline snapshots keep their old objects.
            coords = phase['geometry']['coordinates']
            fraction = (minute-phase['start_minutes'])/max(1e-9,phase['end_minutes']-phase['start_minutes'])
            lengths = [haversine(a[1],a[0],b[1],b[0]) for a,b in zip(coords,coords[1:])]
            remaining = max(0,fraction)*sum(lengths)
            cut = 0
            for cut,length in enumerate(lengths):
                if remaining <= length:
                    break
                remaining -= length
            point_geo = [point[1],point[0]]
            remainder = [point_geo]+coords[cut+1:]
            remainder_latlon = [[p[1],p[0]] for p in remainder]
            vid = old['vehicle_id']
            was_blocked = vid in self.blocked_returns
            if not was_blocked and all(screen_line(remainder_latlon,state,flood) for state in context['states']):
                continue
            route = self.forecast.return_route(point, self.config.base_location, minute,
                minute+self.config.planning_window_minutes,road,flood,zones)
            trip = deepcopy(old)
            prefix = deepcopy(trip['phases'][:phase_index])
            if minute > phase['start_minutes']:
                traversed = deepcopy(phase)
                traversed['end_minutes'] = minute
                traversed['geometry']['coordinates'] = coords[:cut+1]+[point_geo]
                if len(traversed['geometry']['coordinates']) < 2:
                    traversed['geometry']['coordinates'] = [point_geo,point_geo]
                prefix.append(traversed)
            if route is None:
                end = max(minute+60, self.timeline[-1]['time_elapsed_hours']*60+self.config.planning_window_minutes)
                new_phase = dict(status='waiting_for_safe_road',start_minutes=minute,end_minutes=end,
                    geometry=dict(type='LineString',coordinates=[point_geo,point_geo]))
                self.blocked_returns.add(vid)
                trip['route_status'] = 'return_blocked'
                trip['return_ready_known'] = False
                detail = 'No forecast-screened return path from this position. Vehicle held here; return time is unresolved.'
            else:
                distance = sum(haversine(*a,*b) for a,b in zip(route,route[1:]))
                end = minute+distance/self.config.trucks.speed_kmh*60
                new_phase = dict(status='returning',start_minutes=minute,end_minutes=round(end,6),
                    geometry=dict(type='LineString',coordinates=[[p[1],p[0]] for p in route]))
                self.blocked_returns.discard(vid)
                trip['route_status'] = 'return_rerouted'
                trip['return_ready_known'] = True
                detail = 'Return path replanned from the vehicle position against upcoming modeled flood states.'
            trip['phases'] = prefix+[new_phase]
            trip['return_available_minutes'] = new_phase['end_minutes']
            points=[]
            for item in trip['phases']:
                for p in item['geometry']['coordinates']:
                    if not points or points[-1]!=p:points.append(p)
            trip['geometry']['coordinates'] = points
            trip['distance_km'] = round(sum(haversine(a[1],a[0],b[1],b[0]) for a,b in zip(points,points[1:])),3)
            trip['checked_until_minutes'] = context['checked_until_minutes']
            self.trips[index] = trip
            self.available[vid] = trip['return_available_minutes']
            if route is not None or not was_blocked:
                self.route_events.append(dict(vehicle_id=vid,journey_id=trip['journey_id'],at_minutes=minute,
                    status=trip['route_status'],detail=detail,location=point,old_return_minutes=old['return_available_minutes'],
                    new_return_minutes=trip['return_available_minutes'] if route is not None else None))

    def reservations(self, minute):
        committed, reserved, arrived = Counter(), Counter(), Counter()
        for journey in self.journeys:
            committed[journey['cluster_id']] += journey['people']
            reserved[journey['shelter_id']] += journey['people']
            if journey['completed_minutes'] <= minute+1e-6:
                arrived[journey['shelter_id']] += journey['people']
        return dict(committed), dict(reserved), dict(arrived)

    def plan(self, minute, next_minute, clusters, shelters, road_engine, flood_engine, zones):
        ready = {vid: max(0, available-minute) for vid, available in self.available.items()}
        context = self.forecast.context(minute, minute+self.config.planning_window_minutes, road_engine, flood_engine, zones) if self.forecast else None
        result = plan_rescue_fleet(self.config, clusters, shelters, road_engine, flood_engine, zones,
            vehicle_ready_minutes=ready, departure_cutoff=max(0, next_minute-minute), journey_offset=len(self.journeys), road_forecast=context)
        new_trips, new_journeys = deepcopy(result['trips']), deepcopy(result['journeys'])
        for trip in new_trips:
            for key in ('depart_minutes', 'dropoff_minutes', 'return_available_minutes'):
                trip[key] = round(trip[key]+minute, 6)
            for phase in trip['phases']:
                phase['start_minutes'] = round(phase['start_minutes']+minute, 6)
                phase['end_minutes'] = round(phase['end_minutes']+minute, 6)
            trip['planned_at_minute'] = minute
            self.available[trip['vehicle_id']] = trip['return_available_minutes']
        for journey in new_journeys:
            for key in ('completed_minutes', 'boat_unloaded_minutes', 'truck_loading_minutes'):
                if key in journey:
                    journey[key] = round(journey[key]+minute, 6)
            journey['planned_at_minute'] = minute
        self.trips.extend(new_trips)
        self.journeys.extend(new_journeys)
        for point in result['transfer_points']:
            self.points[point['id']] = point
        completed = [j for j in self.journeys if j['completed_minutes'] <= minute+1e-6]
        pending = [j for j in self.journeys if j['completed_minutes'] > minute+1e-6]
        completed_people = sum(j['people'] for j in completed)
        pending_people = sum(j['people'] for j in pending)
        vehicles = result['vehicles']
        for vehicle in vehicles:
            vid = vehicle['vehicle_id']
            vehicle_trips = [t for t in self.trips if t['vehicle_id'] == vid]
            active = next((t for t in vehicle_trips if t['depart_minutes'] <= minute < t['return_available_minutes']), None)
            phase = next((p for p in active['phases'] if p['start_minutes'] <= minute < p['end_minutes']), None) if active else None
            vehicle['new_trips'] = vehicle['trips']
            vehicle['trips'] = len(vehicle_trips)
            vehicle['available_at_minutes'] = max(minute, self.available[vid])
            vehicle['return_ready_known'] = vid not in self.blocked_returns
            vehicle['location'] = point_on_phase(phase, minute) if phase else list(self.config.base_location)
            vehicle['activity_at_snapshot'] = (phase['status'] if phase else 'not_ready' if self.available[vid] > minute and not vehicle_trips else 'ready_at_base')
            vehicle['status_at_window_end'] = ('not_ready' if not vehicle_trips and self.available[vid] > next_minute
                                             else 'busy_returning' if self.available[vid] > next_minute else 'ready')
            if vid in self.blocked_returns:
                vehicle['allocation_reason'] = 'return_route_blocked'
            elif active and not vehicle['new_trips']:
                vehicle['allocation_reason'] = 'continuing_previous_trip'
            vehicle['earliest_dropoff_minutes'] = round(vehicle['earliest_dropoff_minutes']+minute, 6) if 'earliest_dropoff_minutes' in vehicle else None
        _, reservations, arrivals = self.reservations(minute)
        warnings = [dict(shelter_id=s['shelter_id'], name=s['name'], people=reservations.get(s['shelter_id'], 0),
                         message='Reserved rescue shelter is now compromised. Relocation of these occupants is not modeled.')
                    for s in shelters if s['status'] == 'compromised' and reservations.get(s['shelter_id'], 0)]
        result.update(mode='continuous', snapshot_time_minutes=minute,
            decision_end_minutes=next_minute, playback_start_minutes=minute,
            playback_end_minutes=max(next_minute, minute, *(t['return_available_minutes'] for t in self.trips)),
            cumulative_rescued=completed_people, committed_not_arrived=pending_people,
            cumulative_committed=completed_people+pending_people, newly_planned_people=result['provisionally_served'],
            new_journey_ids=[j['journey_id'] for j in new_journeys], new_vehicle_trips=len(new_trips),
            newly_completed_people=sum(j['people'] for j in completed if j['completed_minutes'] > self.last_minute+1e-6),
            trips=list(self.trips), journeys=list(self.journeys), transfer_points=list(self.points.values()),
            intermodal_served=sum(j['people'] for j in self.journeys if j['kind'] == 'boat_to_truck'),
            shelter_reservations=[dict(shelter_id=sid, reserved=count, arrived=arrivals.get(sid, 0), pending=count-arrivals.get(sid, 0)) for sid, count in reservations.items()],
            shelter_warnings=warnings, route_events=deepcopy(self.route_events), blocked_return_vehicles=sorted(self.blocked_returns),
            semantics='Continuous rescue schedule from the start of this run. Times are absolute simulation minutes. People count as rescued only after final shelter unloading; reserved passengers cannot be assigned twice. Ground assignments are recomputed each hour with rescue seats reserved.')
        result['limitations'] = [line for line in result['limitations'] if 'Shelter reservations do not change' not in line]
        result['limitations'] += ['New departures are committed only before the next timeline step; later departures are replanned using updated flood conditions.',
            'Forecast screening uses the modeled snapshots in the lookahead window and is conservative; it does not establish safety between snapshots or after the available forecast.',
            'Passenger legs retain their approved schedule. Returning trucks are rechecked at each timeline step; relocation from compromised shelters is not modeled.',
            'Completed rescue arrivals affect shelter occupancy and relief demand. Ground assignments remain hourly plans, not cumulative completed evacuations.']
        self.last_minute = minute
        return result
