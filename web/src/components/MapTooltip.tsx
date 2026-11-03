import type { SpeciesSummary } from "../data/schema";
import { fmtInt } from "../lib/format";
import { TIER_LABEL, TIER_ORDER } from "../lib/vocab";
import type { HoverInfo } from "./HexMap";

/**
 * Follows the pointer over the map: how many atlas plants were recorded in the
 * area, and the first few by priority. Purely visual; the same facts are in the
 * panel and lists for keyboard and screen-reader users.
 */
export function MapTooltip({
  info,
  bySlug,
  mode,
  width,
  height,
}: {
  info: HoverInfo;
  bySlug: Map<string, SpeciesSummary>;
  mode: "hotspots" | "species" | "effort";
  width: number;
  height: number;
}) {
  if (!info) return null;
  const { cell, x, y } = info;
  const plants = cell.species
    .map((s) => bySlug.get(s))
    .filter((s): s is SpeciesSummary => !!s && !s.gate)
    .sort((a, b) => TIER_ORDER.indexOf(a.tier) - TIER_ORDER.indexOf(b.tier) || (a.rank ?? 99) - (b.rank ?? 99));
  const priority = cell.n_high + cell.n_watch;
  const left = x > width - 280 ? x - 260 : x + 16;
  const top = y > height - 170 ? y - 150 : y + 16;
  return (
    <div className="map-tip" style={{ left, top }} aria-hidden="true">
      {mode === "effort" ? (
        <p className="map-tip__head">
          <b className="num">{fmtInt(cell.effort)}</b> plant records from botanists here
        </p>
      ) : (
        <p className="map-tip__head">
          {priority > 0 ? (
            <>
              <b className="num">{priority}</b> of the {plants.length} ranked plants here{" "}
              {priority === 1 ? "needs" : "need"} attention or watching
            </>
          ) : plants.length ? (
            <>
              <b className="num">{plants.length}</b> ranked {plants.length === 1 ? "plant" : "plants"} recorded here
            </>
          ) : (
            "No ranked plants recorded here"
          )}
        </p>
      )}
      {plants.length ? (
        <ul className="map-tip__list">
          {plants.slice(0, 4).map((s) => (
            <li key={s.slug}>
              <span className={`dot dot--${s.tier === "High attention" ? "high" : s.tier === "Watch" ? "watch" : "lower"}`} />
              <span>{s.vernacular || s.name}</span>
              <span className="map-tip__tier">{TIER_LABEL[s.tier]}</span>
            </li>
          ))}
          {plants.length > 4 ? <li className="map-tip__more">and {plants.length - 4} more. Click the area to see them all.</li> : null}
        </ul>
      ) : null}
    </div>
  );
}
