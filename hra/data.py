"""Load the committed catalog snapshot and attach scores."""

from __future__ import annotations

import json
from pathlib import Path

from hra.scoring import score_record

ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "data" / "catalog.json"
_CACHE: dict = {"mtime": None, "data": None}


class CatalogError(FileNotFoundError):
    pass


def load_catalog() -> dict:
    if not CATALOG_PATH.exists():
        raise CatalogError(
            "Catalog snapshot is missing. From the repo root run: python scripts/build_catalog.py"
        )
    mtime = CATALOG_PATH.stat().st_mtime
    if _CACHE["mtime"] != mtime or _CACHE["data"] is None:
        _CACHE["data"] = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
        _CACHE["mtime"] = mtime
    return _CACHE["data"]


def species_list() -> list[dict]:
    rows = []
    for species in load_catalog()["species"]:
        scored = dict(species)
        scored["score"] = score_record(species)
        rows.append(scored)
    return rows


def by_id(species_id: str | None) -> dict | None:
    if not species_id:
        return None
    for species in species_list():
        if species["id"] == species_id:
            return species
    return None


def demo_species() -> dict:
    for species in species_list():
        if species.get("demo"):
            return species
    raise CatalogError("Demo species is not marked in the catalog.")


def display_name(species: dict) -> str:
    name = species.get("common_name") or species["scientific_name"]
    if species.get("common_name") and name.islower():
        return name[:1].upper() + name[1:]
    return name


def label_name(species: dict) -> str | None:
    """A short label for lists. This is not a claim that the name is preferred."""
    if species.get("common_name"):
        return display_name(species)
    names = species.get("vernacular_names") or []
    return names[0] if names else None


def category_label(species: dict) -> str:
    iucn = species.get("iucn")
    if not iucn:
        return "Not recorded"
    return iucn["code"]
