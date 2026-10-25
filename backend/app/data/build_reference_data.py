"""Bundle official GCC ward boundaries, OSM rivers and the modeled road graph.

Run from project root: python -m backend.app.data.build_reference_data
No tile downloading; ordinary use reads bundled vectors only.
"""
import hashlib
import gzip
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen

ROOT = Path(__file__).parent
PUBLIC = ROOT.parents[2] / 'frontend/public/data'
GCC = 'https://gisgcc.chennaicorporation.gov.in/server/rest/services/GCCPublic/GCC_AdminBoundary/MapServer/4'


def build_roads():
    """Rebuild offline streets without downloading wards or waterways."""
    path = ROOT / 'chennai_osm_roads.json.gz'
    with gzip.open(path, 'rt', encoding='utf-8') as stream:
        network = json.load(stream)
    # City overview uses arterial streets; routes retain all local access roads.
    overview = {'motorway','motorway_link','trunk','trunk_link','primary','primary_link',
                'secondary','secondary_link','tertiary','tertiary_link'}
    seen, lines = set(), []
    for edge in network['edges']:
        if edge['road_type'] not in overview: continue
        key = (edge['osm_way_id'], tuple(sorted((edge['source'],edge['target']))))
        if key in seen: continue
        seen.add(key)
        lines.append({'type':'Feature','properties':{'name':edge['road_name'],'highway':edge['road_type']},
                      'geometry':{'type':'LineString','coordinates':[[lon,lat] for lat,lon in edge['geometry']]}})
    PUBLIC.mkdir(parents=True,exist_ok=True)
    (PUBLIC/'offline_roads.json').write_text(json.dumps({'type':'FeatureCollection','metadata':network['metadata'],'features':lines},separators=(',',':')),encoding='utf-8')
    manifest_path=PUBLIC/'reference_manifest.json'
    manifest=json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    manifest.update(roads_source=network['metadata']['source'],roads_metadata=network['metadata'])
    manifest.setdefault('files',{})['offline_roads.json']=hashlib.sha256((PUBLIC/'offline_roads.json').read_bytes()).hexdigest()
    manifest_path.write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print(f"Bundled {len(lines)} OSM street segments")
    return lines


def build():
    PUBLIC.mkdir(parents=True, exist_ok=True)
    ward_url = GCC + '/query?' + urlencode(dict(where='1=1', outFields='ward', outSR=4326, f='geojson', geometryPrecision=5))
    with urlopen(ward_url, timeout=90) as response:
        wards = json.load(response)
    if wards.get('type') != 'FeatureCollection' or len(wards.get('features', [])) != 200:
        raise ValueError('Expected all 200 GCC ward polygons; refusing incomplete reference data')
    for feature in wards['features']:
        feature['properties'] = {'ward': str(feature['properties']['ward']).strip()}
    output = ROOT / 'gcc_wards.geojson'
    output.write_text(json.dumps(wards, separators=(',', ':')), encoding='utf-8')
    (PUBLIC / 'gcc_wards.json').write_bytes(output.read_bytes())
    lines = build_roads()
    query = '[out:json][timeout:30];way[waterway=river](12.8,80.05,13.3,80.35);out geom;'
    river_url = 'https://overpass.private.coffee/api/interpreter?' + urlencode({'data': query})
    try:
        with urlopen(river_url, timeout=65) as response:
            raw_rivers = json.load(response)
        rivers = {'type': 'FeatureCollection', 'features': [
            {'type': 'Feature', 'properties': {'name': way['tags'].get('name', 'Waterway')},
             'geometry': {'type': 'LineString', 'coordinates': [[p['lon'], p['lat']] for p in way['geometry']]}}
            for way in raw_rivers['elements'] if len(way.get('geometry', [])) > 1]}
        if not rivers['features']:
            raise ValueError('No waterways returned')
        (PUBLIC / 'offline_rivers.json').write_text(json.dumps(rivers, separators=(',', ':')), encoding='utf-8')
    except Exception as exc:
        if not (PUBLIC / 'offline_rivers.json').exists():
            raise RuntimeError('River download failed; rerun instead of inventing waterways') from exc
        print('Keeping existing bundled rivers:', exc)
    manifest = {'retrieved_at': datetime.now(timezone.utc).isoformat(), 'ward_count': 200,
                'ward_source': GCC, 'ward_query': ward_url, 'ward_vintage': 'Effective boundary date not supplied by source',
                'roads_source': 'OpenStreetMap contributors / Overpass API',
                'river_source': 'OpenStreetMap contributors / Overpass API', 'river_query': river_url,
                'river_license': 'https://www.openstreetmap.org/copyright',
                'files': {name: hashlib.sha256((PUBLIC / name).read_bytes()).hexdigest()
                          for name in ('gcc_wards.json', 'offline_roads.json', 'offline_rivers.json')}}
    (PUBLIC / 'reference_manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    from backend.app.services.ward_profiles import profiles
    profiles.cache_clear()
    (PUBLIC / 'ward_profiles.json').write_text(json.dumps(profiles(), separators=(',', ':')), encoding='utf-8')
    print(json.dumps({'wards': 200, 'roads': len(lines), 'files': manifest['files']}, indent=2))


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument("--roads-only",action="store_true")
    args=parser.parse_args()
    build_roads() if args.roads_only else build()
