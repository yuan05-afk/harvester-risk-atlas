"""IUCN Red List API v4 client — never invent statuses.

Token: set IUCN_API_TOKEN in environment or .env
  Sign up (free, research/education): https://api.iucnredlist.org/users/sign_up
  Manage token: https://api.iucnredlist.org/users/edit
  Docs: https://api.iucnredlist.org/api-docs/index.html
  Terms: https://www.iucnredlist.org/terms/terms-of-use

Without a token every lookup returns status='not_queried' and category=None.
Categories are NEVER inferred from Wikipedia, GBIF, or seed notes.
IUCN category is a *separate dossier field* — not an HPI input.
"""
from __future__ import annotations

import os
import re
import time
from pathlib import Path
from typing import Any

import pandas as pd
import requests

try:
    from dotenv import load_dotenv

    # Load project .env if present (no-op when missing)
    _root = Path(__file__).resolve().parents[2]
    load_dotenv(_root / ".env")
except ImportError:
    pass

API_BASE = "https://api.iucnredlist.org/api/v4"
SIGNUP_URL = "https://api.iucnredlist.org/users/sign_up"


def get_token() -> str:
    return os.getenv("IUCN_API_TOKEN", "").strip()


def _split_binomial(scientific_name: str) -> tuple[str, str] | None:
    """Parse genus + species epithet; skip hybrids / × names for API lookup."""
    name = scientific_name.strip()
    if "×" in name or " x " in name.lower():
        return None
    # Drop authorship if present
    name = re.split(r"\s+[A-Z(]", name, maxsplit=1)[0].strip()
    parts = name.split()
    if len(parts) < 2:
        return None
    return parts[0], parts[1]


def _not_queried(scientific_name: str, note: str | None = None) -> dict[str, Any]:
    return {
        "scientific_name": scientific_name,
        "iucn_category": None,
        "iucn_category_code": None,
        "iucn_assessment_id": None,
        "iucn_year": None,
        "iucn_status": "not_queried",
        "iucn_note": note
        or (
            f"Set IUCN_API_TOKEN to query API v4. Free signup: {SIGNUP_URL}. "
            "Do not invent categories."
        ),
    }


def lookup_iucn(scientific_name: str, token: str | None = None) -> dict[str, Any]:
    """Look up latest global Red List category for a scientific name.

    Returns a dict with iucn_category / iucn_status. Never fabricates a category.
    """
    tok = (token if token is not None else get_token()).strip()
    if not tok:
        return _not_queried(scientific_name)

    parsed = _split_binomial(scientific_name)
    if parsed is None:
        return {
            "scientific_name": scientific_name,
            "iucn_category": None,
            "iucn_category_code": None,
            "iucn_assessment_id": None,
            "iucn_year": None,
            "iucn_status": "skipped",
            "iucn_note": "Name not a simple binomial (hybrid/infraspecific) — not queried",
        }

    genus, species = parsed
    headers = {"Authorization": tok, "Accept": "application/json"}
    try:
        r = requests.get(
            f"{API_BASE}/taxa/scientific_name",
            params={"genus_name": genus, "species_name": species},
            headers=headers,
            timeout=45,
        )
        if r.status_code in (401, 403):
            return {
                "scientific_name": scientific_name,
                "iucn_category": None,
                "iucn_category_code": None,
                "iucn_assessment_id": None,
                "iucn_year": None,
                "iucn_status": "auth_error",
                "iucn_note": f"HTTP {r.status_code} — check IUCN_API_TOKEN (v4 signup required)",
            }
        if r.status_code == 404:
            return {
                "scientific_name": scientific_name,
                "iucn_category": None,
                "iucn_category_code": None,
                "iucn_assessment_id": None,
                "iucn_year": None,
                "iucn_status": "not_on_red_list",
                "iucn_note": "Taxon not found in Red List API (not the same as LC — do not invent)",
            }
        if r.status_code != 200:
            return {
                "scientific_name": scientific_name,
                "iucn_category": None,
                "iucn_category_code": None,
                "iucn_assessment_id": None,
                "iucn_year": None,
                "iucn_status": "api_error",
                "iucn_note": f"HTTP {r.status_code}",
            }

        data = r.json()
        assessments = data.get("assessments") or []
        if not assessments:
            return {
                "scientific_name": scientific_name,
                "iucn_category": None,
                "iucn_category_code": None,
                "iucn_assessment_id": None,
                "iucn_year": None,
                "iucn_status": "no_assessment",
                "iucn_note": "Taxon known to API but no assessments returned",
            }

        # Prefer latest global scope (code "1"); else latest by year
        def _is_global(a: dict) -> bool:
            scopes = a.get("scopes") or []
            return any(str(s.get("code")) == "1" for s in scopes)

        globals_ = [a for a in assessments if _is_global(a)]
        pool = globals_ or assessments
        pool_sorted = sorted(
            pool,
            key=lambda a: str(a.get("year_published") or ""),
            reverse=True,
        )
        latest = pool_sorted[0]
        code = latest.get("red_list_category_code") or latest.get("red_list_category", {})
        if isinstance(code, dict):
            code = code.get("code")
        # Optional descriptive label from full assessment if only code present
        category_label = None
        assessment_id = latest.get("assessment_id") or latest.get("assessmentId")
        year = latest.get("year_published")

        # If summary lacks human label, try assessment endpoint once
        if code and assessment_id:
            try:
                ar = requests.get(
                    f"{API_BASE}/assessment/{assessment_id}",
                    headers=headers,
                    timeout=45,
                )
                if ar.status_code == 200:
                    ad = ar.json()
                    rlc = ad.get("red_list_category") or {}
                    code = rlc.get("code") or code
                    desc = rlc.get("description") or {}
                    if isinstance(desc, dict):
                        category_label = desc.get("en")
                    year = ad.get("year_published") or year
            except requests.RequestException:
                pass

        return {
            "scientific_name": scientific_name,
            "iucn_category": category_label or code,  # prefer English label, else code
            "iucn_category_code": code,
            "iucn_assessment_id": assessment_id,
            "iucn_year": year,
            "iucn_status": "ok",
            "iucn_note": "Live IUCN Red List API v4 — cite assessment; not an HPI input",
        }
    except requests.RequestException as e:
        return {
            "scientific_name": scientific_name,
            "iucn_category": None,
            "iucn_category_code": None,
            "iucn_assessment_id": None,
            "iucn_year": None,
            "iucn_status": "exception",
            "iucn_note": str(e),
        }


def lookup_many(
    names: list[str],
    token: str | None = None,
    pause_s: float = 0.55,
) -> pd.DataFrame:
    """Batch lookup with polite delay. Without token, all rows are not_queried."""
    rows = []
    tok = token if token is not None else get_token()
    for i, name in enumerate(names):
        rows.append(lookup_iucn(name, token=tok))
        if tok and i < len(names) - 1:
            time.sleep(pause_s)
    return pd.DataFrame(rows)


# Back-compat alias used by older docs
def lookup_iucn_status(scientific_name: str) -> dict[str, Any]:
    r = lookup_iucn(scientific_name)
    return {
        "scientific_name": r["scientific_name"],
        "category": r.get("iucn_category_code") or r.get("iucn_category"),
        "status": r.get("iucn_status"),
        "note": r.get("iucn_note"),
    }
