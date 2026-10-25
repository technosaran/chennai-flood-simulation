"""Official ward membership with explicitly modeled planning indicators."""
import json
from pathlib import Path
from functools import lru_cache
from backend.app.services.geometry import haversine

DATA = Path(__file__).parents[1] / 'data'
GCC_SOURCE = 'https://gisgcc.chennaicorporation.gov.in/server/rest/services/GCCPublic/GCC_AdminBoundary/MapServer/4'


def in_ring(lon, lat, ring):
    inside = False
    for a, b in zip(ring, ring[1:] + ring[:1]):
        if (a[1] > lat) != (b[1] > lat) and lon < (b[0]-a[0]) * (lat-a[1]) / (b[1]-a[1]) + a[0]:
            inside = not inside
    return inside


def contains(geometry, location):
    lat, lon = location
    polygons = [geometry['coordinates']] if geometry['type'] == 'Polygon' else geometry['coordinates']
    return any(in_ring(lon, lat, polygon[0]) and not any(in_ring(lon, lat, hole) for hole in polygon[1:]) for polygon in polygons)


@lru_cache(maxsize=1)
def profiles():
    wards = json.loads((DATA / 'gcc_wards.geojson').read_text())['features']
    clusters = json.loads((DATA / 'population_clusters.json').read_text())
    shelters = json.loads((DATA / 'shelters.json').read_text())
    records, covered = [], set()
    for feature in sorted(wards, key=lambda f: int(f['properties']['ward'])):
        geometry = feature['geometry']
        rings = [geometry['coordinates']] if geometry['type'] == 'Polygon' else geometry['coordinates']
        points = [p for polygon in rings for p in polygon[0]]
        center = [sum(p[1] for p in points)/len(points), sum(p[0] for p in points)/len(points)]
        members = [c for c in clusters if contains(geometry, c['location'])]
        covered.update(c['id'] for c in members)
        nearest = sorted(shelters, key=lambda s: haversine(*center, *s['location']))[:3]
        records.append(dict(ward_id=feature['properties']['ward'], center=center,
                            modeled_clusters=members, modeled_population=sum(c['estimated_population'] for c in members) if members else None,
                            official_population=None, vulnerable_group_counts=None,
                            nearby_shelters=[dict(id=s['id'], name=s['name'], capacity=s['capacity'],
                                                 available_baseline_capacity=max(0, s['capacity']-s['current_occupancy']),
                                                 straight_line_km=round(haversine(*center, *s['location']), 2), amenities=s.get('amenities', [])) for s in nearest]))
    return dict(wards=records, outside_gcc_clusters=[c for c in clusters if c['id'] not in covered],
                sources=[dict(title='Greater Chennai Corporation published ward boundaries', url=GCC_SOURCE),
                         dict(title='GCC stormwater drainage context', url='https://chennaicorporation.gov.in/gcc/department/storm-water/'),
                         dict(title='CAG 2017 Chennai flood-management performance audit', url='https://cag.gov.in/ag1/tamil-nadu/en/audit-report/details/45722')],
                historical_context='The CAG 2017 audit examines flood management and response in Chennai and its suburbs. GCC identifies drainage and basin management as flood-mitigation work. These sources provide city context; they do not validate this project’s ward risk scores.',
                planning_checklist=['Assess assistance needs for older adults, children, people with disabilities and people requiring ongoing treatment.',
                                    'Check accessible shelter entrances, toilets, drinking water, backup power and medical support.',
                                    'Recheck road access and usable shelter capacity for the chosen simulation hour.'],
                limitations=['Published ward boundaries have no effective date supplied by the service.',
                             'Modeled cluster populations cover selected locations only; they are not official ward totals.',
                             'No verified vulnerable-group counts or ward-specific flood history are supplied.',
                             'Shelters and capacities are academic planning inputs, not verified operational facilities.',
                             'Nearby shelters use straight-line distance from a boundary vertex-average reference point, not a safe route or travel time.'])


if __name__ == '__main__':
    path = DATA.parents[2] / 'frontend/public/data/ward_profiles.json'
    path.write_text(json.dumps(profiles(), separators=(',', ':')), encoding='utf-8')
    print(f'Wrote {len(profiles()["wards"])} ward profiles to {path}')
