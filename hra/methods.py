"""HPI weights, taken from the scoring table. Nothing here is an IUCN index."""

from __future__ import annotations

import html

from hra.scoring import BANDS, LISTING_POINTS, MIN_GEOREFERENCED


def band_ranges() -> list[tuple[str, str]]:
    ranges: list[tuple[str, str]] = []
    upper: int | None = None
    for threshold, name in BANDS:
        if upper is None:
            label = f"{threshold} and above"
        else:
            label = f"{threshold}–{upper - 1}"
        ranges.append((name, label))
        upper = threshold
    return ranges


def weights_html() -> str:
    listing = "".join(
        f"<tr><td>{html.escape(code)}</td><td class='num'>{points}</td></tr>"
        for code, points in LISTING_POINTS.items()
    )
    bands = "".join(
        f"<tr><td>{html.escape(name)}</td><td class='num'>{html.escape(span)}</td></tr>"
        for name, span in band_ranges()
    )
    return (
        "<p class='body'>HPI adds listing and record concentration, each up to 50, and only when both exist.</p>"
        "<p class='caption'>Listing, from the cited IUCN category</p>"
        "<table class='hra'><thead><tr><th>Category</th><th>Points</th></tr></thead>"
        f"<tbody>{listing}</tbody></table>"
        f"<p class='caption'>Record concentration is the top-country share of georeferenced GBIF records, "
        f"times 50 and rounded. It is scored only with at least {MIN_GEOREFERENCED} of those records.</p>"
        "<p class='caption'>Band</p>"
        "<table class='hra'><thead><tr><th>Band</th><th>HPI</th></tr></thead>"
        f"<tbody>{bands}</tbody></table>"
        "<p class='caption'>HPI is not an IUCN index, a trend, or a harvest volume. "
        "A missing input stays unscored. It is not stored as zero.</p>"
    )
