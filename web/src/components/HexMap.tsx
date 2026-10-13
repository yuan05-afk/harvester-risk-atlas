import * as maplibregl from "maplibre-gl";
import type { ExpressionSpecification, Map as MLMap, MapGeoJSONFeature, MapMouseEvent } from "maplibre-gl";
// MapLibre 6 runs an ES-module worker that imports a shared chunk by relative path.
// Let Vite bundle the worker with its imports and hand MapLibre the result.
import workerUrl from "maplibre-gl/dist/maplibre-gl-worker.mjs?worker&url";
import "maplibre-gl/dist/maplibre-gl.css";
import { useEffect, useRef, useState } from "react";
import { geoUrl } from "../data/api";
import type { CellProps } from "../data/schema";

maplibregl.setWorkerUrl(workerUrl);

export type MapMode = "hotspots" | "species" | "effort";

const PH_BOUNDS: [[number, number], [number, number]] = [
  [116.4, 4.4],
  [127.0, 21.2],
];
/** Below this zoom, aggregate cells (H3 res 4, ~1,770 km²) replace fine cells (res 5, ~250 km²). */
const FINE_ZOOM = 6.5;
const SOURCES = { fine: "cells", coarse: "cells4" } as const;

function css(name: string): string {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim() || "#999";
}

/** MapLibre paints need literal colours; resolve "var(--token)" against the document. */
function resolveColor(c: string): string {
  const m = /^var\((--[\w-]+)\)$/.exec(c.trim());
  return m ? css(m[1]) : c;
}

function fillFor(mode: MapMode, memberColor: string): ExpressionSpecification {
  if (mode === "effort") {
    return ["step", ["get", "effort"], "#edefed", 10, "#d1d6d1", 50, "#adb3ae", 100, "#818882", 500, "#59605a"];
  }
  if (mode === "species") {
    return ["case", ["boolean", ["feature-state", "member"], false], resolveColor(memberColor), "rgba(0,0,0,0)"];
  }
  return [
    "step",
    ["+", ["get", "n_high"], ["get", "n_watch"]],
    "rgba(0,0,0,0)",
    1,
    css("--hot-1"),
    2,
    css("--hot-2"),
    3,
    css("--hot-3"),
    4,
    css("--hot-4"),
  ];
}

function toProps(f?: MapGeoJSONFeature): CellProps | null {
  if (!f) return null;
  const p = f.properties as Record<string, unknown>;
  return {
    h3: String(p.h3),
    effort: Number(p.effort),
    pa: p.pa === null || p.pa === undefined || p.pa === "null" ? null : Number(p.pa),
    n_high: Number(p.n_high),
    n_watch: Number(p.n_watch),
    n_lower: Number(p.n_lower),
    n_cohort: Number(p.n_cohort),
    species: typeof p.species === "string" ? JSON.parse(p.species) : (p.species as string[]),
  };
}

/**
 * The atlas map. Locations are only ever H3 cells, never points: res 4 at the
 * country view, res 5 once zoomed in (and always for a single plant).
 * Every interaction also exists as a list next to the map.
 */
export function HexMap({
  mode,
  memberCells,
  memberColor = "var(--tier-high)",
  showPA = true,
  selectedCell,
  onCellClick,
  onCellHover,
  interactive = true,
  bounds,
  label,
}: {
  mode: MapMode;
  memberCells?: string[];
  memberColor?: string;
  showPA?: boolean;
  selectedCell?: string | null;
  onCellClick?: (cell: CellProps | null) => void;
  onCellHover?: (cell: CellProps | null) => void;
  interactive?: boolean;
  /** [west, south, east, north] to frame, e.g. one plant's cells */
  bounds?: [number, number, number, number] | null;
  label: string;
}) {
  const el = useRef<HTMLDivElement>(null);
  const map = useRef<MLMap | null>(null);
  const [ready, setReady] = useState(false);
  const [drawn, setDrawn] = useState(false);
  const prevMembers = useRef<string[]>([]);
  const prevSelected = useRef<string | null>(null);
  const handlers = useRef({ onCellClick, onCellHover });
  handlers.current = { onCellClick, onCellHover };

  useEffect(() => {
    if (!el.current) return;
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const cellLayers = (source: string, id: string) =>
      [
        { id: `${id}-fill`, type: "fill", source, paint: { "fill-color": "rgba(0,0,0,0)", "fill-opacity": 0.92 } },
        {
          id: `${id}-edge`,
          type: "line",
          source,
          paint: { "line-color": css("--sheet"), "line-width": ["interpolate", ["linear"], ["zoom"], 4, 0.3, 9, 1.2], "line-opacity": 0.8 },
        },
        {
          id: `${id}-hover`,
          type: "line",
          source,
          paint: { "line-color": css("--ink"), "line-width": ["case", ["boolean", ["feature-state", "hover"], false], 1.5, 0] },
        },
        {
          id: `${id}-selected`,
          type: "line",
          source,
          paint: { "line-color": css("--ink"), "line-width": ["case", ["boolean", ["feature-state", "selected"], false], 3, 0] },
        },
      ] as maplibregl.LayerSpecification[];

    const m = new maplibregl.Map({
      container: el.current,
      style: {
        version: 8,
        sources: {
          land: { type: "geojson", data: geoUrl("land.geojson") },
          [SOURCES.fine]: { type: "geojson", data: geoUrl("cells.geojson"), promoteId: "h3" },
          [SOURCES.coarse]: { type: "geojson", data: geoUrl("cells_r4.geojson"), promoteId: "h3" },
          pa: { type: "geojson", data: geoUrl("pa.geojson") },
        },
        layers: [
          { id: "sea", type: "background", paint: { "background-color": css("--sea") } },
          { id: "land", type: "fill", source: "land", paint: { "fill-color": css("--land") } },
          { id: "land-edge", type: "line", source: "land", paint: { "line-color": css("--rule-strong"), "line-width": 0.6 } },
          ...cellLayers(SOURCES.coarse, "coarse"),
          ...cellLayers(SOURCES.fine, "fine"),
          {
            id: "pa",
            type: "line",
            source: "pa",
            layout: { visibility: showPA ? "visible" : "none" },
            paint: { "line-color": css("--c-habitat"), "line-width": 1, "line-dasharray": [2, 1.5], "line-opacity": 0.85 },
          },
        ],
      },
      bounds: PH_BOUNDS,
      fitBoundsOptions: { padding: 16 },
      interactive,
      attributionControl: false,
      dragRotate: false,
      pitchWithRotate: false,
      fadeDuration: reduce ? 0 : 200,
      minZoom: 4,
      maxZoom: 10,
    });
    m.touchZoomRotate.disableRotation();
    if (interactive) m.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-left");
    m.addControl(
      new maplibregl.AttributionControl({
        compact: true,
        customAttribution: "Land: Natural Earth; protected areas: WDPCA (UNEP-WCMC); cells: H3",
      }),
    );

    let hovered: { source: string; id: string } | null = null;
    const setHover = (next: { source: string; id: string } | null) => {
      if (hovered) m.setFeatureState(hovered, { hover: false });
      hovered = next;
      if (next) m.setFeatureState(next, { hover: true });
    };
    const fills = ["coarse-fill", "fine-fill"];
    const pick = (e: MapMouseEvent) => {
      const visible = fills.filter((id) => m.getLayoutProperty(id, "visibility") !== "none");
      return m.queryRenderedFeatures(e.point, { layers: visible })[0];
    };
    m.on("mousemove", (e) => {
      const f = pick(e);
      m.getCanvas().style.cursor = f ? "pointer" : "";
      setHover(f ? { source: f.source, id: String(f.id) } : null);
      handlers.current.onCellHover?.(toProps(f));
    });
    m.on("mouseout", () => {
      setHover(null);
      handlers.current.onCellHover?.(null);
    });
    m.on("click", (e) => handlers.current.onCellClick?.(toProps(pick(e))));
    m.on("load", () => {
      m.resize();
      m.fitBounds(PH_BOUNDS, { padding: 16, duration: 0 });
      setReady(true);
    });
    // "idle" can fire before GeoJSON parsing ends; wait for the sources themselves.
    const onData = () => {
      if (m.isSourceLoaded("land") && m.isSourceLoaded(SOURCES.coarse) && m.isSourceLoaded(SOURCES.fine)) {
        m.once("idle", () => setDrawn(true));
        m.off("sourcedata", onData);
      }
    };
    m.on("sourcedata", onData);
    // The container is often sized after the map is created (grid layout, lazy load).
    const ro = new ResizeObserver(() => m.resize());
    ro.observe(el.current);
    map.current = m;
    return () => {
      ro.disconnect();
      m.remove();
      map.current = null;
    };
    // The map is created once; props are applied by the effects below.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Layer, colour and resolution switch.
  useEffect(() => {
    const m = map.current;
    if (!m || !ready) return;
    const fill = fillFor(mode, memberColor);
    m.setPaintProperty("fine-fill", "fill-color", fill);
    m.setPaintProperty("coarse-fill", "fill-color", fill);
    const single = mode === "species";
    for (const part of ["fill", "edge", "hover", "selected"]) {
      m.setLayoutProperty(`coarse-${part}`, "visibility", single ? "none" : "visible");
      m.setLayerZoomRange(`coarse-${part}`, 0, FINE_ZOOM);
      m.setLayerZoomRange(`fine-${part}`, single ? 0 : FINE_ZOOM, 24);
    }
  }, [mode, memberColor, ready]);

  useEffect(() => {
    const m = map.current;
    if (!m || !ready) return;
    for (const id of prevMembers.current) m.setFeatureState({ source: SOURCES.fine, id }, { member: false });
    for (const id of memberCells ?? []) m.setFeatureState({ source: SOURCES.fine, id }, { member: true });
    prevMembers.current = memberCells ?? [];
  }, [memberCells, ready]);

  useEffect(() => {
    const m = map.current;
    if (!m || !ready || !bounds) return;
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    m.fitBounds(
      [
        [bounds[0], bounds[1]],
        [bounds[2], bounds[3]],
      ],
      { padding: 40, maxZoom: 7.5, duration: reduce ? 0 : 300 },
    );
  }, [bounds, ready]);

  useEffect(() => {
    const m = map.current;
    if (!m || !ready) return;
    m.setLayoutProperty("pa", "visibility", showPA ? "visible" : "none");
  }, [showPA, ready]);

  useEffect(() => {
    const m = map.current;
    if (!m || !ready) return;
    const sourceOf = (id: string) => (id.startsWith("84") ? SOURCES.coarse : SOURCES.fine);
    if (prevSelected.current) m.setFeatureState({ source: sourceOf(prevSelected.current), id: prevSelected.current }, { selected: false });
    if (selectedCell) m.setFeatureState({ source: sourceOf(selectedCell), id: selectedCell }, { selected: true });
    prevSelected.current = selectedCell ?? null;
  }, [selectedCell, ready]);

  return (
    <div className="hexmap-wrap">
      <div ref={el} className="hexmap" role="region" aria-label={label} aria-busy={!drawn} />
      {!drawn ? (
        <div className="hexmap__loading" role="status">
          <span className="status__pulse" aria-hidden="true" />
          Drawing the map…
        </div>
      ) : null}
    </div>
  );
}
