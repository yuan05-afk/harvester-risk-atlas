"""Where to look next, from survey effort: the areas right next to a plant's records that botanists have barely or
never searched. A plant recorded in one cell is likely to grow in the neighbouring cells too; where those cells hold
almost no plant records of any kind, its absence there means nothing yet, so they are the cheapest places to look.

    .venv/Scripts/python.exe scripts/survey_gaps.py      (needs h3; run after scripts/name_check.py)

For each scored plant: its occupied H3 res-5 cells, their land neighbours (one ring), and how many of those neighbours
are never searched (0 vascular-plant records in GBIF) or under-searched (< 100, the atlas's well-searched threshold).
Counts only are published; the neighbour cells themselves are not, so no finer location is revealed.
"""
import gzip
import json
from pathlib import Path

import h3

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / 'web' / 'public' / 'data'
counts = json.load(gzip.open(ROOT / 'data/raw/effort/tracheophyta_ph_h3r5.json.gz'))['counts']
land = {f['properties'].get('h3') for f in json.load(open(WEB / 'geo' / 'cells.geojson', encoding='utf-8'))['features']}
land.discard(None)
WELL = 100

species = json.load(open(WEB / 'species.json', encoding='utf-8'))
total = {'plants': 0, 'neighbours': 0, 'never': 0, 'under': 0}
for s in species:
    if s.get('tier') == 'Not scored':
        continue
    p = WEB / 'species' / f"{s['slug']}.json"
    d = json.load(open(p, encoding='utf-8'))
    occ = set(d.get('cells') or [])
    ring = set()
    for c in occ:
        ring |= set(h3.grid_disk(c, 1))
    ring -= occ
    ring = {c for c in ring if c in land} if land else ring
    never = sum(1 for c in ring if counts.get(c, 0) == 0)
    under = sum(1 for c in ring if 0 < counts.get(c, 0) < WELL)
    d.setdefault('check', {})['survey'] = {'neighbours': len(ring), 'never': never, 'under': under, 'threshold': WELL}
    json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    total['plants'] += 1
    total['neighbours'] += len(ring)
    total['never'] += never
    total['under'] += under
    print(f"{s['name']:30s} occupied {len(occ):3d}  neighbours {len(ring):3d}  never searched {never:3d}  under-searched {under:3d}")
m = json.load(open(WEB / 'manifest.json', encoding='utf-8'))
m.setdefault('name_check', {})['survey'] = total
json.dump(m, open(WEB / 'manifest.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(total)
