"""Build the Track 3 catalog snapshot from Wikidata and GBIF.

IUCN categories are copied only from Wikidata P141 statements that cite a
named IUCN Red List version. This script does not infer or fill missing
assessments. Occurrence counts and coordinates come from the GBIF API.

Run from the repo root:

    python scripts/build_catalog.py
"""

from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "catalog.json"
UA = "harvester-risk-atlas/0.1 (EthnoHACK Track 3; catalog snapshot)"

# Status item ids are checked against live Wikidata labels before use.
STATUS_CODE = {
    "Q219127": "CR",
    "Q96377276": "EN",
    "Q278113": "VU",
    "Q719675": "NT",
    "Q211005": "LC",
}
STATUS_LABEL = {
    "CR": "Critically Endangered",
    "EN": "Endangered",
    "VU": "Vulnerable",
    "NT": "Near Threatened",
    "LC": "Least Concern",
}

SPECIES = [
    {"qid": "Q2249742", "scientific_name": "Aquilaria malaccensis", "demo": True},
    {"qid": "Q1379627", "scientific_name": "Aquilaria crassna"},
    {"qid": "Q24853263", "scientific_name": "Nardostachys jatamansi"},
    {"qid": "Q1661525", "scientific_name": "Saussurea costus"},
    {"qid": "Q1930232", "scientific_name": "Dalbergia cochinchinensis"},
    {"qid": "Q901803", "scientific_name": "Commiphora wightii"},
    {"qid": "Q186553", "scientific_name": "Taxus wallichiana"},
    {"qid": "Q12955947", "scientific_name": "Swietenia macrophylla"},
    {"qid": "Q2051175", "scientific_name": "Guaiacum officinale"},
    {"qid": "Q2392887", "scientific_name": "Pterocarpus santalinus"},
    {"qid": "Q2235214", "scientific_name": "Aniba rosaeodora"},
    {"qid": "Q959738", "scientific_name": "Prunus africana"},
    {"qid": "Q1051710", "scientific_name": "Hydrastis canadensis"},
    {"qid": "Q133964", "scientific_name": "Boswellia sacra"},
    {"qid": "Q2737217", "scientific_name": "Panax quinquefolius"},
    {"qid": "Q2367386", "scientific_name": "Boswellia papyrifera"},
]


def get_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    last_error: Exception | None = None
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=60) as response:
                return json.loads(response.read().decode())
        except Exception as exc:  # noqa: BLE001 - retry transient API errors
            last_error = exc
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"GET failed for {url}: {last_error}")


def slug(name: str) -> str:
    return name.casefold().replace(" ", "-")


def vernaculars(taxon_key: int) -> tuple[str | None, str | None, list[str]]:
    """English GBIF vernacular names. A single display name is used only on a tie-break that GBIF itself makes."""
    data = get_json(f"https://api.gbif.org/v1/species/{taxon_key}/vernacularNames")
    grouped: dict[str, dict] = {}
    preferred: set[str] = set()
    for row in data.get("results") or []:
        language = str(row.get("language") or "").casefold()
        if language not in {"en", "eng", "english"}:
            continue
        name = " ".join(str(row.get("vernacularName") or "").split())
        if not name:
            continue
        key = name.casefold()
        bucket = grouped.setdefault(key, {"name": name, "count": 0})
        bucket["count"] += 1
        if name[:1].isupper():
            bucket["name"] = name
        if row.get("preferred"):
            preferred.add(key)
    ranked = sorted(grouped.values(), key=lambda item: (-item["count"], item["name"].casefold()))
    display = [item["name"] for item in ranked]
    if len(preferred) == 1:
        key = next(iter(preferred))
        return grouped[key]["name"], "gbif-preferred", display
    if ranked and (len(ranked) == 1 or ranked[0]["count"] > ranked[1]["count"]):
        return ranked[0]["name"], "gbif-most-recorded", display
    return None, None, display


def facet_counts(payload: dict, field: str) -> list[dict]:
    for facet in payload.get("facets") or []:
        if str(facet.get("field", "")).lower() == field.lower():
            return facet.get("counts") or []
    return []


def qid_of(value: dict) -> str:
    return value["datavalue"]["value"]["id"]


def text_of(snak: dict) -> str:
    value = snak["datavalue"]["value"]
    if isinstance(value, dict):
        return str(value.get("time") or value.get("id") or value.get("text") or "")
    return str(value)


def load_wikidata(qids: list[str]) -> dict:
    url = (
        "https://www.wikidata.org/w/api.php?action=wbgetentities&format=json"
        f"&props=claims|labels|sitelinks&languages=en&sitefilter=enwiki&ids={'|'.join(qids)}"
    )
    return get_json(url)["entities"]


def load_labels(qids: list[str]) -> dict[str, str]:
    if not qids:
        return {}
    url = (
        "https://www.wikidata.org/w/api.php?action=wbgetentities&format=json"
        f"&props=labels&languages=en&ids={'|'.join(qids)}"
    )
    entities = get_json(url)["entities"]
    labels = {}
    for qid, entity in entities.items():
        labels[qid] = entity.get("labels", {}).get("en", {}).get("value", "")
    return labels


def listing_from_claims(claims: dict) -> dict | None:
    statements = claims.get("P141") or []
    if not statements:
        return None
    ranked = [item for item in statements if item.get("rank") == "preferred"] or statements
    if len(ranked) != 1:
        raise RuntimeError(f"Expected one IUCN statement, found {len(ranked)}")
    statement = ranked[0]
    status_qid = statement["mainsnak"]["datavalue"]["value"]["id"]
    if status_qid not in STATUS_CODE:
        raise RuntimeError(f"Unmapped IUCN status item {status_qid}")
    references = statement.get("references") or []
    if not references:
        raise RuntimeError("IUCN statement has no reference")
    snaks = references[0].get("snaks") or {}
    if "P248" not in snaks or "P627" not in snaks:
        raise RuntimeError("IUCN reference is missing stated-in or taxon id")
    source_qid = qid_of(snaks["P248"][0])
    taxon_id = text_of(snaks["P627"][0]).lstrip("+")
    retrieved = None
    if "P813" in snaks:
        raw = text_of(snaks["P813"][0])
        if raw.startswith("+"):
            raw = raw[1:]
        retrieved = raw[:10]
    return {
        "code": STATUS_CODE[status_qid],
        "label": STATUS_LABEL[STATUS_CODE[status_qid]],
        "status_qid": status_qid,
        "source_qid": source_qid,
        "iucn_taxon_id": taxon_id,
        "retrieved": retrieved,
    }


def gbif_match(name: str) -> dict:
    url = "https://api.gbif.org/v1/species/match?name=" + urllib.parse.quote(name)
    return get_json(url)


def gbif_species(key: int) -> dict:
    return get_json(f"https://api.gbif.org/v1/species/{key}")


def occurrence_summary(taxon_key: int) -> dict:
    dated = get_json(
        "https://api.gbif.org/v1/occurrence/search?"
        f"taxonKey={taxon_key}&limit=0&facet=year&facetLimit=300"
    )
    georef = get_json(
        "https://api.gbif.org/v1/occurrence/search?"
        f"taxonKey={taxon_key}&hasCoordinate=true&limit=0&facet=country&facetLimit=100"
    )
    sample = get_json(
        "https://api.gbif.org/v1/occurrence/search?"
        f"taxonKey={taxon_key}&hasCoordinate=true&limit=120"
    )
    year_rows = facet_counts(dated, "year")
    country_rows = facet_counts(georef, "country")
    years = [{"year": int(row["name"]), "count": int(row["count"])} for row in year_rows if str(row["name"]).isdigit()]
    countries = [{"code": row["name"], "count": int(row["count"])} for row in country_rows]
    points = []
    seen: set[tuple[float, float]] = set()
    gbif_iucn = None
    for record in sample.get("results") or []:
        if gbif_iucn is None and record.get("iucnRedListCategory"):
            gbif_iucn = record["iucnRedListCategory"]
        lat = record.get("decimalLatitude")
        lon = record.get("decimalLongitude")
        if lat is None or lon is None:
            continue
        rounded = (round(float(lat), 3), round(float(lon), 3))
        if rounded in seen:
            continue
        seen.add(rounded)
        points.append({"lat": rounded[0], "lon": rounded[1]})
    country_total = sum(item["count"] for item in countries)
    top = max(countries, key=lambda item: item["count"]) if countries else None
    return {
        "dated_record_count": int(dated.get("count") or 0),
        "year_facet_truncated": len(year_rows) >= 300,
        "years": years,
        "georeferenced_count": int(georef.get("count") or 0),
        "country_facet_count": country_total,
        "countries": countries,
        "top_country_code": None if top is None else top["code"],
        "top_country_count": None if top is None else top["count"],
        "top_country_share": None if not top or country_total == 0 else round(top["count"] / country_total, 4),
        "points": points,
        "gbif_occurrence_iucn_code": gbif_iucn,
    }


def country_names() -> dict[str, str]:
    payload = get_json("https://api.gbif.org/v1/enumeration/country")
    names = {}
    rows = payload if isinstance(payload, list) else payload.get("results") or payload.get("countries") or []
    for row in rows:
        code = row.get("iso2") or row.get("countryCode") or row.get("code")
        title = row.get("title") or row.get("name")
        if code and title:
            names[code] = title
    return names


def main() -> None:
    for qid, expected in {
        "Q219127": "critically endangered",
        "Q96377276": "endangered",
        "Q278113": "vulnerable",
        "Q719675": "near threatened",
        "Q211005": "least concern",
    }.items():
        label = load_labels([qid])[qid].casefold()
        if label != expected:
            raise RuntimeError(f"{qid} label is {label!r}, expected {expected!r}")

    qids = [item["qid"] for item in SPECIES]
    entities = load_wikidata(qids)
    countries = country_names()
    source_qids: set[str] = set()
    records = []

    for seed in SPECIES:
        entity = entities[seed["qid"]]
        listing = listing_from_claims(entity.get("claims") or {})
        if listing:
            source_qids.add(listing["source_qid"])
        match = gbif_match(seed["scientific_name"])
        usage_key = match.get("usageKey")
        if not usage_key:
            raise RuntimeError(f"No GBIF match for {seed['scientific_name']}")
        accepted_key = match.get("acceptedUsageKey") or usage_key
        accepted = gbif_species(int(accepted_key))
        time.sleep(0.15)
        summary = occurrence_summary(int(accepted_key))
        time.sleep(0.15)
        common_name, common_basis, vernacular_names = vernaculars(int(accepted_key))
        time.sleep(0.1)
        wiki_title = (entity.get("sitelinks") or {}).get("enwiki", {}).get("title")
        top_code = summary["top_country_code"]
        record = {
            "id": slug(seed["scientific_name"]),
            "scientific_name": seed["scientific_name"],
            "common_name": common_name,
            "common_name_basis": common_basis,
            "vernacular_names": vernacular_names,
            "wiki_title": wiki_title,
            "qid": seed["qid"],
            "wikidata_url": f"https://www.wikidata.org/wiki/{seed['qid']}",
            "demo": bool(seed.get("demo")),
            "gbif_usage_key": int(usage_key),
            "gbif_accepted_key": int(accepted_key),
            "gbif_status": match.get("status"),
            "gbif_match_type": match.get("matchType"),
            "accepted_scientific_name": accepted.get("scientificName"),
            "family": accepted.get("family"),
            "iucn": None
            if listing is None
            else {
                **listing,
                "url": f"https://www.iucnredlist.org/species/{listing['iucn_taxon_id']}",
            },
            "occurrences": {
                **summary,
                "top_country_name": countries.get(top_code) if top_code else None,
                "gbif_species_url": f"https://www.gbif.org/species/{accepted_key}",
            },
        }
        records.append(record)
        print(
            f"{record['scientific_name']:28} "
            f"{(listing or {}).get('code') or '—':3} "
            f"geo={summary['georeferenced_count']:<5} "
            f"top={summary['top_country_code']} {summary['top_country_share']} "
            f"common={record['common_name']} ({record['common_name_basis']})"
        )

    source_labels = load_labels(sorted(source_qids))
    for record in records:
        if record["iucn"]:
            record["iucn"]["source_title"] = source_labels.get(record["iucn"]["source_qid"], "")

    catalog = {
        "built_on": date.today().isoformat(),
        "scope": (
            "EthnoHACK 2026 Track 3 demo catalog of wild-harvested plants. "
            "IUCN categories are present only when a Wikidata P141 statement cites a named "
            "IUCN Red List version. A missing category is not an IUCN assessment."
        ),
        "species": records,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(catalog, indent=2), encoding="utf-8")
    print(f"wrote {OUT} ({OUT.stat().st_size} bytes, {len(records)} species)")


if __name__ == "__main__":
    main()
