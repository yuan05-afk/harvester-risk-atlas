import { Download } from "lucide-react";
import { useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { Caterpillar } from "../components/charts/Caterpillar";
import { WithData } from "../components/Status";
import { TierChip } from "../components/TierChip";
import { useSpeciesList } from "../data/api";
import type { SpeciesSummary, Tier } from "../data/schema";
import { fmtPct, fmtScore } from "../lib/format";
import { COMPONENT_META, gateReason, TIER_META } from "../lib/vocab";

const RANKED_TIERS: Tier[] = ["High attention", "Watch", "Lower"];

export function Rankings() {
  const list = useSpeciesList();
  return <WithData state={list}>{(species) => <RankingsView species={species} />}</WithData>;
}

function RankingsView({ species }: { species: SpeciesSummary[] }) {
  const [params, setParams] = useSearchParams();
  const active = new Set((params.get("tier")?.split(",").filter(Boolean) as Tier[]) ?? []);
  const [asTable, setAsTable] = useState(false);
  const scored = species.filter((s) => !s.gate);
  const shown = active.size ? scored.filter((s) => active.has(s.tier)) : scored;
  const notScored = species.filter((s) => s.gate).sort((a, b) => a.gate.localeCompare(b.gate) || a.name.localeCompare(b.name));

  const toggle = (t: Tier) => {
    const next = new Set(active);
    if (next.has(t)) next.delete(t);
    else next.add(t);
    const p = new URLSearchParams(params);
    if (next.size) p.set("tier", [...next].join(","));
    else p.delete("tier");
    setParams(p, { replace: true });
  };

  const csv = useMemo(() => toCsv(species), [species]);

  return (
    <div className="page">
      <header className="page__head">
        <h1>Rankings</h1>
        <p className="lede">
          {scored.length} native plants, ordered by median rank. The line is the 90% interval: where lines overlap, the
          evidence cannot tell those plants apart.
        </p>
      </header>

      <div className="toolbar" role="group" aria-label="Filter by tier">
        {RANKED_TIERS.map((t) => (
          <button
            key={t}
            type="button"
            className={`filter-chip${active.has(t) ? " is-on" : ""}`}
            aria-pressed={active.has(t)}
            onClick={() => toggle(t)}
          >
            <span className="filter-chip__swatch" style={{ background: TIER_META[t].color }} aria-hidden="true" />
            {t} <span className="num filter-chip__n">{scored.filter((s) => s.tier === t).length}</span>
          </button>
        ))}
        <span className="toolbar__spacer" />
        <button type="button" className="link-button" aria-pressed={asTable} onClick={() => setAsTable((v) => !v)}>
          {asTable ? "Show chart" : "Show as table"}
        </button>
        <a
          className="button button--small"
          href={`data:text/csv;charset=utf-8,${encodeURIComponent(csv)}`}
          download="harvester-risk-atlas-rankings.csv"
        >
          <Download size={14} aria-hidden="true" /> CSV
        </a>
      </div>

      <section className="sheet ranking-sheet" aria-label="Ranked plants">
        {asTable ? <RankTable rows={shown} /> : <Caterpillar species={shown} />}
        <p className="figure__source">
          Rank 1 is the highest priority. Ranks and intervals come from 2,000 simulations that vary the weights and
          resample the evidence. <Link to="/methods#uncertainty">How the intervals are made</Link>.
        </p>
      </section>

      <section className="band">
        <div className="band__head">
          <h2>Listed but not ranked</h2>
          <p>
            {notScored.length} plants in the atlas are not ranked. They are kept so that you can look them up, and so
            that you can see why.
          </p>
        </div>
        <ul className="unranked">
          {notScored.map((s) => (
            <li key={s.slug}>
              <Link to={`/species/${s.slug}`}>
                <i className="binomial">{s.name}</i>
              </Link>{" "}
              <span className="unranked__vern">{s.vernacular}</span>
              <span className="unranked__why">{gateReason(s)}</span>
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}

function RankTable({ rows }: { rows: SpeciesSummary[] }) {
  const sorted = [...rows].sort((a, b) => (a.rank ?? 0) - (b.rank ?? 0));
  return (
    <div className="table-wrap">
      <table className="data-table">
        <thead>
          <tr>
            <th scope="col" className="num">
              Rank
            </th>
            <th scope="col">Plant</th>
            <th scope="col">Tier</th>
            <th scope="col" className="num">
              90% interval
            </th>
            <th scope="col" className="num">
              Top quarter
            </th>
            {(["R", "H", "E"] as const).map((k) => (
              <th scope="col" key={k} className="num">
                {COMPONENT_META[k].short}
              </th>
            ))}
            <th scope="col" className="num">
              Score
            </th>
          </tr>
        </thead>
        <tbody>
          {sorted.map((s) => (
            <tr key={s.slug}>
              <td className="num">{s.rank}</td>
              <th scope="row">
                <Link to={`/species/${s.slug}`}>
                  <i className="binomial">{s.name}</i>
                </Link>
                <span className="cell-sub">{s.vernacular}</span>
              </th>
              <td>
                <TierChip tier={s.tier} compact />
              </td>
              <td className="num">
                {s.rank_ci[0]}–{s.rank_ci[1]}
              </td>
              <td className="num">{fmtPct(s.p_top)}</td>
              {(["R", "H", "E"] as const).map((k) => (
                <td key={k} className="num">
                  {fmtScore(s.components[k])}
                </td>
              ))}
              <td className="num">{fmtScore(s.score)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function toCsv(species: SpeciesSummary[]): string {
  const head = [
    "scientific_name",
    "vernacular",
    "family",
    "tier",
    "not_ranked_reason",
    "rank_median",
    "rank_p05",
    "rank_p95",
    "p_top_quartile",
    "range_restriction",
    "harvest_sensitivity",
    "habitat_exposure",
    "climate_exposure",
    "score",
    "dao_2026_20",
  ];
  const esc = (v: unknown) => {
    const s = v === null || v === undefined ? "" : String(v);
    return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
  };
  const rows = species.map((s) =>
    [
      s.name,
      s.vernacular,
      s.family,
      s.tier,
      s.gate ? gateReason(s) : "",
      s.rank,
      s.rank_ci[0],
      s.rank_ci[1],
      s.p_top,
      s.components.R,
      s.components.H,
      s.components.E,
      s.components.C,
      s.score,
      s.dao,
    ]
      .map(esc)
      .join(","),
  );
  return [head.join(","), ...rows].join("\n");
}
