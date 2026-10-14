"""Polite JSON GET with retries and a JSON-on-disk cache."""
from __future__ import annotations

import gzip
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

USER_AGENT = "harvester-risk-atlas/2.0 (research; EthnoHack 2026 Track 3)"
_SESSION: requests.Session | None = None


def session() -> requests.Session:
    global _SESSION
    if _SESSION is None:
        _SESSION = requests.Session()
        _SESSION.headers["User-Agent"] = USER_AGENT
    return _SESSION


def get_json(url: str, params: dict[str, Any] | None = None, *, retries: int = 4, timeout: int = 60) -> Any:
    """GET a JSON document. Retries on 429/5xx and connection errors with backoff."""
    delay = 1.0
    for attempt in range(retries + 1):
        try:
            r = session().get(url, params=params, timeout=timeout)
        except requests.RequestException:
            if attempt == retries:
                raise
        else:
            if r.status_code < 400:
                return r.json()
            if r.status_code not in (429, 500, 502, 503, 504) or attempt == retries:
                r.raise_for_status()
        time.sleep(delay)
        delay *= 2
    raise RuntimeError("unreachable")


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def write_cache(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, "wt", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False)


def read_cache(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        return json.load(fh)
