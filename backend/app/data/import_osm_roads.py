"""Acquire an offline Chennai street graph from OpenStreetMap via Overpass.

Run: python -m backend.app.data.import_osm_roads
No network is used by ordinary application startup. Preserve OSM node topology,
road curves, access and one-way direction; never join geometric crossings.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import gzip
import hashlib
import json
import math
from pathlib import Path
import re
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).parent
BOUNDS = (12.82, 80.03, 13.26, 80.34)
HIGHWAYS = {'motorway', 'motorway_link', 'trunk', 'trunk_link', 'primary', 'primary_link',
            'secondary', 'secondary_link', 'tertiary', 'tertiary_link', 'residential',
            'unclassified', 'living_street', 'service', 'pedestrian', 'footway', 'path', 'steps'}
SPEEDS = {'motorway': 60, 'trunk': 50, 'primary': 40, 'secondary': 35, 'tertiary': 30,
          'residential': 20, 'unclassified': 20, 'living_street': 10, 'service': 15}


def distance(a, b):
    la, lb = math.radians(a[0]), math.radians(b[0])
    x = math.sin((lb-la)/2)**2 + math.cos(la)*math.cos(lb)*math.sin(math.radians(b[1]-a[1])/2)**2
    return 6371 * 2 * math.atan2(math.sqrt(x), math.sqrt(max(0, 1-x)))


def allowed(tags, mode):
    # Specific access tags override general access. Destination access remains
    # available for facility approaches; private/no roads are excluded.
    keys = ('motorcar', 'motor_vehicle', 'vehicle', 'access') if mode == 'truck' else ('foot', 'access')
    access = next((tags[k] for k in keys if k in tags), 'yes')
    if access in ('no', 'private', 'agricultural', 'forestry'): return False
    road = tags.get('highway')
    if mode == 'truck': return road not in ('pedestrian', 'footway', 'path', 'steps')
    return road not in ('motorway', 'motorway_link', 'trunk', 'trunk_link') or tags.get('foot') in ('yes', 'designated', 'permissive')


def compile_network(raw):
    ways = [w for w in raw.get('elements', []) if w.get('type') == 'way' and
            w.get('tags', {}).get('highway') in HIGHWAYS and len(w.get('nodes', [])) == len(w.get('geometry', []))
            and len(w.get('nodes', [])) > 1 and (allowed(w['tags'], 'truck') or allowed(w['tags'], 'foot'))]
    if not ways: raise ValueError('No routable streets in source response')
    uses = Counter(n for w in ways for n in set(w['nodes']))
    nodes, edges = {}, []
    for way in ways:
        tags = way['tags']; ids = way['nodes']; geom = [[p['lat'], p['lon']] for p in way['geometry']]
        # Keep endpoints and true shared OSM nodes. Degree-two shape points stay
        # in edge geometry, reducing graph size without straightening streets.
        breaks = [i for i,n in enumerate(ids) if i in (0,len(ids)-1) or uses[n] > 1]
        truck, foot = allowed(tags, 'truck'), allowed(tags, 'foot')
        direction = tags.get('oneway', 'yes' if tags.get('junction') == 'roundabout' or tags.get('highway') == 'motorway' else 'no')
        if tags.get('oneway:motor_vehicle') in ('yes','no','-1'): direction = tags['oneway:motor_vehicle']
        # Conditional/reversible traffic cannot be resolved by a static snapshot.
        if direction in ('reversible', 'alternating'): truck = False
        speed = SPEEDS.get(tags['highway'].removesuffix('_link'), 20)
        match = re.fullmatch(r'(\d+(?:\.\d+)?)\s*(mph)?',tags.get('maxspeed',''))
        if match: speed = min(80, max(5, float(match[1])*(1.609344 if match[2] else 1)))
        for start,end in zip(breaks,breaks[1:]):
            if ids[start] == ids[end]: continue
            coords = geom[start:end+1];length = sum(distance(a,b) for a,b in zip(coords,coords[1:]))
            if length <= 0: continue
            for idx in (start,end):
                nid='OSM-'+str(ids[idx]);nodes[nid]={'id':nid,'lat':geom[idx][0],'lon':geom[idx][1]}
            for reverse in (False,True):
                motor = truck and (direction not in ('yes','1','true') if reverse else direction != '-1')
                walk = foot and (tags.get('oneway:foot') != ('yes' if reverse else '-1'))
                if not motor and not walk: continue
                src,tgt = ('OSM-'+str(ids[start]),'OSM-'+str(ids[end]))
                if reverse: src,tgt=tgt,src
                edges.append({'id':f"OSM-{way['id']}-{start}-{'r' if reverse else 'f'}",'source':src,'target':tgt,
                              'osm_way_id':way['id'],'road_name':tags.get('name',tags.get('ref',tags['highway'].replace('_',' '))),
                              'road_type':tags['highway'],'distance_km':round(length,7),'speed_kmh':speed,
                              'geometry':list(reversed(coords)) if reverse else coords,
                              'truck_allowed':motor,'foot_allowed':walk,
                              'bridge':tags.get('bridge','no'),'tunnel':tags.get('tunnel','no'),
                              # A mapped bridge is not verified hydraulic clearance.
                              'is_elevated':False,'layer':tags.get('layer','0'),
                              'access':tags.get('access','yes'),'capacity':8000})
    return {'metadata':{'source':'OpenStreetMap contributors / Overpass API','license':'ODbL',
                        'attribution_url':'https://www.openstreetmap.org/copyright','bounds':list(BOUNDS),
                        'osm_timestamp':raw.get('osm3s',{}).get('timestamp_osm_base'),
                        'retrieved_at':datetime.now(timezone.utc).isoformat(),'node_count':len(nodes),'directed_edge_count':len(edges),
                        'limitations':['Static OSM snapshot, not live road status.', 'Turn restrictions and conditional access are not resolved.',
                                       'Facility access connectors are unverified; mapped bridges do not establish flood clearance.']},
            'nodes':list(nodes.values()),'edges':edges}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache',type=Path,default=ROOT/'osm_roads_source.json.gz')
    parser.add_argument('--refresh',action='store_true')
    args=parser.parse_args()
    if args.cache.exists() and not args.refresh:
        raw_bytes=gzip.decompress(args.cache.read_bytes())
    else:
        bbox=','.join(map(str,BOUNDS));roads='|'.join(sorted(HIGHWAYS))
        query=f'[out:json][timeout:90];way["highway"~"^({roads})$"]({bbox});out body geom;'
        failures=[]
        for endpoint in ['https://overpass.kumi.systems/api/interpreter','https://overpass-api.de/api/interpreter']:
            try:
                req=Request(endpoint,data=urlencode({'data':query}).encode(),headers={'User-Agent':'ChennaiFloodLab-AcademicMap/1.0','Accept-Encoding':'gzip'})
                with urlopen(req,timeout=110) as res:
                    data=res.read();raw_bytes=gzip.decompress(data) if res.headers.get('Content-Encoding')=='gzip' else data
                raw=json.loads(raw_bytes)
                if raw.get('remark') or not raw.get('elements'):raise ValueError(raw.get('remark','Incomplete response'))
                args.cache.parent.mkdir(parents=True,exist_ok=True);args.cache.write_bytes(gzip.compress(raw_bytes));break
            except Exception as exc:failures.append(str(exc))
        else:raise RuntimeError('Street download failed: '+'; '.join(failures))
    graph=compile_network(json.loads(raw_bytes))
    if len(graph['nodes']) < 1000:raise ValueError('Refusing to replace street data with an incomplete graph')
    graph['metadata']['source_sha256']=hashlib.sha256(raw_bytes).hexdigest()
    target=ROOT/'chennai_osm_roads.json.gz';temp=target.with_suffix('.tmp')
    temp.write_bytes(gzip.compress(json.dumps(graph,separators=(',',':')).encode('utf-8')));temp.replace(target)
    print(json.dumps(graph['metadata'],indent=2),flush=True)


if __name__ == '__main__': main()
