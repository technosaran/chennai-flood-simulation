"""Finite, frozen-snapshot rescue scheduling with synchronized boat/truck handoffs."""
import math
from functools import lru_cache
import networkx as nx
from backend.app.services.geometry import haversine


def plan_rescue_fleet(config, clusters, shelters, road_engine, flood_engine, zones,
                      vehicle_ready_minutes=None, departure_cutoff=None, journey_offset=0, road_forecast=None):
    horizon = config.planning_window_minutes
    base = list(config.base_location)
    origins = {c['cluster_id']: c for c in clusters}
    need = {cid: int(c['trapped_population']) for cid, c in origins.items()}
    initial = sum(need.values())
    destinations = {s['shelter_id']: s for s in shelters if s['status'] != 'compromised'
                    and (config.destination_shelter_id is None or s['shelter_id'] == config.destination_shelter_id)
                    and s['remaining_capacity'] > 0 and flood_engine.get_point_depth(*s['location'], zones) < .3}
    slots = {sid: int(s['remaining_capacity']) for sid, s in destinations.items()}
    depths = {cid: flood_engine.get_point_depth(*c['location'], zones) for cid, c in origins.items()}
    graph = (road_forecast['graph'] if road_forecast else road_engine.build_dynamic_graph(zones, closure_threshold_m=.3, slowdown_threshold_m=.1, mode='truck')) if config.trucks.count else None
    route_changes, blocked_legs = set(), set()
    road_paths = {}
    options = {mode: {} for mode in ('trucks', 'boats', 'helicopters')}
    transfer_options = []
    candidate_points = {}

    def nearest(point):
        try:
            return road_engine.find_nearest_node(*point, mode='truck')
        except TypeError:
            return road_engine.find_nearest_node(*point)

    def route_coords(path):
        try:
            return road_engine.get_route_coordinates(path, graph)
        except TypeError:
            return road_engine.get_route_coordinates(path)

    @lru_cache(maxsize=None)
    def road_distance(start, end):
        if any(flood_engine.get_point_depth(*p, zones) >= .3 for p in (start, end)):
            return None
        source, target = nearest(start), nearest(end)
        if source is None or target is None:
            return None
        try:
            path = nx.shortest_path(graph, source, target, weight='weight')
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            if (road_forecast and road_forecast['baseline'].has_node(source)
                    and road_forecast['baseline'].has_node(target) and nx.has_path(road_forecast['baseline'],source,target)):
                blocked_legs.add((start,end))
            return None
        if road_forecast:
            baseline_path = nx.shortest_path(road_forecast['baseline'],source,target,weight='weight')
            if path != baseline_path:
                route_changes.add((start,end))
        coords = [list(start)] + route_coords(path) + [list(end)]
        for a, b in zip(coords, coords[1:]):
            samples = max(1, math.ceil(haversine(*a, *b) * 1000 / 25))
            if any(flood_engine.get_point_depth(*(a[j] + (b[j]-a[j])*i/samples for j in range(2)), state) >= .3 for state in (road_forecast['states'] if road_forecast else [zones]) for i in range(samples+1)):
                if road_forecast:
                    blocked_legs.add((start,end))
                return None
        road_paths[(start, end)] = coords
        return sum(haversine(*a, *b) for a, b in zip(coords, coords[1:]))

    def road(a, b):
        return road_distance(tuple(a), tuple(b))

    def geometry(points):
        return dict(type='LineString', coordinates=[[p[1], p[0]] for p in points])

    def path(a, b, mode):
        return road_paths[(tuple(a), tuple(b))] if mode == 'trucks' else [a, b]

    def phase(status, start, end, points):
        return dict(status=status, start_minutes=round(start, 6), end_minutes=round(end, 6), geometry=geometry(points))

    for mode in options:
        pool = getattr(config, mode)
        if not pool.count:
            continue
        for cid, cluster in origins.items():
            if need[cid] <= 0 or (mode == 'trucks' and depths[cid] >= .3) or (mode == 'boats' and depths[cid] < .3):
                continue
            for sid, shelter in destinations.items():
                points = [base, cluster['location'], shelter['location'], base]
                legs = [road(a, b) if mode == 'trucks' else haversine(*a, *b) for a, b in zip(points, points[1:])]
                if any(d is None for d in legs):
                    continue
                arrival = (legs[0]+legs[1])/pool.speed_kmh*60 + 2*pool.handling_minutes
                cycle = arrival + legs[2]/pool.speed_kmh*60
                options[mode][(cid, sid)] = (arrival, cycle, legs)

    # Sample dry roadside points around each wet cluster. A candidate is a
    # modeled rendezvous, never a verified boat landing/launch site.
    if config.enable_intermodal_transfers and config.boats.count and config.trucks.count and destinations:
        for cid, cluster in origins.items():
            if need[cid] <= 0 or depths[cid] < .3:
                continue
            pickup = cluster['location']
            found = {}
            for radius in (.25, .5, 1, 2, 4, 8):
                for bearing in range(0, 360, 30):
                    angle = math.radians(bearing)
                    probe = [pickup[0]+radius*math.cos(angle)/111.32,
                             pickup[1]+radius*math.sin(angle)/(111.32*math.cos(math.radians(pickup[0])))]
                    node = nearest(probe)
                    if node is None or node in found:
                        continue
                    point = route_coords([node])[0]
                    distance = haversine(*pickup, *point)
                    if (.02 <= distance <= 8.5 and flood_engine.get_point_depth(*point, zones) < .3
                            and road(base, point) is not None):
                        found[node] = (distance, list(point))
                if len(found) >= 8:
                    break
            for node, (_, point) in sorted(found.items(), key=lambda item: (item[1][0], str(item[0])))[:8]:
                approach, returning = road(base, point), None
                if approach is None:
                    continue
                for sid, shelter in destinations.items():
                    onward = road(point, shelter['location'])
                    returning = road(shelter['location'], base)
                    if onward is None or returning is None:
                        continue
                    pid = f'TRANSFER-{node}'
                    candidate_points[pid] = dict(id=pid, name='Dry roadside transfer '+str(node), location=point,
                                                 depth_m=round(flood_engine.get_point_depth(*point, zones), 3),
                                                 access='Road screened; boat landing and launch access unverified')
                    boat_legs = [haversine(*base, *pickup), haversine(*pickup, *point), haversine(*point, *base)]
                    transfer_options.append(dict(cid=cid, sid=sid, point_id=pid, boat_legs=boat_legs,
                                                 truck_legs=[approach, onward, returning]))

    vehicles = {}
    for mode in options:
        pool = getattr(config, mode)
        for index in range(pool.count):
            vid = f'{mode.upper()}-{index+1:02d}'
            ready = (vehicle_ready_minutes or {}).get(vid, pool.ready_after_minutes)
            vehicles[vid] = dict(vehicle_id=vid, mode=mode, seats=pool.seats, trips=0, available_at_minutes=ready)
    trips, journeys = [], []

    def transfer_timing(option, boat_ready, truck_ready):
        b, t = config.boats, config.trucks
        bl, tl = option['boat_legs'], option['truck_legs']
        at_pickup = boat_ready + bl[0]/b.speed_kmh*60
        at_point = at_pickup + b.handling_minutes + bl[1]/b.speed_kmh*60
        boat_done = at_point + b.handling_minutes
        truck_at_point = truck_ready + tl[0]/t.speed_kmh*60
        load_start = max(boat_done, truck_at_point)
        at_shelter = load_start + t.handling_minutes + tl[1]/t.speed_kmh*60
        completed = at_shelter + t.handling_minutes
        return at_pickup, at_point, boat_done, truck_at_point, load_start, at_shelter, completed

    def add_trip(vid, cid, sid, count, depart, dropoff, back, legs, phases, journey_id, final=True, point_id=None):
        vehicle = vehicles[vid]
        vehicle['trips'] += 1
        vehicle['available_at_minutes'] = back
        coords = []
        for item in phases:
            for point in item['geometry']['coordinates']:
                if not coords or coords[-1] != point:
                    coords.append(point)
        trips.append(dict(vehicle_id=vid, mode=vehicle['mode'], cluster_id=cid, shelter_id=sid,
                          destination_name=destinations[sid]['name'] if final else candidate_points[point_id]['name'],
                          people=count, depart_minutes=round(depart, 6), dropoff_minutes=round(dropoff, 6),
                          return_available_minutes=round(back, 6), distance_km=round(sum(legs), 3),
                          geometry=dict(type='LineString', coordinates=coords), phases=phases,
                          journey_id=journey_id, transfer_point_id=point_id, counts_toward_served=final,
                          route_status=('forecast_rerouted' if any((tuple([p[1],p[0]]),tuple([q[1],q[0]])) in route_changes for item in phases for p,q in [(item['geometry']['coordinates'][0],item['geometry']['coordinates'][-1])]) else 'forecast_screened') if road_forecast and vehicle['mode']=='trucks' else 'snapshot_estimate',
                          checked_until_minutes=road_forecast['checked_until_minutes'] if road_forecast and vehicle['mode']=='trucks' else None,
                          feasibility='road-screened snapshot estimate' if vehicle['mode'] == 'trucks' else 'provisional direct-distance transfer; verify access'))

    while True:
        candidates = []
        for vid, vehicle in vehicles.items():
            mode, ready = vehicle['mode'], vehicle['available_at_minutes']
            for (cid, sid), timing in options[mode].items():
                dropoff = ready+timing[0]
                if (need[cid] > 0 and slots[sid] > 0 and dropoff <= horizon+1e-9
                        and (departure_cutoff is None or ready < departure_cutoff-1e-9)):
                    candidates.append(((-depths[cid], dropoff, 0, vid, cid, sid), 'direct', vid, cid, sid, timing))
        boats = [v for v in vehicles.values() if v['mode'] == 'boats']
        trucks = [v for v in vehicles.values() if v['mode'] == 'trucks']
        # Identical speeds/seats in each pool: the earliest-ready member
        # dominates all later members for a given handoff option.
        boat = min(boats, key=lambda v: (v['available_at_minutes'], v['vehicle_id']), default=None)
        truck = min(trucks, key=lambda v: (v['available_at_minutes'], v['vehicle_id']), default=None)
        if (boat and truck and (departure_cutoff is None or
                max(boat['available_at_minutes'], truck['available_at_minutes']) < departure_cutoff-1e-9)):
            for option in transfer_options:
                cid, sid = option['cid'], option['sid']
                if need[cid] <= 0 or slots[sid] <= 0:
                    continue
                timing = transfer_timing(option, boat['available_at_minutes'], truck['available_at_minutes'])
                if timing[-1] <= horizon+1e-9:
                    candidates.append(((-depths[cid], timing[-1], 1, boat['vehicle_id'], cid, sid), 'transfer', boat['vehicle_id'], truck['vehicle_id'], option, timing))
        if not candidates:
            break
        choice = min(candidates, key=lambda item: item[0])
        jid = f'JOURNEY-{journey_offset+len(journeys)+1:04d}'
        if choice[1] == 'direct':
            _, _, vid, cid, sid, (arrival, cycle, legs) = choice
            vehicle = vehicles[vid]
            mode, ready = vehicle['mode'], vehicle['available_at_minutes']
            pool = getattr(config, mode)
            pickup, shelter = origins[cid]['location'], destinations[sid]['location']
            at_pickup = ready+legs[0]/pool.speed_kmh*60
            at_shelter = at_pickup+pool.handling_minutes+legs[1]/pool.speed_kmh*60
            phases = [phase('travelling_to_pickup', ready, at_pickup, path(base, pickup, mode)),
                      phase('loading', at_pickup, at_pickup+pool.handling_minutes, [pickup, pickup]),
                      phase('carrying_people', at_pickup+pool.handling_minutes, at_shelter, path(pickup, shelter, mode)),
                      phase('unloading', at_shelter, ready+arrival, [shelter, shelter]),
                      phase('returning', ready+arrival, ready+cycle, path(shelter, base, mode))]
            count = min(pool.seats, need[cid], slots[sid])
            add_trip(vid, cid, sid, count, ready, ready+arrival, ready+cycle, legs, phases, jid)
            journeys.append(dict(journey_id=jid, kind='direct', cluster_id=cid, shelter_id=sid, people=count,
                                 vehicle_ids=[vid], completed_minutes=round(ready+arrival, 6)))
        else:
            _, _, bvid, tvid, option, timing = choice
            cid, sid, pid = option['cid'], option['sid'], option['point_id']
            b, t = config.boats, config.trucks
            br, tr = vehicles[bvid]['available_at_minutes'], vehicles[tvid]['available_at_minutes']
            bl, tl = option['boat_legs'], option['truck_legs']
            pickup, point, shelter = origins[cid]['location'], candidate_points[pid]['location'], destinations[sid]['location']
            at_pickup, at_point, boat_done, truck_at_point, load_start, at_shelter, completed = timing
            boat_back, truck_back = boat_done+bl[2]/b.speed_kmh*60, completed+tl[2]/t.speed_kmh*60
            count = min(b.seats, t.seats, need[cid], slots[sid])
            bp = [phase('travelling_to_pickup', br, at_pickup, [base, pickup]),
                  phase('loading', at_pickup, at_pickup+b.handling_minutes, [pickup, pickup]),
                  phase('carrying_people', at_pickup+b.handling_minutes, at_point, [pickup, point]),
                  phase('unloading', at_point, boat_done, [point, point]),
                  phase('returning', boat_done, boat_back, [point, base])]
            tp = [phase('travelling_to_transfer', tr, truck_at_point, path(base, point, 'trucks')),
                  phase('waiting_for_boat', truck_at_point, load_start, [point, point]),
                  phase('loading', load_start, load_start+t.handling_minutes, [point, point]),
                  phase('carrying_people', load_start+t.handling_minutes, at_shelter, path(point, shelter, 'trucks')),
                  phase('unloading', at_shelter, completed, [shelter, shelter]),
                  phase('returning', completed, truck_back, path(shelter, base, 'trucks'))]
            add_trip(bvid, cid, sid, count, br, boat_done, boat_back, bl, bp, jid, False, pid)
            add_trip(tvid, cid, sid, count, tr, completed, truck_back, tl, tp, jid, True, pid)
            journeys.append(dict(journey_id=jid, kind='boat_to_truck', cluster_id=cid, shelter_id=sid, people=count,
                                 vehicle_ids=[bvid, tvid], transfer_point_id=pid, boat_unloaded_minutes=round(boat_done, 6),
                                 truck_loading_minutes=round(load_start, 6), completed_minutes=round(completed, 6)))
        need[cid] -= count
        slots[sid] -= count

    earliest = {}
    for mode, mode_options in options.items():
        ready = getattr(config, mode).ready_after_minutes
        values = [ready+timing[0] for (cid, sid), timing in mode_options.items() if need[cid] > 0 and slots[sid] > 0]
        if mode in ('boats', 'trucks'):
            values += [transfer_timing(o, config.boats.ready_after_minutes, config.trucks.ready_after_minutes)[-1]
                       for o in transfer_options if need[o['cid']] > 0 and slots[o['sid']] > 0]
        if values:
            earliest[mode] = min(values)
    for vehicle in vehicles.values():
        mode = vehicle['mode']
        vehicle['status_at_window_end'] = ('not_ready' if not vehicle['trips'] and vehicle['available_at_minutes'] > horizon
                                          else 'busy_returning' if vehicle['available_at_minutes'] > horizon else 'ready')
        vehicle['available_at_minutes'] = round(vehicle['available_at_minutes'], 6)
        compatible = any(need[cid] and (depths[cid] < .3 if mode == 'trucks' else depths[cid] >= .3 if mode == 'boats' else True) for cid in origins)
        vehicle['allocation_reason'] = ('assigned' if vehicle['trips'] else 'no_remaining_demand' if not any(need.values())
            else 'no_safe_shelter_space' if not any(slots.values())
            else 'vehicle_not_ready_in_window' if getattr(config, mode).ready_after_minutes > horizon
            else 'trip_exceeds_planning_window' if mode in earliest and earliest[mode] > horizon
            else 'partner_vehicle_unavailable' if mode in earliest and not compatible
            else 'pickup_depth_incompatible' if not compatible
            else 'no_screened_road_access' if mode == 'trucks' and mode not in earliest
            else 'no_compatible_destination' if mode not in earliest else 'fleet_or_time_window_exhausted')
        if mode in earliest:
            vehicle['earliest_dropoff_minutes'] = round(earliest[mode], 3)
    remaining = []
    for cid, cluster in origins.items():
        if need[cid]:
            reachable = any((cid, sid) in options[mode] and slots[sid] > 0 for mode in options for sid in slots)
            reachable = reachable or any(o['cid'] == cid and slots[o['sid']] > 0 for o in transfer_options)
            reason = 'no_safe_shelter_space' if not any(slots.values()) else 'no_compatible_vehicle_or_access' if not reachable else 'fleet_or_time_window_exhausted'
            remaining.append(dict(cluster_id=cid, name=cluster['name'], people=need[cid], reason=reason))

    served, left = initial-sum(need.values()), sum(need.values())
    recommendations = []
    if left and earliest:
        blocked = {mode: value for mode, value in earliest.items() if value > horizon}
        if blocked:
            mode, first = min(blocked.items(), key=lambda item: item[1])
            suggested = math.ceil(first/15)*15
            recommendations.append(dict(kind='planning_window' if suggested <= 240 else 'closer_base',
                title=f'Allow at least {suggested} minutes' if suggested <= 240 else 'Move the rescue base closer',
                message=f'Earliest fresh-vehicle shelter arrival using {mode} is {first:.1f} minutes; the current window is {horizon:g} minutes. Change the planning window in Advanced settings and rerun.',
                suggested_window_minutes=suggested if suggested <= 240 else None))
    if left > sum(slots.values()):
        recommendations.append(dict(kind='shelter_capacity', title='Add dry shelter capacity',
            message=f'Remaining demand exceeds dry residual shelter space by {left-sum(slots.values()):,} people. Extra vehicles alone cannot close this gap.'))
    if left and served and sum(slots.values()) > 0:
        active = [v for v in vehicles.values() if v['trips']]
        # Observed average, not an optimization result; handoff legs count once.
        throughput = served/len(active)
        additional = math.ceil(min(left, sum(slots.values()))/throughput)
        recommendations.append(dict(kind='fleet_capacity', title='Increase rescue capacity',
            message=f'This plan serves {served:,} people with {len(active)} active vehicles. At the same average yield, about {additional:,} additional vehicles would be needed for the remaining shelter-supported demand. This rough estimate ignores shared handoff bottlenecks; the simulator allows 30 vehicles total.',
            estimated_additional_vehicles=additional, estimate_only=True))
        idle_trucks = sum(v['mode'] == 'trucks' and not v['trips'] for v in vehicles.values())
        if idle_trucks and any(j['kind'] == 'boat_to_truck' for j in journeys):
            extra = min(idle_trucks, 20-config.boats.count, 30-len(vehicles))
            if extra > 0:
                recommendations.append(dict(kind='handoff_bottleneck', title='Pair idle trucks with additional boats',
                    message=f'{idle_trucks} trucks have no trip while boat handoffs use the available boats. Try adding up to {extra} boats and rerun; more trucks alone will not remove this bottleneck. This is a planning suggestion, not a guaranteed gain.',
                    suggested_additional_boats=extra))
    if left and config.boats.count and config.trucks.count and not config.enable_intermodal_transfers:
        recommendations.append(dict(kind='enable_transfers', title='Enable boat-to-truck transfers',
            message='Allow boats to meet trucks at modeled dry roadside points. Both vehicles and final shelter arrival must fit the window.'))
    if left and not served and not earliest:
        recommendations.append(dict(kind='access', title='Review fleet access and shelter availability',
            message='No compatible route reaches a dry shelter. Check flood depths, available vehicle modes, dry base access and shelter space.'))
    used_points = {j['transfer_point_id'] for j in journeys if j['kind'] == 'boat_to_truck'}
    forecast_report = ({key:value for key,value in road_forecast.items() if key not in ('graph','baseline','states')} | dict(alternative_legs=len(route_changes),blocked_legs=len(blocked_legs))) if road_forecast else None
    return dict(planning_window_minutes=horizon, snapshot_demand=initial, provisionally_served=served, still_needing_support=left,
        safe_shelter_spaces_before=sum(int(s['remaining_capacity']) for s in destinations.values()), safe_shelter_spaces_after=sum(slots.values()),
        trips=trips, journeys=journeys, transfer_points=[candidate_points[pid] for pid in sorted(used_points)],
        intermodal_served=sum(j['people'] for j in journeys if j['kind'] == 'boat_to_truck'),
        recommendations=recommendations, vehicles=list(vehicles.values()), unserved=remaining,
        road_forecast=forecast_report,
        semantics='Independent plan at this hour; no dispatch, no cumulative rescues, no changes to ground assignments or inventory.',
        limitations=['Flood conditions are frozen during the planning window; future accessibility is not guaranteed.',
            'Vehicles start at one configured base and return there before reuse; readiness delay applies per pool.',
            'Boat and helicopter legs are direct-distance proxies; launch, landing, docking, water continuity and air access are unverified.',
            'Transfer points are sampled dry road nodes within 8.5 km of pickup, not surveyed boat landing sites. Dry staging and supervised waiting are assumed.',
            'Truck graph and endpoint connectors are screened at 0.30 m; flow velocity and traffic forecasts are absent.',
            'Both handoff vehicles are reserved together. People count once, after final shelter unloading; intermediate boat legs are not additional rescues.',
            'Shelter reservations do not change ground assignments or supply inventory. Cargo transport uses a separate fleet.',
            'Greedy depth-priority scheduling and fleet-size extrapolations are estimates, not globally optimal solutions.'])
