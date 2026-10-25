"""Conservative truck routing across the known scenario's upcoming flood states."""
import math
import networkx as nx
from backend.app.services.geometry import haversine


def screen_line(points, zones, flood):
    for a,b in zip(points,points[1:]):
        count=max(1,math.ceil(haversine(a[0],a[1],b[0],b[1])*1000/25))
        for i in range(count+1):
            point=[a[j]+(b[j]-a[j])*i/count for j in range(2)]
            if flood.get_point_depth(*point,zones)>=.3:
                return False
    return True


class RoadForecast:
    def __init__(self,timeline):
        self.timeline=timeline
        self.cached_key=None
        self.cached=None

    def context(self,minute,until,road,flood,zones):
        key=(minute,until)
        if key==self.cached_key:
            return self.cached
        future=[s for s in self.timeline if minute < s['time_elapsed_hours']*60 <= until+1e-6]
        states=[zones]+[s['zones_state'] for s in future]
        baseline=road.build_dynamic_graph(zones,closure_threshold_m=.3,slowdown_threshold_m=.1,mode='truck')
        screened=baseline.copy()
        for step in future:
            upcoming=road.build_dynamic_graph(step['zones_state'],closure_threshold_m=.3,slowdown_threshold_m=.1,mode='truck')
            for a,b in list(screened.edges()):
                if not upcoming.has_edge(a,b):
                    screened.remove_edge(a,b)
                    continue
                # Parallel OSM alternatives can change geometry between states.
                # Preserve only the actual selected curve, not just its endpoints.
                edge=screened[a][b]
                try: coords=road.get_route_coordinates([a,b],screened)
                except TypeError: coords=road.get_route_coordinates([a,b])
                if not screen_line(coords,step['zones_state'],flood):
                    screened.remove_edge(a,b)
                else:
                    edge['weight']=max(edge.get('weight',0),upcoming[a][b].get('weight',0))
        known_end=max((s['time_elapsed_hours']*60 for s in self.timeline),default=minute)
        data=dict(graph=screened,baseline=baseline,states=states,from_minutes=minute,
                  checked_until_minutes=min(until,known_end),requested_until_minutes=until,
                  states_checked=len(states),edges_closed_ahead=baseline.number_of_edges()-screened.number_of_edges(),
                  coverage='complete' if known_end>=until else 'partial')
        self.cached_key,self.cached=key,data
        return data

    def return_route(self,start,end,minute,until,road,flood,zones):
        context=self.context(minute,until,road,flood,zones)
        try:
            source,target=road.find_nearest_node(*start,mode='truck'),road.find_nearest_node(*end,mode='truck')
        except TypeError:
            source,target=road.find_nearest_node(*start),road.find_nearest_node(*end)
        try:
            path=nx.shortest_path(context['graph'],source,target,weight='weight')
            try: coords=road.get_route_coordinates(path,context['graph'])
            except TypeError: coords=road.get_route_coordinates(path)
        except (nx.NetworkXNoPath,nx.NodeNotFound):
            return None
        coords=[list(start)]+coords+[list(end)]
        return coords if all(screen_line(coords,state,flood) for state in context['states']) else None
