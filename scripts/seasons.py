"""Season timeline: when each plant is recorded, flowering and fruiting through the year, corrected for when people look.

    .venv/Scripts/python.exe scripts/seasons.py      (needs h3; fetches GBIF's public occurrence API, no key)

For every cohort taxon, GBIF occurrence search (country=PH) gives each record's month and, where the observer noted it,
its reproductive condition (mostly iNaturalist annotations: flowering, fruiting). Months are joined to the atlas's
cleaned records by GBIF id, so the map uses only reliable records. Survey effort per month is the count of all
Philippine vascular-plant records in that month (Tracheophyta, the same target group as the rarity layer):
records peak in March to May, so raw monthly counts mostly show when people go out. The activity index divides a
plant's share of records in a month by the share of all plant records in that month: 1 means "as expected from effort",
above 1 "recorded more than effort explains".

Seasons follow PAGASA's two-season climate: dry December to May, wet June to November.
What this cannot show: seed spread, die-back or harvest timing; no dataset measures those, and the page says so.
"""
from __future__ import annotations

import csv
import datetime as dt
import gzip
import http.client
import json
import subprocess
import time
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import h3
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / 'web' / 'public' / 'data'
API = 'https://api.gbif.org/v1/occurrence/search'
DRY = {12, 1, 2, 3, 4, 5}
UA = {'User-Agent': 'harvester-risk-atlas seasons (EthnoHack 2026; research use)', 'Accept-Encoding': 'gzip'}


def get(params: dict) -> dict:
    # curl, not urllib: on Windows urllib takes ~20 s per page here (slow connection setup), curl about 1 s.
    url = API + '?' + urllib.parse.urlencode(params)
    for k in range(6):
        r = subprocess.run(['curl', '-s', '--compressed', '-m', '90', '-A', UA['User-Agent'], url], capture_output=True)
        if r.returncode == 0:
            try:
                return json.loads(r.stdout)
            except ValueError:
                pass
        time.sleep(5 * (k + 1))
    raise RuntimeError('GBIF unreachable: ' + url)


def phase(rc: str | None) -> set[str]:
    s = (rc or '').lower()
    if not s or 'no evidence' in s or 'no flowers' in s:
        return set()
    out = set()
    if 'flower' in s or 'bud' in s or 'anthesis' in s:
        out.add('flowering')
    if 'fruit' in s or 'seed' in s:
        out.add('fruiting')
    return out


def main() -> None:
    effort = {int(c['name']): c['count'] for c in get({'country': 'PH', 'taxonKey': 7707728, 'limit': 0, 'facet': 'month', 'facetLimit': 12})['facets'][0]['counts']}
    eff_total = sum(effort.values())
    taxa = {r['scientific_name']: int(float(r['gbif_taxon_key'])) for r in csv.DictReader(open(ROOT / 'data/processed/v2/taxa.csv', encoding='utf-8')) if r['gbif_taxon_key']}
    clean = pd.read_parquet(ROOT / 'data/processed/v2/records_clean.parquet', columns=['scientific_name', 'gbif_id', 'lat', 'lon'])
    clean['gbif_id'] = clean['gbif_id'].astype('int64')
    species = json.load(open(WEB / 'species.json', encoding='utf-8'))
    by_name = {s['name']: s for s in species}
    taxa = {n: k for n, k in taxa.items() if n in by_name}
    # GBIF answers a deep page in 20-30 s at times, so pages are fetched in parallel.
    counts = {n: get({'country': 'PH', 'taxonKey': k, 'limit': 0})['count'] for n, k in taxa.items()}
    jobs = [(n, off) for n in taxa for off in range(0, min(counts[n], 3000), 300)]
    print(len(jobs), 'pages for', len(taxa), 'plants', flush=True)
    with ThreadPoolExecutor(8) as ex:
        got = list(ex.map(lambda j: (j[0], get({'country': 'PH', 'taxonKey': taxa[j[0]], 'limit': 300, 'offset': j[1]})), jobs))
    pages = defaultdict(list)
    for n, page in got:
        pages[n].append(page)
    summary = []
    for name, key in taxa.items():
        s = by_name.get(name)
        if not s:
            continue
        month_of, flow, fruit, all_m = {}, Counter(), Counter(), Counter()
        for page in pages[name]:
            for r in page['results']:
                m = r.get('month')
                if not m:
                    continue
                month_of[int(r['key'])] = m
                all_m[m] += 1
                ph = phase(r.get('reproductiveCondition'))
                flow[m] += 'flowering' in ph
                fruit[m] += 'fruiting' in ph
        recs = clean[clean['scientific_name'] == name]
        cells = defaultdict(set)
        rec_m = Counter()
        for gid, lat, lon in recs[['gbif_id', 'lat', 'lon']].itertuples(index=False):
            m = month_of.get(int(gid))
            if m:
                rec_m[m] += 1
                cells[m].add(h3.latlng_to_cell(lat, lon, 5))
        n_all = sum(all_m.values())
        months = []
        for m in range(1, 13):
            share = all_m[m] / n_all if n_all else 0
            idx = share / (effort[m] / eff_total) if n_all else 0
            months.append({'m': m, 'all': all_m[m], 'records': rec_m[m], 'flowering': flow[m], 'fruiting': fruit[m], 'index': round(idx, 3)})
        dry_share = sum(all_m[m] for m in DRY) / n_all if n_all else None
        dry_expected = sum(effort[m] for m in DRY) / eff_total
        seasons = {
            'months': months, 'n': n_all, 'n_flowering': sum(flow.values()), 'n_fruiting': sum(fruit.values()),
            'dry_share': None if dry_share is None else round(dry_share, 3), 'dry_expected': round(dry_expected, 3),
            'cells': {str(m): sorted(cells[m]) for m in range(1, 13) if cells[m]},
            'cells_r4': {str(m): sorted({h3.cell_to_parent(c, 4) for c in cells[m]}) for m in range(1, 13) if cells[m]},
            'fetched': dt.date.today().isoformat(),
        }
        p = WEB / 'species' / f"{s['slug']}.json"
        d = json.load(open(p, encoding='utf-8'))
        d['seasons'] = seasons
        json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
        summary.append({'slug': s['slug'], 'name': name, 'vernacular': s.get('vernacular'), 'tier': s.get('tier'), 'ph_status': s.get('ph_status'),
                        'n': n_all, 'counts': [x['all'] for x in months], 'n_flowering': seasons['n_flowering'], 'n_fruiting': seasons['n_fruiting'],
                        'index': [x['index'] for x in months], 'flowering': [x['flowering'] for x in months], 'fruiting': [x['fruiting'] for x in months],
                        'dry_share': seasons['dry_share']})
        print(f"{name:30s} n {n_all:4d}  flowering {seasons['n_flowering']:3d}  fruiting {seasons['n_fruiting']:3d}  dry share {seasons['dry_share']}  (expected {seasons['dry_expected']})")
    json.dump({'effort': [effort[m] for m in range(1, 13)], 'dry': sorted(DRY), 'fetched': dt.date.today().isoformat(), 'species': summary},
              open(WEB / 'seasons.json', 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    m = json.load(open(WEB / 'manifest.json', encoding='utf-8'))
    m['seasons'] = {'fetched': dt.date.today().isoformat(), 'effort': [effort[k] for k in range(1, 13)], 'n_species': len(summary)}
    json.dump(m, open(WEB / 'manifest.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)


if __name__ == '__main__':
    main()
