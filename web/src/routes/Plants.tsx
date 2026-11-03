import { Download, Search } from "lucide-react";
import { motion } from "motion/react";
import { useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { Caterpillar } from "../components/charts/Caterpillar";
import { PlantCard } from "../components/PlantCard";
import { WithData } from "../components/Status";
import { useSpeciesList } from "../data/api";
import type { SpeciesSummary, Tier } from "../data/schema";
import { gateReason, TIER_LABEL, TIER_META } from "../lib/vocab";
import { Disclosure } from "./Species";

const RANKED: Tier[] = ["High attention", "Watch", "Lower"];

export function Plants() {
  const list = useSpeciesList();
  return <WithData state={list}>{(species) => <PlantsView species={species} />}</WithData>;
}

function PlantsView({ species }: { species: SpeciesSummary[] }) {
  const [params, setParams] = useSearchParams();
  const tier = params.get("tier") as Tier | null;
  const [q, setQ] = useState("");
  const query = q.trim().toLowerCase();
  const scored = species.filter((s) => !s.gate).sort((a, b) => (a.rank ?? 0) - (b.rank ?? 0) || a.name.localeCompare(b.name));
  const match = (s: SpeciesSummary) =>
    !query || [s.name, s.vernacular, s.family].some((v) => v.toLowerCase().includes(query));
  const notRanked = species.filter((s) => s.gate && match(s)).sort((a, b) => a.name.localeCompare(b.name));
  const csv = useMemo(() => toCsv(species), [species]);
  const setTier = (t: Tier | null) => {
    const p = new URLSearchParams(params);
    if (t) p.set("tier", t);
    else p.delete("tier");
    setParams(p, { replace: true });
  };

  return (
    <div className="page plants">
      <header className="page__head">
        <h1>The plants, ranked</h1>
        <p className="lede">
          {scored.length} native medicinal plants, from those most in need of attention to those of lower concern. The
          stamp on each shows its rank.
        </p>
      </header>

      <div className="plants-toolbar">
        <label className="panel-search">
          <Search size={16} aria-hidden="true" />
          <span className="sr-only">Filter plants</span>
          <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Filter by name or family" />
        </label>
        <div className="segmented-pills" role="group" aria-label="Show">
          <button type="button" aria-pressed={!tier} className={!tier ? "is-on" : ""} onClick={() => setTier(null)}>
            All
          </button>
          {RANKED.map((t) => (
            <button key={t} type="button" aria-pressed={tier === t} className={tier === t ? "is-on" : ""} onClick={() => setTier(t)}>
              <span className={`dot dot--${TIER_META[t].key}`} aria-hidden="true" />
              {TIER_LABEL[t]}
            </button>
          ))}
        </div>
      </div>

      {RANKED.filter((t) => !tier || tier === t).map((t) => {
        const items = scored.filter((s) => s.tier === t && match(s));
        if (!items.length) return null;
        return (
          <section key={t} className="tier-section">
            <header className="tier-section__head">
              <h2>
                <span className={`dot dot--lg dot--${TIER_META[t].key}`} aria-hidden="true" />
                {TIER_LABEL[t]}
                <span className="num tier-section__count">{items.length}</span>
              </h2>
              <p>{TIER_META[t].blurb}</p>
            </header>
            <div className="card-grid">
              {items.map((s, i) => (
                <motion.div
                  key={s.slug}
                  initial={{ opacity: 0, y: 14 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true, margin: "-40px" }}
                  transition={{ duration: 0.35, delay: Math.min(i, 8) * 0.04 }}
                >
                  <PlantCard s={s} nScored={scored.length} eager={i < 3} />
                </motion.div>
              ))}
            </div>
          </section>
        );
      })}

      <section className="tier-section">
        <Disclosure label="How sure is this order?">
          <p className="prose-width">
            Each plant was ranked 2,000 times, each time with the evidence shuffled a little and the three parts weighed
            differently. The dot is its usual rank; the line shows the range it landed in nine times out of ten. Where
            lines overlap, the evidence cannot tell those plants apart.
          </p>
          <div className="sheet pad">
            <Caterpillar species={scored} />
          </div>
          <p className="figure__source">
            <Link to="/how-it-works#sure">More on how sure the ranking is</Link>.{" "}
            <a href={`data:text/csv;charset=utf-8,${encodeURIComponent(csv)}`} download="harvester-risk-atlas-plants.csv">
              <Download size={14} aria-hidden="true" /> Download the full table (CSV)
            </a>
          </p>
        </Disclosure>
        <Disclosure label={`${notRanked.length} plants listed but not ranked`}>
          <p className="prose-width">
            These are kept so you can look them up and see why they are not ranked: most were brought to the
            Philippines from elsewhere.
          </p>
          <ul className="unranked">
            {notRanked.map((s) => (
              <li key={s.slug}>
                <Link to={`/species/${s.slug}`}>{s.vernacular || s.name}</Link> <i className="binomial">{s.name}</i>
                <span className="unranked__why">{gateReason(s)}</span>
              </li>
            ))}
          </ul>
        </Disclosure>
      </section>
    </div>
  );
}

function toCsv(species: SpeciesSummary[]): string {
  const head = [
    "scientific_name",
    "filipino_name",
    "family",
    "priority",
    "not_ranked_reason",
    "rank",
    "rank_low",
    "rank_high",
    "chance_top_quarter",
    "rarity",
    "harvest_harm",
    "habitat_pressure",
    "climate_exposure",
    "score",
    "denr_dao_2026_20",
    "photo_credit",
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
      TIER_LABEL[s.tier],
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
      s.photo ? `${s.photo.creator} (${s.photo.licence})` : "",
    ]
      .map(esc)
      .join(","),
  );
  return [head.join(","), ...rows].join("\n");
}
