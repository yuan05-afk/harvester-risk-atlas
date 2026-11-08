"""Cross-checks every plant in the atlas against two expert sources, and finds where to look next.

    python scripts/name_check.py            # fetches (and caches) the sources, writes the check, patches the web data

Sources
- World Flora Online (WFO) Plant List, the backbone the EthnoHack datasets guide recommends: name match, WFO ID,
  accepted or synonym, and the accepted name.
- Co's Digital Flora of the Philippines (CDFP; Pelser, Barcelona & Nickrent, eds., 2011 onwards,
  www.philippineplants.org), the expert checklist founded on Leonardo L. Co's work: whether the name is in the
  Philippine flora, its status there (native, endemic, introduced), its Philippine distribution, and the IUCN and
  DAO categories it gives. CDFP pages are cached locally under data/raw/cdfp/ but not committed: CDFP permits use with
  citation but not republishing substantial amounts, so only the facts for these 51 plants are published.

What it computes for each plant
- agreement of our nativity gate (WCVP) with CDFP's status, and of our DENR category with CDFP's DAO category;
- record check: which provinces in our cleaned GBIF records fall inside CDFP's documented distribution;
- look next: places CDFP documents for the plant where open data holds no reliable record (survey targets);
- double-check: provinces with open records outside CDFP's documented distribution (possible misidentification).
Places are compared by their name stem ("Surigao del Sur" -> "surigao"), so a province matches its island or the
province named in CDFP. Province-level only: no finer location is ever published.
"""
from __future__ import annotations

import csv
import datetime as dt
import html
import json
import re
import time
import urllib.parse
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / 'data' / 'raw' / 'cdfp'
WEB = ROOT / 'web' / 'public' / 'data'
OUT = ROOT / 'data' / 'processed' / 'v2' / 'name_check.csv'
TODAY = dt.date.today().isoformat()
UA = {'User-Agent': 'harvester-risk-atlas name check (EthnoHack 2026; research use)'}


def _retry(fn):
    for k in range(4):
        try:
            return fn()
        except (OSError, urllib.error.URLError):
            if k == 3:
                raise
            time.sleep(3 * (k + 1))


def get(url: str) -> str:
    def go():
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40) as r:
            return r.read().decode('utf-8', 'replace')
    return _retry(go)


def text_of(h: str) -> str:
    h = re.sub(r'<script.*?</script>', ' ', h, flags=re.S)
    return html.unescape(re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', h)))


# ----------------------------------------------------------------------------------------------------- WFO
def _gql(query: str) -> dict:
    def go():
        req = urllib.request.Request('https://list.worldfloraonline.org/gql.php', data=json.dumps({'query': query}).encode(), headers={**UA, 'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=40) as r:
            return json.loads(r.read())['data']
    return _retry(go)


def _role(wfo_id: str) -> str:
    return (_gql('{ taxonNameById(nameId: "%s") { role } }' % wfo_id)['taxonNameById'] or {}).get('role', '')


def wfo(name: str) -> dict:
    q = urllib.parse.quote(name)
    d = json.loads(get(f'https://list.worldfloraonline.org/matching_rest.php?input_string={q}'))
    m = d.get('match') or {}
    note = ''
    if not m:
        # Homonyms (the same binomial by different authors): take the one WFO places in its classification.
        sp = name.split()[-1]
        placed = [c for c in d.get('candidates', []) if (c.get('placement') or '').endswith('/' + sp)]
        if not placed:
            return {'wfo_id': '', 'wfo_name': '', 'wfo_role': 'no match', 'wfo_accepted': '', 'wfo_note': f"{len(d.get('candidates', []))} candidates, none placed"}
        # Prefer the placed candidate WFO accepts (e.g. Artemisia vulgaris L., not the synonym A. vulgaris Burm.f.).
        m = placed[0]
        for c in placed:
            if _role(c['wfo_id']) == 'accepted':
                m = c
                break
        note = f"homonym: {len(d.get('candidates', []))} candidates; the accepted placed one used"
    n = _gql('{ taxonNameById(nameId: "%s") { id fullNameStringPlain role currentPreferredUsage { hasName { id fullNameStringPlain } } } }' % m['wfo_id'])['taxonNameById']
    acc = ((n.get('currentPreferredUsage') or {}).get('hasName') or {})
    strip = lambda s: re.sub(r'<[^>]+>', '', s or '')
    return {'wfo_id': n['id'], 'wfo_name': strip(n["fullNameStringPlain"]), 'wfo_role': n.get('role', ''),
            'wfo_accepted': strip(acc.get("fullNameStringPlain", "")), 'wfo_note': note}


# ---------------------------------------------------------------------------------------------------- CDFP
def family_page(family: str) -> str:
    RAW.mkdir(parents=True, exist_ok=True)
    f = RAW / f'{family}.html'
    if not f.exists():
        # CDFP's host blocks automated requests, so pages are saved by a person in a browser (see README) and read
        # from data/raw/cdfp/. A family without a saved page is reported as not checked, never as not listed.
        raise RuntimeError('page not saved; not checked')
    h = f.read_text(encoding='utf-8')
    if 'Distribution:' not in h:
        raise RuntimeError('page not available; not checked')
    return text_of(h)


STATUS = re.compile(r'\b(Native|Endemic|Introduced|Naturalized|Cultivated)\b\.')


def cdfp_entry(t: str, name: str) -> dict:
    """The block for `name`: from its accepted entry (or a synonym line, '= name') to the next entry."""
    g, s = name.replace('×', '').split()[:2] if '×' not in name else (name.split()[0], name.split()[-1])
    pat = re.compile(rf'(?<![=≡] )\b{re.escape(g)} {re.escape(s)}\b')
    syn = re.compile(rf'[=≡] {re.escape(g)} {re.escape(s)}\b')
    m = pat.search(t)
    via = ''
    if not m:
        sm = syn.search(t)
        if not sm:
            return {'cdfp_listed': False}
        # The accepted entry is the last "Genus species Author ," before the synonym line.
        heads = [h for h in re.finditer(r'(?:(?<=\. )|(?<=\d\. ))([A-Z][a-z]+ [a-z][a-z-]+) [A-Z(]', t[: sm.start()])]
        if not heads:
            return {'cdfp_listed': False}
        m = heads[-1]
        via = m.group(1)
    start = m.start()
    nxt = re.search(r' Distribution:.*?(?:Native|Endemic|Introduced|Naturalized|Cultivated)\.', t[start:])
    block = t[start: start + (nxt.end() if nxt else 1500)]
    dist = re.search(r'Distribution: (.*?)(?: Notes:| Conservation status:| DAO category:| Native\.| Endemic\.| Introduced\.| Naturalized\.| Cultivated\.)', block)
    iucn = re.search(r'Conservation status: ([^.]*?\(IUCN [\d.]+\))', block)
    dao = re.search(r'DAO category: ([^.]+)\.', block)
    st = STATUS.findall(block)
    return {'cdfp_listed': True, 'cdfp_name': via or f'{g} {s}', 'cdfp_status': st[-1] if st else '',
            'cdfp_distribution': dist.group(1).strip() if dist else '', 'cdfp_iucn': iucn.group(1) if iucn else '',
            'cdfp_dao': dao.group(1).strip() if dao else ''}


# Words that are not places when splitting CDFP's Philippine distribution.
NOT_PLACE = {'endemic to the philippines', 'philippines', 'photos', 'photo', 'cultivated', 'widely cultivated', 'throughout the philippines', 'throughout'}
COUNTRY_HINT = re.compile(r'\b(Borneo|Sumatra|Java|China|India|Malay|Myanmar|Thailand|Vietnam|Cambodia|Laos|Taiwan|Japan|Australia|New Guinea|Sulawesi|Moluccas|Africa|America|Asia|Pacific|Sri Lanka|Singapore|Indonesia|Bangladesh|Nepal|Bhutan|Solomon|Bismarck|Micronesia|Polynesia|Madagascar|Mascarenes|Hainan|Ryukyu|Lesser Sunda|Andaman|Nicobar|Korea|Pakistan|Arabia|Europe|Mexico|Brazil|Caribbean|tropics|Tropics|Cosmopolitan|Pantropical|Malesia)\b')


def ph_places(dist: str) -> list[str]:
    """Philippine places in a CDFP distribution: islands in capitals, provinces after a colon."""
    parts = [p.strip() for p in dist.split('.') if p.strip()]
    ph = [p for p in parts if not COUNTRY_HINT.search(p) and p.lower() not in NOT_PLACE]
    places: list[str] = []
    for p in ph:
        for chunk in re.split(r',\s*(?=[A-Z]{3,}|[A-Z][a-z])', p):
            chunk = re.sub(r'\((?:photos?|[^)]*)\)', '', chunk).strip(' ,')
            if ':' in chunk:
                island, provs = chunk.split(':', 1)
                places += [x.strip() for x in provs.split(',') if x.strip()]
            elif chunk and chunk.lower() not in NOT_PLACE and not chunk.lower().startswith('endemic'):
                places.append(chunk)
    seen, out = set(), []
    for p in places:
        k = p.lower()
        if k not in seen and len(k) > 2:
            seen.add(k)
            out.append(p)
    return out


def stem(place: str) -> str:
    s = place.lower()
    s = re.sub(r'\b(del norte|del sur|occidental|oriental|islands?|island|province|city|norte|sur|group|is\.)\b', '', s)
    s = re.sub(r'[^a-z ]', ' ', s)
    return re.sub(r'\s+', ' ', s).strip().split(' ')[0] if s.strip() else ''


def title(p: str) -> str:
    return ' '.join(w.capitalize() if w.isupper() else w for w in p.split())


CURATED = {r['scientific_name']: r for r in csv.DictReader(open(ROOT / 'data/curated/cdfp_facts.csv', encoding='utf-8'))}


def main() -> None:
    cohort = list(csv.DictReader(open(ROOT / 'data/curated/cohort.csv', encoding='utf-8')))
    species = json.load(open(WEB / 'species.json', encoding='utf-8'))
    by_name = {s['name']: s for s in species}
    rows = []
    for c in cohort:
        name = c['scientific_name']
        fam = c['family'].strip()
        w = wfo(name.replace('× ', '×'))  # WFO parses hybrids written "Mentha ×piperita"
        try:
            e = cdfp_entry(family_page(fam), name)
            e['cdfp_checked'] = True
        except Exception as ex:  # a family page that cannot be read is reported, never guessed
            e = dict(CURATED[name], cdfp_listed=True, cdfp_checked=True) if name in CURATED else {'cdfp_listed': False, 'cdfp_checked': False, 'cdfp_error': str(ex)[:80]}
        s = by_name.get(name, {})
        detail = json.load(open(WEB / 'species' / f"{s['slug']}.json", encoding='utf-8')) if s else {}
        ours = [p['name'] if isinstance(p, dict) else p for p in (detail.get('provinces') or [])]
        cdfp_places = ph_places(e.get('cdfp_distribution', ''))
        cstems = {stem(p) for p in cdfp_places} - {''}
        confirmed = [p for p in ours if stem(p) in cstems]
        double = [p for p in ours if stem(p) not in cstems] if e.get('cdfp_listed') and cstems else []
        ostems = {stem(p) for p in ours}
        look = [title(p) for p in cdfp_places if stem(p) not in ostems and stem(p)]
        our_native = (s.get('ph_status') == 'native') if s else None
        cstat = e.get('cdfp_status', '')
        cdfp_native = None if not cstat else cstat in ('Native', 'Endemic')
        rows.append({
            'scientific_name': name, 'family': fam, **w,
            'cdfp_checked': e.get('cdfp_checked', False), 'cdfp_listed': e.get('cdfp_listed', False), 'cdfp_name': e.get('cdfp_name', ''), 'cdfp_status': cstat,
            'cdfp_iucn': e.get('cdfp_iucn', ''), 'cdfp_dao': e.get('cdfp_dao', ''),
            'our_wcvp_status': s.get('ph_status', ''), 'our_dao': s.get('dao') or '',
            'nativity_agrees': '' if cdfp_native is None or our_native is None else cdfp_native == our_native,
            'dao_agrees': '' if not e.get('cdfp_checked') or not (e.get('cdfp_dao') or s.get('dao')) else _dao(s.get('dao')) == _dao(e.get('cdfp_dao')),
            'record_provinces': len(ours), 'confirmed_provinces': len(confirmed),
            'look_next': '; '.join(look[:8]), 'double_check': '; '.join(double),
            'cdfp_url': f'https://www.philippineplants.org/Families/{fam}.html', 'checked': TODAY,
        })
        print(f"{name:32s} WFO {w['wfo_role'] or '-':9s} CDFP {cstat or ('listed' if e.get('cdfp_listed') else 'not found'):10s} "
              f"ours {s.get('ph_status',''):11s} records {len(confirmed)}/{len(ours)} confirmed  look-next {len(look)}")
        time.sleep(0.3)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, 'w', newline='', encoding='utf-8') as f:
        wr = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        wr.writeheader()
        wr.writerows(rows)
    patch_web(rows)


def _dao(v: str | None) -> str:
    v = (v or '').lower()
    for k, short in [('critically', 'CR'), ('endangered', 'EN'), ('vulnerable', 'VU'), ('other threatened', 'OTS')]:
        if k in v:
            return short
    return v.upper().strip()


def patch_web(rows: list[dict]) -> None:
    """Adds `check` to each plant's JSON and a summary to manifest.json; the app reads both."""
    species = json.load(open(WEB / 'species.json', encoding='utf-8'))
    by_name = {s['name']: s for s in species}
    summary = {'checked': TODAY, 'n': len(rows), 'wfo_matched': 0, 'wfo_accepted': 0, 'cdfp_listed': 0,
               'nativity_agree': 0, 'nativity_disagree': [], 'dao_disagree': [], 'records': 0, 'records_confirmed': 0, 'with_look_next': 0}
    for r in rows:
        s = by_name.get(r['scientific_name'])
        if not s:
            continue
        check = {
            'wfo': {'id': r['wfo_id'], 'name': r['wfo_name'], 'role': r['wfo_role'], 'accepted': r['wfo_accepted']},
            'cdfp': {'checked': r['cdfp_checked'], 'listed': r['cdfp_listed'], 'name': r['cdfp_name'], 'status': r['cdfp_status'], 'iucn': r['cdfp_iucn'],
                     'dao': r['cdfp_dao'], 'url': r['cdfp_url']},
            'nativity_agrees': r['nativity_agrees'], 'dao_agrees': r['dao_agrees'],
            'records': r['record_provinces'], 'confirmed': r['confirmed_provinces'],
            'look_next': [p for p in r['look_next'].split('; ') if p], 'double_check': [p for p in r['double_check'].split('; ') if p],
            'checked': r['checked'],
        }
        p = WEB / 'species' / f"{s['slug']}.json"
        d = json.load(open(p, encoding='utf-8'))
        d['check'] = check
        json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
        s['check'] = {'cdfp': r['cdfp_status'] or ('listed' if r['cdfp_listed'] else ''), 'agrees': r['nativity_agrees'], 'look': len(check['look_next'])}
        summary['wfo_matched'] += bool(r['wfo_id'])
        summary['wfo_accepted'] += r['wfo_role'] == 'accepted'
        summary['cdfp_listed'] += bool(r['cdfp_listed'])
        summary['cdfp_checked'] = summary.get('cdfp_checked', 0) + bool(r['cdfp_checked'])
        if r['nativity_agrees'] is True:
            summary['nativity_agree'] += 1
        elif r['nativity_agrees'] is False:
            summary['nativity_disagree'].append(r['scientific_name'])
        if r['dao_agrees'] is False:
            summary['dao_disagree'].append(r['scientific_name'])
        summary['records'] += r['record_provinces']
        summary['records_confirmed'] += r['confirmed_provinces']
        summary['with_look_next'] += bool(check['look_next']) and s.get('tier') != 'Not scored'
    json.dump(species, open(WEB / 'species.json', 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    m = json.load(open(WEB / 'manifest.json', encoding='utf-8'))
    m['name_check'] = summary
    src = [x for x in m.get('sources', []) if x.get('id') not in ('cdfp', 'wfo')]
    src += [
        {'id': 'cdfp', 'name': "Co's Digital Flora of the Philippines (Pelser, Barcelona & Nickrent, eds., 2011 onwards)", 'use': 'expert cross-check: status, Philippine distribution, IUCN and DAO categories', 'licence': 'Use with citation; no bulk republication', 'url': 'https://www.philippineplants.org/', 'accessed': TODAY},
        {'id': 'wfo', 'name': 'World Flora Online Plant List', 'use': 'name check: WFO ID, accepted name or synonym', 'licence': 'CC0 (backbone data)', 'url': 'https://list.worldfloraonline.org/', 'accessed': TODAY},
    ]
    m['sources'] = src
    json.dump(m, open(WEB / 'manifest.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(json.dumps(summary, indent=1))


if __name__ == '__main__':
    main()
