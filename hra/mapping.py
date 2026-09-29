"""Esri gray atlas. Cluster counts stay neutral; marker color is HPI only."""

from __future__ import annotations

import html

import folium
from folium.plugins import MarkerCluster

from hra.theme import MONO, risk_color

ESRI_GRAY = (
    "https://server.arcgisonline.com/ArcGIS/rest/services/"
    "Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}"
)
ESRI_LABELS = (
    "https://server.arcgisonline.com/ArcGIS/rest/services/"
    "Canvas/World_Light_Gray_Reference/MapServer/tile/{z}/{y}/{x}"
)
ESRI_ATTR = "Tiles &copy; Esri &mdash; Esri, DeLorme, NAVTEQ"

CLUSTER_JS = """
function(cluster) {
  var count = cluster.getChildCount();
  return L.divIcon({
    html: '<div class="hra-cluster">' + count + '</div>',
    className: 'hra-cluster-wrap',
    iconSize: L.point(34, 34)
  });
}
"""


def build_map(species_rows: list[dict]) -> folium.Map:
    atlas = folium.Map(
        location=[18, 20],
        zoom_start=2,
        tiles=None,
        control_scale=True,
        zoom_control=True,
        attributionControl=True,
    )
    folium.TileLayer(tiles=ESRI_GRAY, attr=ESRI_ATTR, name="Esri Gray", max_zoom=16).add_to(atlas)
    folium.TileLayer(
        tiles=ESRI_LABELS,
        attr=ESRI_ATTR,
        name="Place labels",
        overlay=True,
        control=False,
        max_zoom=16,
    ).add_to(atlas)
    atlas.get_root().header.add_child(
        folium.Element(
            f"""
            <style>
              .hra-cluster-wrap {{ background: transparent; border: none; }}
              .hra-cluster {{
                width: 30px; height: 30px; border-radius: 999px;
                background: #24312b; color: #fff;
                font-family: {MONO};
                font-size: 11px; line-height: 30px; text-align: center;
                border: 2px solid #fff;
              }}
              .leaflet-container {{ background: #e8e8ea; font-family: -apple-system, BlinkMacSystemFont, "Inter", "Segoe UI", sans-serif; }}
            </style>
            """
        )
    )
    cluster = MarkerCluster(icon_create_function=CLUSTER_JS)
    bounds: list[list[float]] = []
    for species in species_rows:
        points = (species.get("occurrences") or {}).get("points") or []
        if not points:
            continue
        color = risk_color(species["score"].get("band"))
        name = html.escape(species.get("common_name") or species["scientific_name"])
        scientific = html.escape(species["scientific_name"])
        iucn = (species.get("iucn") or {}).get("code") or "Not recorded"
        hpi = species["score"].get("hpi")
        hpi_text = "Not scored" if hpi is None else f"{hpi} {species['score'].get('band')}"
        popup = (
            f"<div style='font-size:13px;line-height:1.4;min-width:160px'>"
            f"<strong>{name}</strong><br>"
            f"<span style='color:#6e6e73'>{scientific}</span><br>"
            f"IUCN {html.escape(iucn)} · HPI {html.escape(hpi_text)}</div>"
        )
        for point in points:
            folium.CircleMarker(
                location=[point["lat"], point["lon"]],
                radius=6,
                color="#ffffff",
                weight=1,
                fill=True,
                fill_color=color,
                fill_opacity=0.92,
                tooltip=species["scientific_name"],
                popup=folium.Popup(popup, max_width=240),
            ).add_to(cluster)
            bounds.append([point["lat"], point["lon"]])
    cluster.add_to(atlas)
    if len(bounds) == 1:
        atlas.location = bounds[0]
        atlas.zoom_start = 5
    elif len(bounds) > 1:
        atlas.fit_bounds(bounds, padding=(24, 24))
    return atlas
