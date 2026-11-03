import * as maplibregl from "maplibre-gl";
import type {
  DataDrivenPropertyValueSpecification,
  ExpressionSpecification,
  GeoJSONSource,
  Map as MLMap,
  MapGeoJSONFeature,
  MapMouseEvent,
} from "maplibre-gl";
// MapLibre 6 runs an ES-module worker that imports a shared chunk by relative path.
// Let Vite bundle the worker with its imports and hand MapLibre the result.
import workerUrl from "maplibre-gl/dist/maplibre-gl-worker.mjs?worker&url";
import "maplibre-gl/dist/maplibre-gl.css";
import { useEffect, useRef, useState } from "react";
import { geoUrl } from "../data/api";
import type { CellProps } from "../data/schema";

maplibregl.setWorkerUrl(workerUrl);

export type MapMode = "hotspots" | "species" | "effort";
export type HoverInfo = { cell: CellProps; x: number; y: number } | null;
export type CellSet = { fine: string[]; coarse: string[] };

const PH_BOUNDS: [[number, number], [number, number]] = [
  [116.4, 4.4],
  [127.0, 21.2],
];
/** Below this zoom, aggregate cells (H3 res 4, ~1,770 km²) replace fine cells (res 5, ~250 km²). */
const FINE_ZOOM = 6.5;
const SRC = { fine: "cells", coarse: "cells4" } as const;
const EMPTY = { type: "FeatureCollection" as const, features: [] };
const CLEAR = "rgba(0,0,0,0)";

function css(name: string): string {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim() || "#999";
}

const MEMBER: ExpressionSpecification = ["boolean", ["feature-state", "member"], false];
const PREVIEW: ExpressionSpecification = ["boolean", ["feature-state", "preview"], false];
const PRIORITY: ExpressionSpecification = ["+", ["get", "n_high"], ["get", "n_watch"]];

function fill(mode: MapMode): ExpressionSpecification {
  if (mode === "effort") {
    return ["step", ["get", "effort"], "#edefed", 10, "#d1d6d1", 50, "#adb3ae", 100, "#818882", 500, "#59605a"];
  }
  if (mode === "species") {
    return ["case", MEMBER, css("--tier-high"), PREVIEW, css("--hot-1"), CLEAR];
  }
  return [
    "case",
    PREVIEW,
    css("--highlight"),
    ["step", PRIORITY, CLEAR, 1, css("--hot-1"), 2, css("--hot-2"), 3, css("--hot-3"), 4, css("--hot-4")],
  ];
}

/** Outlines only where a cell is drawn; empty cells stay invisible. */
function edgeOpacity(mode: MapMode): DataDrivenPropertyValueSpecification<number> {
  if (mode === "effort") return 0.6;
  if (mode === "species") return ["case", ["any", MEMBER, PREVIEW], 0.95, 0];
  return ["case", ["any", PREVIEW, [">", PRIORITY, 0]], 0.95, 0];
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
 * The atlas map. Locations are only ever H3 cells cut to the coastline, never
 * points: res 4 at the country view, res 5 once zoomed in.
 */
export function HexMap({
  mode,
  member,
  preview,
  showPA = false,
  selectedCell,
  onCellClick,
  onHover,
  interactive = true,
  bounds,
  padding = 40,
  label,
}: {
  mode: MapMode;
  /** The chosen plant's cells, fine and coarse. */
  member?: CellSet | null;
  /** A plant being hovered in a list: its cells glow until the pointer leaves. */
  preview?: CellSet | null;
  showPA?: boolean;
  selectedCell?: string | null;
  onCellClick?: (cell: CellProps | null) => void;
  onHover?: (info: HoverInfo) => void;
  interactive?: boolean;
  /** [west, south, east, north] to frame, e.g. one plant's cells */
  bounds?: [number, number, number, number] | null;
  padding?: number | { top: number; bottom: number; left: number; right: number };
  label: string;
}) {
  const el = useRef<HTMLDivElement>(null);
  const map = useRef<MLMap | null>(null);
  const [ready, setReady] = useState(false);
  const [drawn, setDrawn] = useState(false);
  const handlers = useRef({ onCellClick, onHover });
  handlers.current = { onCellClick, onHover };
  const loaded = useRef({ fine: false, pa: false });
  const needFine = useRef(!!member);
  const states = useRef<Record<"member" | "preview" | "selected", { source: string; id: string }[]>>({
    member: [],
    preview: [],
    selected: [],
  });

  const load = (m: MLMap, which: "fine" | "pa") => {
    if (loaded.current[which]) return;
    loaded.current[which] = true;
    const src = m.getSource(which === "fine" ? SRC.fine : "pa") as GeoJSONSource | undefined;
    src?.setData(geoUrl(which === "fine" ? "cells.geojson" : "pa.geojson"));
  };

  const setState = (key: "member" | "preview" | "selected", next: { source: string; id: string }[]) => {
    const m = map.current;
    if (!m) return;
    for (const f of states.current[key]) m.setFeatureState(f, { [key]: false });
    for (const f of next) m.setFeatureState(f, { [key]: true });
    states.current[key] = next;
  };

  useEffect(() => {
    if (!el.current) return;
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const cellLayers = (source: string, id: string) =>
      [
        { id: `${id}-fill`, type: "fill", source, paint: { "fill-color": CLEAR, "fill-opacity": 0.95 } },
        {
          id: `${id}-edge`,
          type: "line",
          source,
          paint: {
            "line-color": css("--sheet"),
            "line-width": ["interpolate", ["linear"], ["zoom"], 4, 0.6, 9, 1.4],
            "line-opacity": 0,
          },
        },
        {
          id: `${id}-hover`,
          type: "line",
          source,
          paint: { "line-color": css("--ink"), "line-width": ["case", ["boolean", ["feature-state", "hover"], false], 2, 0] },
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
          [SRC.coarse]: { type: "geojson", data: geoUrl("cells_r4.geojson"), promoteId: "h3" },
          // Fine cells and protected areas are large; they load on first need.
          [SRC.fine]: { type: "geojson", data: EMPTY, promoteId: "h3" },
          pa: { type: "geojson", data: EMPTY },
        },
        layers: [
          { id: "sea", type: "background", paint: { "background-color": css("--sea") } },
          { id: "land", type: "fill", source: "land", paint: { "fill-color": css("--land") } },
          ...cellLayers(SRC.coarse, "coarse"),
          ...cellLayers(SRC.fine, "fine"),
          {
            id: "pa",
            type: "fill",
            source: "pa",
            layout: { visibility: "none" },
            paint: { "fill-color": css("--c-habitat"), "fill-opacity": 0.14, "fill-outline-color": css("--c-habitat") },
          },
          { id: "land-edge", type: "line", source: "land", paint: { "line-color": css("--rule-strong"), "line-width": 0.7 } },
        ],
      },
      bounds: PH_BOUNDS,
      fitBoundsOptions: { padding: 16 },
      // Always interactive so hover and click work; a locked map just cannot pan or zoom.
      interactive: true,
      dragPan: interactive,
      scrollZoom: interactive,
      boxZoom: interactive,
      doubleClickZoom: interactive,
      keyboard: interactive,
      touchZoomRotate: interactive,
      touchPitch: false,
      attributionControl: false,
      dragRotate: false,
      pitchWithRotate: false,
      fadeDuration: reduce ? 0 : 250,
      minZoom: 4,
      maxZoom: 10,
    });
    if (interactive) m.touchZoomRotate.disableRotation();
    if (interactive) m.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-left");
    m.addControl(
      new maplibregl.AttributionControl({
        compact: true,
        customAttribution: "Land: Natural Earth; protected areas: WDPCA; cells: H3",
      }),
      "bottom-right",
    );

    let hovered: { source: string; id: string } | null = null;
    const pick = (e: MapMouseEvent) => {
      const z = m.getZoom();
      const layer = z < FINE_ZOOM ? "coarse-fill" : "fine-fill";
      return m.queryRenderedFeatures(e.point, { layers: [layer] }).find((f) => {
        const c = toProps(f);
        return c && (c.n_cohort > 0 || c.effort > 0);
      });
    };
    m.on("mousemove", (e) => {
      const f = pick(e);
      const next = f ? { source: f.source, id: String(f.id) } : null;
      if (hovered?.id !== next?.id) {
        if (hovered) m.setFeatureState(hovered, { hover: false });
        if (next) m.setFeatureState(next, { hover: true });
        hovered = next;
      }
      m.getCanvas().style.cursor = f ? "pointer" : "";
      const cell = toProps(f);
      handlers.current.onHover?.(cell ? { cell, x: e.point.x, y: e.point.y } : null);
    });
    m.on("mouseout", () => {
      if (hovered) m.setFeatureState(hovered, { hover: false });
      hovered = null;
      handlers.current.onHover?.(null);
    });
    m.on("click", (e) => handlers.current.onCellClick?.(toProps(pick(e))));
    m.on("zoomend", () => {
      if (m.getZoom() >= FINE_ZOOM - 0.5) load(m, "fine");
    });
    m.on("load", () => {
      m.resize();
      // The credits start folded behind their (i) button so they never cover the map.
      m.getContainer().querySelector(".maplibregl-ctrl-attrib")?.classList.remove("maplibregl-compact-show");
      if (needFine.current) load(m, "fine");
      setReady(true);
    });
    const onData = () => {
      const fineOk = !needFine.current || m.isSourceLoaded(SRC.fine);
      if (m.isSourceLoaded("land") && m.isSourceLoaded(SRC.coarse) && fineOk) {
        m.once("idle", () => setDrawn(true));
        m.off("sourcedata", onData);
      }
    };
    m.on("sourcedata", onData);
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

  // Layer styling and the coarse/fine switch.
  useEffect(() => {
    const m = map.current;
    if (!m || !ready) return;
    for (const res of ["coarse", "fine"]) {
      m.setPaintProperty(`${res}-fill`, "fill-color", fill(mode));
      m.setPaintProperty(`${res}-edge`, "line-opacity", edgeOpacity(mode));
    }
    for (const part of ["fill", "edge", "hover", "selected"]) {
      m.setLayerZoomRange(`coarse-${part}`, 0, FINE_ZOOM);
      m.setLayerZoomRange(`fine-${part}`, FINE_ZOOM, 24);
    }
  }, [mode, ready]);

  useEffect(() => {
    const m = map.current;
    if (!m || !ready) return;
    needFine.current = !!member;
    if (member) load(m, "fine");
    setState("member", [
      ...(member?.coarse ?? []).map((id) => ({ source: SRC.coarse, id })),
      ...(member?.fine ?? []).map((id) => ({ source: SRC.fine, id })),
    ]);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [member, ready]);

  useEffect(() => {
    if (!ready) return;
    setState("preview", [
      ...(preview?.coarse ?? []).map((id) => ({ source: SRC.coarse, id })),
      ...(preview?.fine ?? []).map((id) => ({ source: SRC.fine, id })),
    ]);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [preview, ready]);

  useEffect(() => {
    if (!ready) return;
    const src = selectedCell && selectedCell[1] === "4" ? SRC.coarse : SRC.fine;
    setState("selected", selectedCell ? [{ source: src, id: selectedCell }] : []);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedCell, ready]);

  const boundsKey = bounds ? bounds.join(",") : "ph";
  useEffect(() => {
    const m = map.current;
    if (!m || !ready) return;
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const target: [[number, number], [number, number]] = bounds
      ? [
          [bounds[0], bounds[1]],
          [bounds[2], bounds[3]],
        ]
      : PH_BOUNDS;
    m.fitBounds(target, { padding, maxZoom: 7.2, duration: reduce ? 0 : 800 });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [boundsKey, ready]);

  useEffect(() => {
    const m = map.current;
    if (!m || !ready) return;
    if (showPA) load(m, "pa");
    m.setLayoutProperty("pa", "visibility", showPA ? "visible" : "none");
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [showPA, ready]);

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
