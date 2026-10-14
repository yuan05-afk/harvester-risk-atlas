"""One openly licensed photo per species, for recognition in the web app.

Photos come from iNaturalist research-grade observations published to GBIF
(dataset 50c9509d-…), restricted to CC0 and CC BY 4.0 so they can be
redistributed with credit. Philippine observations are preferred.

Candidates are listed in data/curated/photos.csv. A person picks one per
species (column ``chosen``) after looking at the contact sheet; the build
then saves a resized copy to web/public/photos/<slug>.jpg with its credit.
Only the photo is used. The observation's location is never shown.
"""
from __future__ import annotations

import io
from pathlib import Path

import pandas as pd

from ..config import DATA_RAW, ROOT
from .http import get_json, session

API = "https://api.gbif.org/v1/occurrence/search"
INAT_RG = "50c9509d-22c7-4a22-a47d-8c48425ef4a7"
LICENSES = ("CC0_1_0", "CC_BY_4_0")
# Used only when no CC0 / CC BY photo exists. The atlas is non-commercial research
# and education, which CC BY-NC permits, with credit.
FALLBACK_LICENSES = ("CC_BY_NC_4_0",)
CANDIDATES_CSV = ROOT / "data" / "curated" / "photos.csv"
RAW_DIR = DATA_RAW / "photos"
WEB_DIR = ROOT / "web" / "public" / "photos"
MAX_WIDTH = 720


def _licence_name(url: str) -> str:
    url = (url or "").lower()
    if "publicdomain/zero" in url:
        return "CC0"
    if "/by/4.0" in url:
        return "CC BY 4.0"
    if "/by-nc/4.0" in url:
        return "CC BY-NC 4.0"
    return url


def candidates(taxon_key: int, n: int = 6, licenses: tuple[str, ...] = LICENSES) -> list[dict]:
    """Up to ``n`` photo candidates, Philippine observations first."""
    allowed = {"CC0", "CC BY 4.0"}
    if licenses == FALLBACK_LICENSES:
        allowed = {"CC BY-NC 4.0"}
    out: list[dict] = []
    seen: set[str] = set()
    for country in ("PH", None):
        params = {
            "taxonKey": taxon_key,
            "datasetKey": INAT_RG,
            "mediaType": "StillImage",
            "license": list(licenses),
            "limit": 20,
        }
        if country:
            params["country"] = country
        for rec in get_json(API, params).get("results", []):
            for m in rec.get("media", [])[:1]:
                url = m.get("identifier") or ""
                lic = _licence_name(m.get("license") or rec.get("license") or "")
                if not url or url in seen or lic not in allowed:
                    continue
                seen.add(url)
                out.append(
                    {
                        "image_url": url.replace("/original.", "/medium."),
                        "creator": m.get("creator") or m.get("rightsHolder") or "",
                        "licence": lic,
                        "page": m.get("references") or "",
                        "observation": f"https://www.gbif.org/occurrence/{rec.get('key')}",
                        "country": rec.get("countryCode") or "",
                    }
                )
            if len(out) >= n:
                return out
    return out


def download(url: str, dest: Path) -> Path:
    from PIL import Image

    dest.parent.mkdir(parents=True, exist_ok=True)
    r = session().get(url, timeout=60)
    r.raise_for_status()
    img = Image.open(io.BytesIO(r.content)).convert("RGB")
    if img.width > MAX_WIDTH:
        img = img.resize((MAX_WIDTH, round(img.height * MAX_WIDTH / img.width)), Image.LANCZOS)
    img.save(dest, "JPEG", quality=80, optimize=True, progressive=True)
    return dest


def build_candidates(taxa: pd.DataFrame, slugify) -> pd.DataFrame:
    """Fetch candidates for every species with a GBIF key; keep earlier choices."""
    old = pd.read_csv(CANDIDATES_CSV, keep_default_na=False) if CANDIDATES_CSV.exists() else pd.DataFrame()
    rows = []
    for t in taxa.itertuples(index=False):
        slug = slugify(t.scientific_name)
        if len(old) and slug in set(old["slug"]):
            rows.extend(old[old["slug"] == slug].to_dict("records"))
            continue
        if not t.gbif_taxon_key or t.gbif_taxon_key != t.gbif_taxon_key:
            continue
        found = candidates(int(t.gbif_taxon_key)) or candidates(int(t.gbif_taxon_key), licenses=FALLBACK_LICENSES)
        for i, c in enumerate(found):
            rows.append({"slug": slug, "scientific_name": t.scientific_name, "candidate": i, "chosen": i == 0, **c})
    df = pd.DataFrame(rows)
    df.to_csv(CANDIDATES_CSV, index=False, encoding="utf-8")
    return df


def raw_path(slug: str, candidate: int) -> Path:
    return RAW_DIR / f"{slug}_{candidate}.jpg"
