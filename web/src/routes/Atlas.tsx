import { ArrowLeft, FileText, Layers, Search, X } from "lucide-react";
import { AnimatePresence, motion } from "motion/react";
import { useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import type { CellSet, HoverInfo, MapMode } from "../components/HexMap";
import { HexMap } from "../components/HexMapLazy";
import { MapTooltip } from "../components/MapTooltip";
import { PlantRow } from "../components/PlantCard";
import { PlantPhoto } from "../components/PlantPhoto";
import { LevelMeter } from "../components/Reasons";
import { Stamp } from "../components/Stamp";
import { Loading, WithData } from "../components/Status";
import { useCells, useCellsCoarse, useSpecies, useSpeciesList } from "../data/api";
import type { CellProps, SpeciesDetail, SpeciesSummary, Tier } from "../data/schema";
import { explain, summary } from "../lib/explain";
import { fmtInt, fmtPct } from "../lib/format";
import { useWidth } from "../lib/useWidth";
import { COMPONENT_META, rankSentence, SCORED_COMPONENTS, TIER_LABEL, TIER_META, TIER_ORDER } from "../lib/vocab";

export function Atlas() {
  const list = useSpeciesList();
  const fine = useCells();
  const coarse = useCellsCoarse();
  return (
    <WithData state={list}>
      {(species) => (
        <WithData state={fine}>
          {(f) => (
            <WithData state={coarse}>
              {(c) => (
                <AtlasView
                  species={species}
                  fine={f.features.map((x) => x.properties)}
                  coarse={c.features.map((x) => x.properties)}
                />
              )}
            </WithData>
          )}
        </WithData>
      )}
    </WithData>
  );
}

function AtlasView({ species, fine, coarse }: { species: SpeciesSummary[]; fine: CellProps[]; coarse: CellProps[] }) {
  const [params, setParams] = useSearchParams();
  const sp = params.get("sp");
  const cellId = params.get("cell");
  const layer: MapMode = sp ? "species" : params.get("layer") === "effort" ? "effort" : "hotspots";
  const [showPA, setShowPA] = useState(false);
  const [hover, setHover] = useState<HoverInfo>(null);
  const [previewSlug, setPreviewSlug] = useState<string | null>(null);
  const [mapRef, mapW] = useWidth<HTMLDivElement>(900);

  const bySlug = useMemo(() => new Map(species.map((s) => [s.slug, s])), [species]);
  const cellsOf = useMemo(() => {
    const idx = new Map<string, CellSet>();
    const add = (cells: CellProps[], key: keyof CellSet) => {
      for (const c of cells)
        for (const s of c.species) {
          if (!idx.has(s)) idx.set(s, { fine: [], coarse: [] });
          idx.get(s)![key].push(c.h3);
        }
    };
    add(fine, "fine");
    add(coarse, "coarse");
    return idx;
  }, [fine, coarse]);
  const byCell = useMemo(() => new Map([...fine, ...coarse].map((c) => [c.h3, c])), [fine, coarse]);

  const chosen = sp ? bySlug.get(sp) ?? null : null;
  const detail = useSpecies(chosen?.slug);
  const selected = cellId ? byCell.get(cellId) ?? null : null;
  const nScored = species.filter((s) => !s.gate).length;

  const update = (patch: Record<string, string | null>) => {
    const p = new URLSearchParams(params);
    for (const [k, v] of Object.entries(patch)) {
      if (v === null) p.delete(k);
      else p.set(k, v);
    }
    setParams(p, { replace: false });
  };

  const member = chosen ? cellsOf.get(chosen.slug) ?? null : null;
  const preview = previewSlug && previewSlug !== chosen?.slug ? cellsOf.get(previewSlug) ?? null : null;
  const bounds = chosen && detail.status === "ready" ? detail.data.bounds : null;

  return (
    <div className="atlas">
      <div className="atlas__map" ref={mapRef}>
        <HexMap
          mode={layer}
          member={member}
          preview={preview}
          showPA={showPA}
          selectedCell={cellId}
          bounds={bounds}
          padding={{ top: 60, bottom: 60, left: 60, right: 60 }}
          onHover={setHover}
          onCellClick={(c) => update({ cell: c && (c.n_cohort > 0 || layer === "effort") ? c.h3 : null })}
          label="Atlas map of the Philippines. The panel beside it lists the same plants and areas."
        />
        <MapTooltip info={hover} bySlug={bySlug} mode={layer} width={mapW} height={800} />
        <div className="map-controls">
          <div className="map-controls__group" role="group" aria-label="What the map shows">
            <Layers size={16} aria-hidden="true" />
            <button
              type="button"
              aria-pressed={layer !== "effort"}
              className={layer !== "effort" ? "is-on" : ""}
              onClick={() => update({ layer: null })}
            >
              Priority
            </button>
            <button
              type="button"
              aria-pressed={layer === "effort"}
              className={layer === "effort" ? "is-on" : ""}
              onClick={() => update({ layer: "effort", sp: null })}
            >
              Survey coverage
            </button>
          </div>
          <label className="map-controls__check">
            <input type="checkbox" checked={showPA} onChange={(e) => setShowPA(e.target.checked)} />
            Protected areas
          </label>
        </div>
        <MapLegend layer={layer} chosen={chosen} />
      </div>

      <aside className="atlas__panel" aria-label="Plants and areas">
        <div className="atlas__grip" aria-hidden="true" />
        <AnimatePresence mode="wait" initial={false}>
          {chosen ? (
            <motion.div key={`sp-${chosen.slug}`} {...panelMotion}>
              {detail.status === "ready" ? (
                <PlantPanel d={detail.data} nScored={nScored} onBack={() => update({ sp: null })} />
              ) : (
                <Loading label="Opening the plant" />
              )}
            </motion.div>
          ) : selected ? (
            <motion.div key={`cell-${selected.h3}`} {...panelMotion}>
              <AreaPanel
                c={selected}
                bySlug={bySlug}
                onClose={() => update({ cell: null })}
                onPick={(slug) => update({ sp: slug, cell: null })}
                onHover={setPreviewSlug}
              />
            </motion.div>
          ) : (
            <motion.div key="browse" {...panelMotion}>
              <BrowsePanel species={species} onPick={(slug) => update({ sp: slug })} onHover={setPreviewSlug} />
            </motion.div>
          )}
        </AnimatePresence>
      </aside>
    </div>
  );
}

const panelMotion = {
  initial: { opacity: 0, x: 16 },
  animate: { opacity: 1, x: 0 },
  exit: { opacity: 0, x: -12 },
  transition: { duration: 0.2, ease: "easeOut" as const },
};

function MapLegend({ layer, chosen }: { layer: MapMode; chosen: SpeciesSummary | null }) {
  return (
    <div className="map-legend map-legend--atlas">
      {layer === "species" && chosen ? (
        <>
          <span className="map-legend__title">
            Where {chosen.vernacular || chosen.name} was recorded
          </span>
          <span className="legend-row">
            <span className="legend__swatch" style={{ background: "var(--tier-high)" }} aria-hidden="true" /> Area with at
            least one reliable record
          </span>
        </>
      ) : layer === "effort" ? (
        <>
          <span className="map-legend__title">How thoroughly botanists have recorded plants here</span>
          <span className="ramp" aria-hidden="true">
            {["#edefed", "#d1d6d1", "#adb3ae", "#818882", "#59605a"].map((c) => (
              <i key={c} style={{ background: c }} />
            ))}
          </span>
          <span className="ramp__ends">
            <span>few records</span>
            <span>500 or more</span>
          </span>
        </>
      ) : (
        <>
          <span className="map-legend__title">Plants needing attention or watching, per area</span>
          <span className="ramp" aria-hidden="true">
            <i style={{ background: "var(--hot-1)" }} />
            <i style={{ background: "var(--hot-2)" }} />
            <i style={{ background: "var(--hot-3)" }} />
            <i style={{ background: "var(--hot-4)" }} />
          </span>
          <span className="ramp__ends">
            <span>1</span>
            <span>4 or more</span>
          </span>
        </>
      )}
    </div>
  );
}

function BrowsePanel({
  species,
  onPick,
  onHover,
}: {
  species: SpeciesSummary[];
  onPick: (slug: string) => void;
  onHover: (slug: string | null) => void;
}) {
  const [q, setQ] = useState("");
  const query = q.trim().toLowerCase();
  const match = (s: SpeciesSummary) =>
    !query || s.name.toLowerCase().includes(query) || s.vernacular.toLowerCase().includes(query) || s.family.toLowerCase().includes(query);
  const groups = (["High attention", "Watch", "Lower"] as Tier[]).map((t) => ({
    tier: t,
    items: species.filter((s) => s.tier === t && match(s)).sort((a, b) => (a.rank ?? 0) - (b.rank ?? 0)),
  }));
  const total = groups.reduce((a, g) => a + g.items.length, 0);
  return (
    <div className="panel">
      <h1 className="panel__title">Explore the atlas</h1>
      <p className="panel__lede">
        Point at a plant to see where it grows, or choose one to learn why it ranks where it does. Tap or click an area on
        the map to see what grows there.
      </p>
      <label className="panel-search">
        <Search size={16} aria-hidden="true" />
        <span className="sr-only">Filter plants</span>
        <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Filter by name or family" />
      </label>
      {total === 0 ? <p className="empty-note">No ranked plant matches “{q}”.</p> : null}
      {groups.map((g) =>
        g.items.length ? (
          <section key={g.tier} className="panel__group">
            <h2 className="panel__group-title">
              <span className={`dot dot--${TIER_META[g.tier].key}`} aria-hidden="true" />
              {TIER_LABEL[g.tier]}
              <span className="num panel__count">{g.items.length}</span>
            </h2>
            <ul className="plant-list">
              {g.items.map((s) => (
                <li key={s.slug}>
                  <PlantRow s={s} showTier={false} onSelect={onPick} onHover={onHover} />
                </li>
              ))}
            </ul>
          </section>
        ) : null,
      )}
    </div>
  );
}

function PlantPanel({ d, nScored, onBack }: { d: SpeciesDetail; nScored: number; onBack: () => void }) {
  const why = explain(d);
  const provinces = d.provinces.slice(0, 6);
  return (
    <div className="panel panel--plant">
      <button type="button" className="back-button" onClick={onBack}>
        <ArrowLeft size={16} aria-hidden="true" /> All plants
      </button>
      <div className="panel-plant__media">
        <PlantPhoto s={d} credit="below" eager />
        <Stamp tier={d.tier} rank={d.rank} of={d.rank !== null ? nScored : undefined} size={84} className="panel-plant__stamp" />
      </div>
      <h1 className="panel-plant__name">
        {d.vernacular ? <span>{d.vernacular}</span> : null}
        <i className="binomial">{d.name}</i>
      </h1>
      <p className="panel-plant__summary">{summary(d, nScored)}</p>
      {d.rank !== null ? <p className="panel-plant__rank">{rankSentence(d, nScored)}</p> : null}

      {!d.gate ? (
        <ul className="mini-reasons">
          {SCORED_COMPONENTS.map((k) => (
            <li key={k}>
              <span className="mini-reasons__label">{COMPONENT_META[k].label}</span>
              <LevelMeter value={d.components[k]} color={COMPONENT_META[k].color} label={COMPONENT_META[k].label} />
              <p>{why[k]}</p>
            </li>
          ))}
        </ul>
      ) : null}

      <section className="panel-plant__where">
        <h2>Where it grows</h2>
        <p>
          Recorded in <b className="num">{fmtInt(d.n_cells)}</b> areas across <b className="num">{d.provinces.length}</b>{" "}
          provinces. {d.pa_share !== null ? <>{fmtPct(d.pa_share)} of that area is protected.</> : null}
        </p>
        {provinces.length ? (
          <ul className="chips">
            {provinces.map((p) => (
              <li key={p.name}>{p.name}</li>
            ))}
            {d.provinces.length > provinces.length ? <li className="chips__more">+{d.provinces.length - provinces.length} more</li> : null}
          </ul>
        ) : null}
      </section>

      <div className="panel__actions">
        <Link to={`/species/${d.slug}`} className="button button--primary">
          Full profile
        </Link>
        <Link to={`/species/${d.slug}/brief`} className="button">
          <FileText size={16} aria-hidden="true" /> Field brief
        </Link>
      </div>
    </div>
  );
}

function AreaPanel({
  c,
  bySlug,
  onClose,
  onPick,
  onHover,
}: {
  c: CellProps;
  bySlug: Map<string, SpeciesSummary>;
  onClose: () => void;
  onPick: (slug: string) => void;
  onHover: (slug: string | null) => void;
}) {
  const plants = c.species
    .map((s) => bySlug.get(s))
    .filter((s): s is SpeciesSummary => !!s)
    .sort((a, b) => TIER_ORDER.indexOf(a.tier) - TIER_ORDER.indexOf(b.tier) || (a.rank ?? 99) - (b.rank ?? 99));
  const ranked = plants.filter((s) => !s.gate);
  const coarse = c.h3[1] === "4";
  return (
    <div className="panel">
      <button type="button" className="back-button" onClick={onClose}>
        <X size={16} aria-hidden="true" /> Close this area
      </button>
      <h1 className="panel__title">This area</h1>
      <p className="panel__lede">
        About {coarse ? "1,770" : "250"} km². Zoom in on the map to see smaller areas.
      </p>
      <dl className="area-stats">
        <div>
          <dt>Ranked plants recorded</dt>
          <dd className="num">{ranked.length}</dd>
        </div>
        <div>
          <dt>Needing attention or watching</dt>
          <dd className="num">{c.n_high + c.n_watch}</dd>
        </div>
        <div>
          <dt>Protected</dt>
          <dd className="num">{fmtPct(c.pa)}</dd>
        </div>
        <div>
          <dt>Plant records from botanists</dt>
          <dd className="num">{fmtInt(c.effort)}</dd>
        </div>
      </dl>
      {ranked.length ? (
        <ul className="plant-list">
          {ranked.map((s) => (
            <li key={s.slug}>
              <PlantRow s={s} onSelect={onPick} onHover={onHover} />
            </li>
          ))}
        </ul>
      ) : (
        <p className="empty-note">
          No ranked plant has a reliable record here. Few botanists may have recorded plants in this area; switch to
          Survey coverage to check.
        </p>
      )}
    </div>
  );
}
