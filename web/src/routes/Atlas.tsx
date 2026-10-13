import { X } from "lucide-react";
import { useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import type { MapMode } from "../components/HexMap";
import { HexMap } from "../components/HexMapLazy";
import { WithData } from "../components/Status";
import { TierChip } from "../components/TierChip";
import { useCells, useCellsCoarse, useSpecies, useSpeciesList } from "../data/api";
import type { CellProps, SpeciesSummary } from "../data/schema";
import { fmtInt, fmtPct } from "../lib/format";
import { TIER_ORDER } from "../lib/vocab";

const LAYERS: { id: MapMode; label: string; hint: string }[] = [
  { id: "hotspots", label: "Priority hotspots", hint: "Plants on high attention or watch recorded in each cell" },
  { id: "species", label: "One plant", hint: "Cells where the chosen plant was recorded" },
  { id: "effort", label: "Survey effort", hint: "All plant records in GBIF per cell: where botanists have looked" },
];

export function Atlas() {
  const list = useSpeciesList();
  const cells = useCells();
  const coarse = useCellsCoarse();
  return (
    <WithData state={list}>
      {(species) => (
        <WithData state={cells}>
          {(fine) => (
            <WithData state={coarse}>
              {(agg) => (
                <AtlasView
                  species={species}
                  cells={[...fine.features, ...agg.features].map((f) => f.properties)}
                />
              )}
            </WithData>
          )}
        </WithData>
      )}
    </WithData>
  );
}

function AtlasView({ species, cells }: { species: SpeciesSummary[]; cells: CellProps[] }) {
  const [params, setParams] = useSearchParams();
  const sp = params.get("sp");
  const layer = (params.get("layer") as MapMode) ?? (sp ? "species" : "hotspots");
  const cellId = params.get("cell");
  const [showPA, setShowPA] = useState(true);
  const [hover, setHover] = useState<CellProps | null>(null);

  const bySlug = useMemo(() => new Map(species.map((s) => [s.slug, s])), [species]);
  const byCell = useMemo(() => new Map(cells.map((c) => [c.h3, c])), [cells]);
  const chosen = sp ? bySlug.get(sp) ?? null : null;
  const detail = useSpecies(layer === "species" && chosen ? chosen.slug : undefined);
  const selected = cellId ? byCell.get(cellId) ?? null : null;

  const update = (patch: Record<string, string | null>) => {
    const p = new URLSearchParams(params);
    for (const [k, v] of Object.entries(patch)) {
      if (v === null) p.delete(k);
      else p.set(k, v);
    }
    setParams(p, { replace: true });
  };

  const ranked = species
    .filter((s) => !s.gate)
    .sort((a, b) => TIER_ORDER.indexOf(a.tier) - TIER_ORDER.indexOf(b.tier) || (a.rank ?? 0) - (b.rank ?? 0));
  const memberCells = detail.status === "ready" ? detail.data.cells : undefined;
  const bounds = detail.status === "ready" ? detail.data.bounds : null;
  const activeLayer = LAYERS.find((l) => l.id === layer) ?? LAYERS[0];

  return (
    <div className="atlas">
      <div className="atlas__map">
        <HexMap
          mode={layer}
          memberCells={layer === "species" ? memberCells : []}
          memberColor="var(--tier-high)"
          showPA={showPA}
          selectedCell={cellId}
          bounds={layer === "species" ? bounds : null}
          onCellHover={setHover}
          onCellClick={(c) => update({ cell: c ? c.h3 : null })}
          label={`Atlas map. Layer: ${activeLayer.label}. Use the panel to choose plants and cells.`}
        />
        {hover ? (
          <div className="atlas__hover" aria-hidden="true">
            <CellSummaryLine c={hover} />
          </div>
        ) : null}
      </div>

      <aside className="atlas__panel" aria-label="Atlas controls and details">
        <div className="atlas__panel-grip" aria-hidden="true" />
        <fieldset className="segmented">
          <legend className="sr-only">Map layer</legend>
          {LAYERS.map((l) => (
            <label key={l.id} className={`segmented__opt${layer === l.id ? " is-on" : ""}`}>
              <input
                type="radio"
                name="layer"
                value={l.id}
                checked={layer === l.id}
                onChange={() => update({ layer: l.id })}
              />
              {l.label}
            </label>
          ))}
        </fieldset>
        <p className="atlas__hint">{activeLayer.hint}.</p>
        <Legend layer={layer} />
        <label className="check">
          <input type="checkbox" checked={showPA} onChange={(e) => setShowPA(e.target.checked)} />
          Show protected areas (dashed)
        </label>

        {selected ? (
          <CellCard c={selected} bySlug={bySlug} onClose={() => update({ cell: null })} onPick={(slug) => update({ sp: slug, layer: "species" })} />
        ) : null}

        {layer === "species" ? (
          <div className="atlas__section">
            <label className="field">
              <span className="field__label">Plant</span>
              <select value={chosen?.slug ?? ""} onChange={(e) => update({ sp: e.target.value || null })}>
                <option value="">Choose a plant…</option>
                {species
                  .slice()
                  .sort((a, b) => a.name.localeCompare(b.name))
                  .map((s) => (
                    <option key={s.slug} value={s.slug}>
                      {s.name}
                      {s.vernacular ? ` (${s.vernacular})` : ""}
                    </option>
                  ))}
              </select>
            </label>
            {chosen ? (
              <div className="atlas__chosen">
                <TierChip tier={chosen.tier} />
                <p>
                  Recorded in <b className="num">{fmtInt(chosen.n_cells)}</b> cells.{" "}
                  <Link to={`/species/${chosen.slug}`}>Open the full profile</Link>
                </p>
              </div>
            ) : null}
          </div>
        ) : null}

        {layer !== "species" ? (
          <div className="atlas__section">
            <h2 className="atlas__h">Ranked plants</h2>
            <ul className="atlas__list">
              {ranked.map((s) => (
                <li key={s.slug}>
                  <button type="button" className="atlas__item" onClick={() => update({ sp: s.slug, layer: "species", cell: null })}>
                    <span>
                      <i className="binomial">{s.name}</i>
                      <span className="atlas__vern">{s.vernacular}</span>
                    </span>
                    <TierChip tier={s.tier} compact />
                  </button>
                </li>
              ))}
            </ul>
          </div>
        ) : null}
      </aside>
    </div>
  );
}

function Legend({ layer }: { layer: MapMode }) {
  if (layer === "species") {
    return (
      <div className="legend-row">
        <span className="legend__swatch" style={{ background: "var(--tier-high)" }} aria-hidden="true" /> Cell with at
        least one usable record
      </div>
    );
  }
  if (layer === "effort") {
    const steps = ["#edefed", "#d1d6d1", "#adb3ae", "#818882", "#59605a"];
    return (
      <div className="legend-ramp">
        <span className="ramp" aria-hidden="true">
          {steps.map((c) => (
            <i key={c} style={{ background: c }} />
          ))}
        </span>
        <span className="ramp__ends">
          <span>under 10 records</span>
          <span>500 or more</span>
        </span>
      </div>
    );
  }
  return (
    <div className="legend-ramp">
      <span className="ramp" aria-hidden="true">
        <i style={{ background: "var(--hot-1)" }} />
        <i style={{ background: "var(--hot-2)" }} />
        <i style={{ background: "var(--hot-3)" }} />
        <i style={{ background: "var(--hot-4)" }} />
      </span>
      <span className="ramp__ends">
        <span>1 plant</span>
        <span>4 or more</span>
      </span>
    </div>
  );
}

function CellSummaryLine({ c }: { c: CellProps }) {
  const pri = c.n_high + c.n_watch;
  return (
    <span>
      {pri ? `${pri} on high attention or watch, ` : ""}
      {c.n_cohort} atlas plants recorded; {fmtInt(c.effort)} plant records in all
      {c.pa !== null ? `; ${fmtPct(c.pa)} protected` : ""}
    </span>
  );
}

function CellCard({
  c,
  bySlug,
  onClose,
  onPick,
}: {
  c: CellProps;
  bySlug: Map<string, SpeciesSummary>;
  onClose: () => void;
  onPick: (slug: string) => void;
}) {
  const here = c.species
    .map((s) => bySlug.get(s))
    .filter((s): s is SpeciesSummary => !!s)
    .sort((a, b) => TIER_ORDER.indexOf(a.tier) - TIER_ORDER.indexOf(b.tier) || a.name.localeCompare(b.name));
  return (
    <section className="cellcard sheet" aria-live="polite" aria-label="Selected cell">
      <header className="cellcard__head">
        <h2 className="atlas__h">Selected area, about {c.h3[1] === "4" ? "1,770" : "250"} km²</h2>
        <button type="button" className="icon-button" onClick={onClose} aria-label="Clear the selected cell">
          <X size={16} />
        </button>
      </header>
      <dl className="cellcard__facts">
        <div>
          <dt>Atlas plants recorded</dt>
          <dd className="num">{c.n_cohort}</dd>
        </div>
        <div>
          <dt>Protected</dt>
          <dd className="num">{fmtPct(c.pa)}</dd>
        </div>
        <div>
          <dt>All plant records</dt>
          <dd className="num">{fmtInt(c.effort)}</dd>
        </div>
      </dl>
      {here.length ? (
        <ul className="atlas__list">
          {here.map((s) => (
            <li key={s.slug}>
              <button type="button" className="atlas__item" onClick={() => onPick(s.slug)}>
                <span>
                  <i className="binomial">{s.name}</i>
                  <span className="atlas__vern">{s.vernacular}</span>
                </span>
                <TierChip tier={s.tier} compact />
              </button>
            </li>
          ))}
        </ul>
      ) : (
        <p className="empty-note">No atlas plant has a usable record in this cell. Survey effort here may be low.</p>
      )}
    </section>
  );
}
