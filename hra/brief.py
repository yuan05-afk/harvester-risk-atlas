"""Plain-language brief built only from scored catalog fields."""

from __future__ import annotations

from hra.data import category_label, display_name


def _listing_sentence(species: dict) -> str:
    iucn = species.get("iucn")
    if not iucn:
        return (
            f"No IUCN category is stored for {species['scientific_name']} in this snapshot. "
            "That is not a statement that IUCN has left it unassessed."
        )
    return (
        f"{species['scientific_name']} is recorded as {iucn['label']} ({iucn['code']}) "
        f"from {iucn.get('source_title') or 'a cited IUCN Red List version'} "
        f"(taxon {iucn['iucn_taxon_id']})."
    )


def _concentration_sentence(species: dict) -> str:
    occurrences = species.get("occurrences") or {}
    share = occurrences.get("top_country_share")
    country = occurrences.get("top_country_name") or occurrences.get("top_country_code")
    count = occurrences.get("georeferenced_count") or 0
    if species["score"]["concentration"] is None or share is None or not country:
        return (
            f"GBIF returned {count} georeferenced records. "
            "Record concentration is left unscored below 30 records."
        )
    percent = round(float(share) * 100)
    return (
        f"{percent}% of georeferenced GBIF records in this snapshot fall in {country} "
        f"({count} georeferenced records). That share is a record pattern, not a harvest volume "
        "or a population estimate."
    )


def species_paragraph(species: dict) -> str:
    score = species["score"]
    name = display_name(species)
    lines = [f"{name} ({species['scientific_name']}).", _listing_sentence(species), _concentration_sentence(species)]
    if score["complete"]:
        lines.append(
            f"HPI is {score['hpi']} ({score['band']}), from listing {score['listing']} and "
            f"record concentration {score['concentration']} on a 0–50 scale each."
        )
    else:
        lines.append("HPI is not scored, because one of those inputs is missing.")
    return " ".join(lines)


def brief_markdown(left: dict, right: dict) -> str:
    title = f"# Brief: {display_name(left)} and {display_name(right)}"
    body = [
        title,
        "",
        "Harvester Risk Atlas · EthnoHACK 2026 Track 3",
        "",
        species_paragraph(left),
        "",
        species_paragraph(right),
        "",
        (
            f"Catalog categories: {category_label(left)} and {category_label(right)}. "
            "HPI is an in-app sum. It is not an IUCN category, a trend, or a quota."
        ),
        "",
    ]
    return "\n".join(body)
