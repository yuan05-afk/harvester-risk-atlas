"""DENR Administrative Order 2026-20: Updated National List of Threatened Philippine Plants.

The PDF is read once into text (data/raw/denr/DAO-2026-20.md) and parsed
here into one row per listed taxon. In the Order, an asterisk before a name
marks a Philippine endemic.

Categories: CR critically endangered, EN endangered, VU vulnerable,
OTS other threatened species.
"""
from __future__ import annotations

import re

import pandas as pd

from ..config import DATA_PROCESSED, DATA_RAW

SOURCE_URL = "https://apidb.denr.gov.ph/infores/uploads/DAO-2026-20.pdf"
RAW_TEXT = DATA_RAW / "denr" / "DAO-2026-20.md"
PROCESSED = DATA_PROCESSED / "v2" / "dao_2026_20.csv"
CITATION = (
    "DENR (2026). Updated National List of Threatened Philippine Plants and Their Categories. "
    "DENR Administrative Order No. 2026-20. " + SOURCE_URL
)
_HEADINGS = {
    "CRITICALLY ENDANGERED": "CR",
    "ENDANGERED": "EN",
    "VULNERABLE": "VU",
    "OTHER THREATENED SPECIES": "OTS",
}
_ROW = re.compile(r"^\|\s*(?P<family>[^|]*)\|\s*(?P<no>\d+)\.\s*\|\s*(?P<name>[^|]+)\|\s*(?P<common>[^|]*)\|")


def binomial(name: str) -> str:
    """Genus + epithet, plus an infraspecific rank and name when present."""
    tokens = name.replace("*", "").replace("&amp;", "&").split()
    if len(tokens) < 2:
        return " ".join(tokens)
    out = tokens[:2]
    for i, tok in enumerate(tokens[2:], start=2):
        if tok in ("ssp.", "subsp.", "var.") and i + 1 < len(tokens):
            out += [tok, tokens[i + 1]]
            break
    return " ".join(out)


def parse(text: str) -> pd.DataFrame:
    rows, category, family = [], None, ""
    for line in text.splitlines():
        heading = re.match(r"^##\s+Category\s+[A-D]\.\s+(.+?)\s*\(", line)
        if heading:
            category = _HEADINGS.get(heading.group(1).strip().upper())
            continue
        if line.startswith("## SECTION 7"):
            break
        m = _ROW.match(line)
        if not m or category is None:
            continue
        fam = m.group("family").strip()
        family = fam or family
        raw = m.group("name").strip()
        rows.append(
            {
                "dao_category": category,
                "family": family,
                "taxon": binomial(raw),
                "name_as_listed": raw.lstrip("*").replace("&amp;", "&").strip(),
                "ph_endemic_dao": raw.startswith("*"),
                "common_name": m.group("common").strip(),
            }
        )
    return pd.DataFrame(rows)


def threatened_list() -> pd.DataFrame:
    if PROCESSED.exists():
        return pd.read_csv(PROCESSED, encoding="utf-8", keep_default_na=False)
    df = parse(RAW_TEXT.read_text(encoding="utf-8"))
    PROCESSED.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(PROCESSED, index=False, encoding="utf-8")
    return df


def lookup(names: list[str], table: pd.DataFrame | None = None) -> dict[str, str]:
    """Category for each species binomial, or "" when not listed."""
    table = threatened_list() if table is None else table
    species = table.assign(sp=table["taxon"].str.split().str[:2].str.join(" "))
    best: dict[str, str] = {}
    order = {"CR": 0, "EN": 1, "VU": 2, "OTS": 3}
    for sp, cat in zip(species["sp"], species["dao_category"]):
        if sp not in best or order[cat] < order[best[sp]]:
            best[sp] = cat
    return {n: best.get(" ".join(n.split()[:2]), "") for n in names}
