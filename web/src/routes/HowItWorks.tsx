import * as Slider from "@radix-ui/react-slider";
import { ArrowDown, ArrowUp, Minus } from "lucide-react";
import { motion } from "motion/react";
import { useMemo, type ReactNode } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { AgreementScale, IntervalGlyph, RankStrip } from "../components/charts/CheckFigures";
import { VerdictMark } from "../components/Figures";
import { PlantPhoto } from "../components/PlantPhoto";
import { WithData } from "../components/Status";
import { useManifest, useSpeciesList, useValidation } from "../data/api";
import type { Component, SpeciesSummary, Validation } from "../data/schema";
import { fmtDate, fmtInt } from "../lib/format";
import { aggregate, DEFAULT_WEIGHTS, KEYS, normalize, ranks, weightsFromParam, weightsToParam, type Weights } from "../lib/score";
import { COMPONENT_META, SCORED_COMPONENTS, TIER_LABEL } from "../lib/vocab";
import { Disclosure } from "./Species";

const rise = {
  initial: { opacity: 0, y: 16 },
  whileInView: { opacity: 1, y: 0 },
  viewport: { once: true, margin: "-60px" },
  transition: { duration: 0.45 },
};

export function HowItWorks() {
  const list = useSpeciesList();
  const validation = useValidation();
  const manifest = useManifest();
  return (
    <div className="page how">
      <header className="page__head">
        <h1>How the atlas decides</h1>
        <p className="lede">
          Five steps turn public records into a ranked list. Each step is simple; the care is in saying how sure we are.
        </p>
      </header>

      <WithData state={list} reserve="100vh">
        {(species) => {
          const nRecords = species.reduce((a, s) => a + s.n_records, 0);
          const nClean = species.reduce((a, s) => a + s.n_clean, 0);
          const nScored = species.filter((s) => !s.gate).length;
          const steps = [
            {
              title: "Collect the records",
              text: `${fmtInt(nRecords)} records of ${species.length} medicinal plants in the Philippines, from museums, herbaria and citizen scientists, via GBIF.`,
              more: "Each plant's name is matched to the GBIF backbone so synonyms count once. Native status comes from Kew's World Checklist of Vascular Plants.",
            },
            {
              title: "Check them",
              text: `${fmtInt(nClean)} records pass: duplicates, vague locations, garden plants and points at sea are set aside.`,
              more: "Every record set aside keeps its reason (for example duplicate, imprecise, cultivated). Locations are then grouped into hexagonal areas of about 250 km², so no exact spot is ever shown.",
            },
            {
              title: "Judge three things",
              text: "Rarity, harvest harm and habitat pressure, each from 0 to 1 on a fixed scale.",
              more: "Rarity is measured where botanists have actually looked, so a common weed with many photos does not look rare by accident. Harvest harm comes from published descriptions of which part is harvested. Habitat pressure combines protected-area cover and forest loss. Climate change is reported but not counted.",
            },
            {
              title: "Test it 2,000 times",
              text: "The ranking is redone with the weights and evidence shuffled a little each time.",
              more: "This shows how much each rank could move if the evidence were slightly different, or if someone weighed the three parts differently.",
            },
            {
              title: "Sort into groups",
              text: `${nScored} native plants land in three groups, by how often they came out in the top quarter.`,
              more: `${TIER_LABEL["High attention"]}: at least 8 times in 10. ${TIER_LABEL.Watch}: 3 to 8 times in 10. ${TIER_LABEL.Lower}: less often. Plants that are not native, or have too few records, are listed but not ranked.`,
            },
          ];
          return (
            <>
              <ol className="steps">
                {steps.map((s, i) => (
                  <motion.li key={s.title} className="step" {...rise} transition={{ ...rise.transition, delay: i * 0.06 }}>
                    <span className="step__num num" aria-hidden="true">
                      {i + 1}
                    </span>
                    <h2>{s.title}</h2>
                    <p>{s.text}</p>
                    <details className="step__more">
                      <summary>More detail</summary>
                      <p>{s.more}</p>
                    </details>
                  </motion.li>
                ))}
              </ol>

              <section className="how-section" id="explorer">
                <header>
                  <h2>What if you weighed things differently?</h2>
                  <p>
                    The atlas counts the three parts equally. If you care more about one of them, try it here. The
                    published ranking stays the same.
                  </p>
                </header>
                <WeightExplorer species={species} />
              </section>
            </>
          );
        }}
      </WithData>

      <section className="how-section" id="sure">
        <header>
          <h2>How sure is the ranking?</h2>
          <p>There is no official count of how much of each plant is harvested, so we tested the ranking in other ways.</p>
        </header>
        <WithData state={validation}>{(v) => <Checks v={v} />}</WithData>
      </section>

      <section className="how-section">
        <header>
          <h2>What changed from the first version</h2>
          <p>
            The first version, built in September 2026, scored plants on how many records it fetched, which was the
            same for nearly every plant, and on how old the records were. It mostly measured how plants had been
            recorded, not how they were doing. A plant with no records at all came first. This version replaces those
            measures, and shows its uncertainty.
          </p>
        </header>
      </section>

      <section className="how-section" id="sources">
        <header>
          <h2>Sources and licences</h2>
        </header>
        <WithData state={manifest}>
          {(m) => (
            <Disclosure label={`${m.sources.length} data sources`}>
              <div className="table-wrap">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th scope="col">Source</th>
                      <th scope="col">Used for</th>
                      <th scope="col">Licence</th>
                    </tr>
                  </thead>
                  <tbody>
                    {m.sources.map((s) => (
                      <tr key={s.id}>
                        <th scope="row">
                          <a href={s.url} target="_blank" rel="noreferrer">
                            {s.name}
                          </a>
                          {s.accessed ? <span className="cell-sub">Retrieved {fmtDate(s.accessed)}</span> : null}
                        </th>
                        <td>{s.use}</td>
                        <td>{s.licence}</td>
                      </tr>
                    ))}
                    <tr>
                      <th scope="row">
                        <a href="https://www.inaturalist.org/" target="_blank" rel="noreferrer">
                          iNaturalist research-grade photos, via GBIF
                        </a>
                      </th>
                      <td>plant photos</td>
                      <td>CC0, CC BY 4.0 or CC BY-NC 4.0; credited on each plant</td>
                    </tr>
                  </tbody>
                </table>
              </div>
              <p className="figure__source">
                {m.index} version {m.version}, built {fmtDate(m.built_at)} from code version {m.git_sha}. The full
                technical write-up is docs/METHODS.md in the project repository.
              </p>
            </Disclosure>
          )}
        </WithData>
      </section>

      <section className="how-section" id="built">
        <header>
          <h2>What was built when</h2>
          <p>
            EthnoHack 2026 (2 to 8 November 2026) asks teams to say what existed before the hackathon. The first version
            of this atlas was built from 29 September to 1 October 2026; this version, including this site, from 14
            October 2026. Both came before the hackathon. Work done during it is logged separately in
            docs/ORIGINALITY.md, which also lists the AI tools used.
          </p>
        </header>
        <p>
          <Link to="/plants">Back to the plants</Link>
        </p>
      </section>
    </div>
  );
}

const PRESETS: { label: string; w: Weights }[] = [
  { label: "Equal (published)", w: { R: 1, H: 1, E: 1, C: 0 } },
  { label: "Rarity first", w: { R: 3, H: 1, E: 1, C: 0 } },
  { label: "Harvest first", w: { R: 1, H: 3, E: 1, C: 0 } },
  { label: "Habitat first", w: { R: 1, H: 1, E: 3, C: 0 } },
  { label: "Add climate", w: { R: 1, H: 1, E: 1, C: 1 } },
];

function WeightExplorer({ species }: { species: SpeciesSummary[] }) {
  // The sliders live in the URL (?w=R,H,E,C) so a particular ranking can be shared.
  const [params, setParams] = useSearchParams();
  const raw = useMemo(() => weightsFromParam(params.get("w")), [params]);
  const setRaw = (next: Weights | ((r: Weights) => Weights)) => {
    const w = typeof next === "function" ? next(raw) : next;
    const p = new URLSearchParams(params);
    const v = weightsToParam(w);
    if (v === null) p.delete("w");
    else p.set("w", v);
    setParams(p, { replace: true, preventScrollReset: true });
  };
  const weights = normalize(raw);
  const scored = useMemo(() => species.filter((s) => !s.gate), [species]);
  const base = useMemo(() => {
    const r = ranks(scored.map((s) => aggregate(s.components, DEFAULT_WEIGHTS)));
    return new Map(scored.map((s, i) => [s.slug, r[i] ?? 0]));
  }, [scored]);
  const alt = useMemo(() => {
    const r = ranks(scored.map((s) => aggregate(s.components, weights)));
    return scored.map((s, i) => ({ s, rank: r[i] ?? 0 })).sort((a, b) => a.rank - b.rank || a.s.name.localeCompare(b.s.name));
  }, [scored, weights]);
  const active = PRESETS.find((p) => KEYS.every((k) => Math.abs(normalize(p.w)[k] - weights[k]) < 1e-9));

  return (
    <div className="explorer">
      <div className="explorer__controls sheet">
        <div className="segmented-pills segmented-pills--wrap" role="group" aria-label="Quick choices">
          {PRESETS.map((p) => (
            <button key={p.label} type="button" aria-pressed={active === p} className={active === p ? "is-on" : ""} onClick={() => setRaw(p.w)}>
              {p.label}
            </button>
          ))}
        </div>
        {[...SCORED_COMPONENTS, "C" as Component].map((k) => (
          <div key={k} className="explorer__slider">
            <label id={`w-${k}`} className="explorer__label">
              <span className="swatch" style={{ background: COMPONENT_META[k].color }} aria-hidden="true" />
              {COMPONENT_META[k].label}
              <span className="num explorer__share">{Math.round(weights[k] * 100)}%</span>
            </label>
            <Slider.Root
              className="slider"
              min={0}
              max={4}
              step={0.25}
              value={[raw[k]]}
              onValueChange={([v]) => setRaw((r) => ({ ...r, [k]: v }))}
              aria-labelledby={`w-${k}`}
            >
              <Slider.Track className="slider__track">
                <Slider.Range className="slider__range" />
              </Slider.Track>
              <Slider.Thumb className="slider__thumb" aria-labelledby={`w-${k}`} />
            </Slider.Root>
          </div>
        ))}
      </div>
      <div className="explorer__result sheet">
        <h3>Top 8 with these weights</h3>
        <ol className="movers" aria-live="polite">
          {alt.slice(0, 8).map(({ s, rank }) => {
            const was = base.get(s.slug) ?? rank;
            const delta = was - rank;
            return (
              <motion.li key={s.slug} layout transition={{ type: "spring", stiffness: 500, damping: 38 }}>
                <span className="movers__rank num">{rank}</span>
                <PlantPhoto s={s} ratio="1 / 1" credit="none" className="movers__thumb" decorative />
                <span className="movers__names">
                  <span>{s.vernacular || s.name}</span>
                  <i className="binomial">{s.name}</i>
                </span>
                <span className={`movers__delta ${delta > 0 ? "up" : delta < 0 ? "down" : ""}`}>
                  {delta > 0 ? (
                    <>
                      <ArrowUp size={14} aria-hidden="true" /> {delta}
                    </>
                  ) : delta < 0 ? (
                    <>
                      <ArrowDown size={14} aria-hidden="true" /> {-delta}
                    </>
                  ) : (
                    <>
                      <Minus size={14} aria-hidden="true" /> same
                    </>
                  )}
                  <span className="sr-only">{delta === 0 ? "" : delta > 0 ? " places up" : " places down"}</span>
                </span>
              </motion.li>
            );
          })}
        </ol>
        <p className="figure__source">Arrows compare with the published equal-weight order.</p>
      </div>
    </div>
  );
}

function Checks({ v }: { v: Validation }) {
  const f = (x: number | null | undefined) => (x ?? 0).toFixed(2);
  const gm = v.aggregation.geometric_mean ?? 0;
  const rm = v.aggregation.mean_component_rank ?? 0;
  const effort = Math.min(...Object.values(v.effort_threshold).map((x) => x ?? 1));
  const listed = (v.dao.listed ?? []).map((l) => l.rank_median).filter((r): r is number => r !== null);
  const listedMean = listed.reduce((a, b) => a + b, 0) / Math.max(1, listed.length);
  const rows: { kind: "ok" | "limit" | "weak"; verdict: string; title: string; text: string; fig: ReactNode }[] = [
    {
      kind: "ok",
      verdict: "Holds up",
      title: "Combine the three parts another way",
      text: `Two other ways of averaging give much the same order: agreement ${f(gm)} and ${f(rm)}, where 1 means identical.`,
      fig: (
        <AgreementScale
          marks={[
            { value: gm, label: "geometric mean" },
            { value: rm, label: "average of ranks" },
          ]}
        />
      ),
    },
    {
      kind: "ok",
      verdict: "Holds up",
      title: "Change what counts as well searched",
      text: `Halving or doubling the bar for a well-searched area barely moves anything: agreement ${f(effort)} or better.`,
      fig: <AgreementScale marks={[{ value: effort, label: "half or double the bar" }]} />,
    },
    {
      kind: "limit",
      verdict: "Known limit",
      title: "Rarity carries the most weight",
      text: `Leaving rarity out changes the order most (${f(v.drop_component.without_R)}), more than harvest harm (${f(v.drop_component.without_H)}) or habitat (${f(v.drop_component.without_E)}). It is also the part best backed by data.`,
      fig: (
        <AgreementScale
          marks={(["R", "H", "E"] as const).map((k) => ({
            value: v.drop_component[`without_${k}`] ?? 0,
            label: `without ${COMPONENT_META[k].short.toLowerCase()}`,
            color: COMPONENT_META[k].color,
          }))}
        />
      ),
    },
    {
      kind: "weak",
      verdict: "Weak signal",
      title: "Compare with the national threatened list",
      text: `The ${v.dao.n_listed} ranked plants on DENR's 2026 list rank ${Math.round(listedMean)}th on average, higher than the ${Math.round((v.n_scored + 1) / 2)}th that chance would give. Four plants are too few to prove much.`,
      fig: <RankStrip ranks={listed} n={v.n_scored} />,
    },
  ];
  return (
    <>
      <ol className="ledger">
        {rows.map((r, i) => (
          <motion.li key={r.title} className={`ledger__row ledger__row--${r.kind}`} {...rise} transition={{ ...rise.transition, delay: i * 0.06 }}>
            <p className="ledger__verdict">
              <VerdictMark kind={r.kind} />
              <span>{r.verdict}</span>
            </p>
            <div className="ledger__text">
              <h3>{r.title}</h3>
              <p>{r.text}</p>
            </div>
            <div className="ledger__fig">{r.fig}</div>
          </motion.li>
        ))}
      </ol>
      <motion.div className="ledger-summary" {...rise}>
        <div>
          <h3>Typical uncertainty</h3>
          <p>
            A plant's rank is usually known to within about <b className="num">{v.interval_width_median}</b> places. The{" "}
            <Link to="/plants">plants page</Link> shows each one's range.
          </p>
        </div>
        {v.interval_width_median !== null ? <IntervalGlyph width={v.interval_width_median} n={v.n_scored} /> : null}
      </motion.div>
    </>
  );
}
