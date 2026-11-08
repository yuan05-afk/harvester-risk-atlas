"""Map shapes for the film (src/geo.json): the Philippines' outline, every res-5 cell with its survey effort,
tongkat ali's five cells, and the islands Co's Digital Flora documents it on. Projected to a 1000-px-tall frame.

    ../.venv/Scripts/python.exe tools/geo.py
"""
import json
import math
from pathlib import Path

import h3

ROOT = Path(__file__).resolve().parents[2]
GEO = ROOT / 'web' / 'public' / 'data' / 'geo'
W0, S0, E0, N0 = 116.4, 4.4, 127.0, 21.2
K = 1000 / (N0 - S0)
COS = math.cos(math.radians(12.5))


def xy(lon, lat):
    return round((lon - W0) * K * COS, 1), round((N0 - lat) * K, 1)


def ring_path(ring):
    pts = [xy(*p[:2]) for p in ring]
    # Drop points closer than 1.2 px to the last kept one: the outline stays crisp at film size, the file small.
    out = [pts[0]]
    for p in pts[1:]:
        if abs(p[0] - out[-1][0]) + abs(p[1] - out[-1][1]) >= 1.2:
            out.append(p)
    if len(out) < 4:
        return ''
    return 'M' + 'L'.join(f'{x},{y}' for x, y in out) + 'Z'


land = json.load(open(GEO / 'land.geojson', encoding='utf-8'))
paths = []
for f in land['features']:
    g = f['geometry']
    polys = g['coordinates'] if g['type'] == 'MultiPolygon' else [g['coordinates']]
    for poly in polys:
        p = ring_path(poly[0])
        if p:
            paths.append(p)

# Survey effort at the country view's cell size (H3 res 4, as the app shows it zoomed out): the share of each res-4
# cell's res-5 children that are well searched (100+ plant records).
cells = json.load(open(GEO / 'cells.geojson', encoding='utf-8'))
kids = {}
for f in cells['features']:
    p = f['properties']
    parent = h3.cell_to_parent(p['h3'], 4)
    kids.setdefault(parent, []).append(p['effort'] >= 100)
eff = []
for c, flags in kids.items():
    lat, lon = h3.cell_to_latlng(c)
    x, y = xy(lon, lat)
    eff.append([x, y, round(sum(flags) / len(flags), 2)])
effs = sorted(e[2] for e in eff)

sp = json.load(open(ROOT / 'web/public/data/species/eurycoma-longifolia.json', encoding='utf-8'))
tongkat = []
for c in sp['cells_r4']:
    lat, lon = h3.cell_to_latlng(c)
    tongkat.append(xy(lon, lat))
places = {'Mindoro': (121.08, 12.93), 'Homonhon': (125.72, 10.73), 'Bucas Grande': (125.97, 9.66)}
look = {k: xy(*v) for k, v in places.items()}

out = {'w': round((E0 - W0) * K * COS), 'h': 1000, 'land': paths, 'cells': eff, 'tongkat': tongkat, 'look': look,
       'cell_r': round(h3.average_hexagon_edge_length(4, 'km') / 111 * K, 2)}
json.dump(out, open(ROOT / 'video/src/geo.json', 'w'), separators=(',', ':'))
print(len(paths), 'land rings', len(eff), 'cells, effort quantiles', effs[len(effs) // 2], effs[int(len(effs) * 0.75)], 'tongkat', tongkat, out['w'])
