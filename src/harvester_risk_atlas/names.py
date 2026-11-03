"""Vernacular → scientific name helper (thin; not a second product)."""
from __future__ import annotations

import os
import re
from functools import lru_cache

import pandas as pd


def _norm(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"[^a-z0-9ñ\s\-×x\.]", "", s)
    s = re.sub(r"\s+", " ", s)
    return s


@lru_cache(maxsize=1)
def _seed_table() -> pd.DataFrame:
    from .config import SEED_SPECIES

    return pd.read_csv(SEED_SPECIES)


def resolve_query(query: str, species_df: pd.DataFrame | None = None) -> list[dict]:
    """Return ranked matches from scientific + vernacular columns.

    Optional LLM path behind ENABLE_LLM_NAMES=1 — stubbed; falls back to fuzzy table.
    """
    q = _norm(query)
    if not q:
        return []

    df = species_df if species_df is not None else _seed_table()
    hits: list[dict] = []
    for _, row in df.iterrows():
        sci = str(row.get("scientific_name", ""))
        vern = str(row.get("vernacular_ph", ""))
        sci_n, vern_n = _norm(sci), _norm(vern)
        score = 0.0
        if q == sci_n or q == vern_n:
            score = 1.0
        elif q in sci_n or q in vern_n:
            score = 0.85
        elif sci_n.startswith(q) or vern_n.startswith(q):
            score = 0.8
        else:
            # token overlap
            qt = set(q.split())
            tt = set(sci_n.split()) | set(vern_n.split())
            if qt & tt:
                score = 0.55 * len(qt & tt) / max(len(qt), 1)
        if score >= 0.5:
            hits.append(
                {
                    "scientific_name": sci,
                    "vernacular_ph": vern,
                    "score": round(score, 3),
                    "method": "table",
                }
            )
    hits.sort(key=lambda x: -x["score"])

    if not hits and os.getenv("ENABLE_LLM_NAMES", "0") == "1":
        hits.extend(_llm_stub(query))
    return hits[:10]


def _llm_stub(query: str) -> list[dict]:
    """Optional OpenAI/LangChain stub — disabled unless flagged + keyed."""
    if not os.getenv("OPENAI_API_KEY"):
        return [
            {
                "scientific_name": "",
                "vernacular_ph": query,
                "score": 0.0,
                "method": "llm_stub_no_key",
                "note": "ENABLE_LLM_NAMES=1 but OPENAI_API_KEY unset",
            }
        ]
    # Intentionally not calling the network in default builds.
    return [
        {
            "scientific_name": "",
            "vernacular_ph": query,
            "score": 0.0,
            "method": "llm_stub",
            "note": "Wire langchain/openai here for production name resolution",
        }
    ]
