"""Optional one-page field brief (HTML → print/PDF via browser). No medical claims."""
from __future__ import annotations

from typing import Any


def render_field_brief_html(row: dict[str, Any], actions: list[str]) -> str:
    hpi = row.get("hpi")
    hpi_s = f"{float(hpi):.3f}" if hpi is not None and hpi == hpi else "—"
    conf = row.get("hpi_confidence")
    conf_s = f"{float(conf):.2f}" if conf is not None and conf == conf else "—"
    actions_li = "".join(f"<li>{a}</li>" for a in actions)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<title>Field brief — {row.get('scientific_name','')}</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, Inter, Helvetica, Arial, sans-serif;
         color: #1d1d1f; max-width: 720px; margin: 2rem auto; padding: 0 1rem; }}
  h1 {{ font-size: 1.35rem; font-weight: 600; letter-spacing: -0.02em; margin-bottom: 0.15rem; }}
  .sub {{ color: #6e6e73; font-size: 0.9rem; margin-bottom: 1.25rem; }}
  .metric {{ font-family: "JetBrains Mono", "IBM Plex Mono", ui-monospace, monospace;
             font-variant-numeric: tabular-nums; }}
  .box {{ border: 1px solid #d2d2d7; border-radius: 8px; padding: 0.85rem 1rem; margin: 0.75rem 0; }}
  .label {{ font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.04em; color: #86868b; }}
  .disc {{ font-size: 0.75rem; color: #6e6e73; border-top: 1px solid #d2d2d7; padding-top: 0.75rem; margin-top: 1.5rem; }}
</style>
</head>
<body>
  <div class="label">Harvester Risk Atlas — field brief</div>
  <h1>{row.get('scientific_name','')}</h1>
  <div class="sub">{row.get('vernacular_ph','')} · {row.get('family','')}</div>
  <div class="box"><div class="label">Stress (HPI v1)</div>
    <div class="metric" style="font-size:1.4rem">{hpi_s}</div>
    <div style="font-size:0.8rem;color:#6e6e73">Confidence {conf_s} · Band: {row.get('hpi_band','—')}</div>
  </div>
  <div class="box"><div class="label">Where</div>
    <div>Centroid ≈ {row.get('lat_mean','—'):.3f}°N, {row.get('lon_mean','—'):.3f}°E
    · n={row.get('n_occurrences',0)} GBIF sample pts</div>
  </div>
  <div class="box"><div class="label">Why it matters</div>
    <div>{row.get('notes','')}</div>
    <div style="margin-top:0.5rem;font-size:0.9rem">IUCN: {row.get('iucn_category') or row.get('iucn_category_code') or row.get('iucn_status') or 'not_queried'}</div>
    <div style="margin-top:0.3rem;font-size:0.8rem;color:#6e6e73">{row.get('iucn_note') or row.get('demo_iucn_note') or ''}</div>
    <div style="margin-top:0.4rem;font-size:0.75rem;color:#86868b">Climate: {row.get('climate_source') or 'n/a'} · PA: {row.get('pa_source') or 'n/a'}</div>
  </div>
  <div class="box"><div class="label">What to do</div>
    <ul>{actions_li}</ul>
  </div>
  <p class="disc">Not medical advice. Not a harvest permit. HPI is a transparent research index;
  IUCN categories are never invented. EthnoHACK 2026 Track 3.</p>
</body>
</html>
"""
