"""In-app Harvester Pressure Index.

HPI is not an IUCN index and not a harvest volume. It is the sum of two
0–50 components when both inputs exist:

- Listing: the IUCN category already stored on the catalog record.
- Record concentration: share of georeferenced GBIF records in the
  most-recorded country, scaled to 50. Requires at least 30 records.

Missing inputs stay unscored. They are never filled with zero, because a
zero would read as low pressure.
"""

from __future__ import annotations

MIN_GEOREFERENCED = 30

LISTING_POINTS = {
    "CR": 50,
    "EN": 40,
    "VU": 30,
    "NT": 18,
    "LC": 8,
}

BANDS = (
    (75, "Severe"),
    (50, "Higher"),
    (25, "Moderate"),
    (0, "Lower"),
)


def band_for(hpi: int | None) -> str | None:
    if hpi is None:
        return None
    for threshold, name in BANDS:
        if hpi >= threshold:
            return name
    return "Lower"


def score_record(species: dict) -> dict:
    iucn = species.get("iucn") or {}
    category = iucn.get("code")
    occurrences = species.get("occurrences") or {}
    geo_count = occurrences.get("georeferenced_count")
    share = occurrences.get("top_country_share")

    listing = LISTING_POINTS.get(category) if category else None
    concentration = None
    gaps: list[str] = []

    if listing is None:
        gaps.append("IUCN category is not in this catalog snapshot, so listing is unscored.")
    if geo_count is None or geo_count < MIN_GEOREFERENCED or share is None:
        shown = 0 if geo_count is None else geo_count
        gaps.append(
            f"Record concentration needs at least {MIN_GEOREFERENCED} georeferenced GBIF records. This species has {shown}."
        )
    else:
        concentration = int(round(float(share) * 50))

    hpi = listing + concentration if listing is not None and concentration is not None else None
    return {
        "listing": listing,
        "concentration": concentration,
        "hpi": hpi,
        "band": band_for(hpi),
        "gaps": gaps,
        "complete": hpi is not None,
    }
