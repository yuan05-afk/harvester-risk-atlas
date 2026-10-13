import * as Slider from "@radix-ui/react-slider";
import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { Caterpillar } from "../components/charts/Caterpillar";
import { WithData } from "../components/Status";
import { useManifest, useSpeciesList, useValidation } from "../data/api";
import type { Component, SpeciesSummary, Validation } from "../data/schema";
import { fmtDate } from "../lib/format";
import { aggregate, DEFAULT_WEIGHTS, KEYS, normalize, ranks, type Weights } from "../lib/score";
import { COMPONENT_META } from "../lib/vocab";

export function Methods() {
  const list = useSpeciesList();
  const validation = useValidation();
  const manifest = useManifest();
  return (
    <div className="page methods">
      <header className="page__head">
        <h1>Methods and evidence</h1>
        <p className="lede">
          How the Harvest Priority Index is built, how sure it is, and where every number comes from. The full technical
          write-up is in the project repository (docs/METHODS.md).
        </p>
        <nav className="toc" aria-label="On this page">
          <a href="#components">Scoring</a>
          <a href="#uncertainty">Uncertainty and tiers</a>
          <a href="#explorer">Try other weights</a>
          <a href="#validation">Checks</a>
          <a href="#limits">Limits</a>
          <a href="#data">Data and licences</a>
          <a href="#originality">What was built when</a>
        </nav>
      </header>

      <section id="components" className="prose">
        <h2>Scoring</h2>
        <p>
          The atlas cannot measure harvest pressure directly: no dataset records how much of each plant is taken. It
          scores what can be measured and says so. Each part runs from 0 to 1 on a fixed scale, so adding a plant never
          changes another plant's values.
        </p>
        <dl className="defs">
          {(["R", "H", "E", "C"] as Component[]).map((k) => (
            <div key={k}>
              <dt>
                <span className="parts__swatch" style={{ background: COMPONENT_META[k].color }} aria-hidden="true" />
                {COMPONENT_META[k].label}
              </dt>
              <dd>{DEFINITIONS[k]}</dd>
            </div>
          ))}
        </dl>
        <p>
          A plant is listed but not ranked if the World Checklist of Vascular Plants does not record it as native to
          the Philippines, or if its cleaned records fall in fewer than 5 grid cells.
        </p>
      </section>

      <section id="uncertainty" className="prose">
        <h2>Uncertainty and tiers</h2>
        <p>
          Each plant is scored 2,000 times. Every run draws new weights around the equal defaults and resamples the
          evidence: how often the plant turns up in well-surveyed cells, and which of its cells count toward protected
          area and forest loss. The atlas reports the median rank, the range that holds 90% of runs, and the share of
          runs that put the plant in the top quarter.
        </p>
        <ul>
          <li>
            <b>High attention</b>: in the top quarter in at least 80% of runs.
          </li>
          <li>
            <b>Watch</b>: 30–80% of runs.
          </li>
          <li>
            <b>Lower</b>: fewer than 30% of runs.
          </li>
        </ul>
      </section>

      <section id="explorer">
        <h2>Try other weights</h2>
        <p className="prose-width">
          Disagree with equal weights? Set your own. The published ranking does not change; this shows how much your
          choice would move each plant. The diamond marks a plant's rank under your weights.
        </p>
        <WithData state={list}>{(species) => <WeightExplorer species={species} />}</WithData>
      </section>

      <section id="validation">
        <h2>Checks</h2>
        <p className="prose-width">
          There is no ground truth for harvest priority, so these checks test robustness and plausibility, not accuracy.
        </p>
        <WithData state={validation}>{(v) => <ValidationTable v={v} />}</WithData>
      </section>

      <section id="limits" className="prose">
        <h2>Limits</h2>
        <ul>
          <li>GBIF records show where plants were recorded, not where they are absent. Survey effort is corrected for only as far as the record layer captures it.</li>
          <li>Harvest sensitivity comes from a literature rubric (plant part, life form, sourcing), not from field data on harvest volumes or trade.</li>
          <li>Native status follows the World Checklist of Vascular Plants. Some of its calls will surprise readers; lagundi, for example, is listed as introduced.</li>
          <li>Forest loss is summarised by province, not at each record.</li>
          <li>Red List categories are not retrieved in this build, and none are shown or guessed.</li>
        </ul>
      </section>

      <section id="data">
        <h2>Data and licences</h2>
        <WithData state={manifest}>
          {(m) => (
            <>
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
                </tbody>
              </table>
              <p className="figure__source">
                {m.index} v{m.version}, built {fmtDate(m.built_at)} from commit {m.git_sha}.
              </p>
            </>
          )}
        </WithData>
      </section>

      <section id="originality" className="prose">
        <h2>What was built when</h2>
        <p>
          EthnoHack 2026 asks teams to say which parts existed before the hackathon (2–8 November 2026). The first version
          of this atlas was built from 29 September to 1 October 2026. Version 2, including this site and the index it
          shows, was rebuilt from 14 October 2026, also before the hackathon. Work done during the hackathon is logged
          separately. The full record, including AI tools used, is in docs/ORIGINALITY.md in the repository.
        </p>
        <p>
          <Link to="/rankings">Back to the rankings</Link>
        </p>
      </section>
    </div>
  );
}

const DEFINITIONS: Record<Component, string> = {
  R: "How often the plant was recorded in grid cells where botanists have recorded at least 100 plants (the reporting rate), together with how many regions of the world it is native to. Rarely recorded, narrowly distributed plants score high.",
  H: "Whether harvesting takes roots, rhizomes, bark or the whole plant; whether the plant is slow to regrow (trees, palms, woody climbers); and whether supply comes only from the wild. Drawn from Stuart's Philippine Medicinal Plants, with each entry cited.",
  E: "The share of the plant's cells that lie outside protected areas, and tree-cover loss from 2001 to 2023 in the provinces where it was recorded, counted fully for forest plants, half for thicket plants and not at all for open-ground plants.",
  C: "Projected warming at the plant's cells for 2041–2060 under SSP2-4.5, across five climate models. It is about +1.5 °C for every plant, so it is reported but carries no weight by default.",
};

function WeightExplorer({ species }: { species: SpeciesSummary[] }) {
  const [raw, setRaw] = useState<Weights>({ R: 1, H: 1, E: 1, C: 0 });
  const weights = normalize(raw);
  const scored = species.filter((s) => !s.gate);
  const alt = useMemo(() => {
    const scores = scored.map((s) => aggregate(s.components, weights));
    const r = ranks(scores);
    return new Map(scored.map((s, i) => [s.slug, r[i] ?? 0]));
  }, [scored, weights]);
  const isDefault = KEYS.every((k) => Math.abs(weights[k] - DEFAULT_WEIGHTS[k]) < 1e-9);
  const outside = scored.filter((s) => {
    const a = alt.get(s.slug)!;
    return a < (s.rank_ci[0] ?? 0) || a > (s.rank_ci[1] ?? 0);
  });

  return (
    <div className="explorer">
      <div className="explorer__controls sheet">
        {KEYS.map((k) => (
          <div key={k} className="explorer__slider">
            <label id={`w-${k}`} className="explorer__label">
              <span className="parts__swatch" style={{ background: COMPONENT_META[k].color }} aria-hidden="true" />
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
        <div className="explorer__summary" aria-live="polite">
          {isDefault ? (
            <p>These are the published weights.</p>
          ) : (
            <p>
              Under your weights, <b className="num">{outside.length}</b> of {scored.length} plants move outside their
              published 90% interval.
            </p>
          )}
          <button type="button" className="button button--small" onClick={() => setRaw({ R: 1, H: 1, E: 1, C: 0 })} disabled={isDefault}>
            Reset to equal weights
          </button>
        </div>
      </div>
      <div className="sheet">
        <Caterpillar species={scored} rankOverride={isDefault ? undefined : alt} />
      </div>
    </div>
  );
}

function ValidationTable({ v }: { v: Validation }) {
  const rows: [string, string, string][] = [
    [
      "Another way to combine the parts",
      `Agreement ${v.aggregation.geometric_mean?.toFixed(2)} (geometric mean), ${v.aggregation.mean_component_rank?.toFixed(2)} (mean of part ranks)`,
      "Ranks hardly depend on the averaging method.",
    ],
    [
      "Leave one part out",
      `Agreement ${v.drop_component.without_R?.toFixed(2)} without range, ${v.drop_component.without_H?.toFixed(2)} without harvest, ${v.drop_component.without_E?.toFixed(2)} without habitat`,
      "Range restriction moves the ranking most.",
    ],
    [
      "Change what counts as well surveyed",
      `Agreement ${v.effort_threshold.well_surveyed_50?.toFixed(3)} at 50 records, ${v.effort_threshold.well_surveyed_200?.toFixed(3)} at 200`,
      "The effort threshold barely matters.",
    ],
    [
      "National threatened list (DENR DAO 2026-20)",
      `${v.dao.n_listed} listed plants ranked; mean rank ${v.dao.mean_rank_listed?.toFixed(1)} against ${v.dao.mean_rank_all?.toFixed(1)} by chance (p = ${v.dao.p_value?.toFixed(3)})`,
      "A weak, directional signal from very few plants.",
    ],
    [
      "Compared with version 1",
      `Agreement ${v.v1_vs_v2.spearman?.toFixed(2)} across ${v.v1_vs_v2.n_shared} shared plants`,
      "Version 2 is a different ranking. Version 1 mostly measured how records were collected.",
    ],
  ];
  return (
    <div className="table-wrap">
      <table className="data-table">
        <thead>
          <tr>
            <th scope="col">Check</th>
            <th scope="col">Result</th>
            <th scope="col">What it means</th>
          </tr>
        </thead>
        <tbody>
          {rows.map(([a, b, c]) => (
            <tr key={a}>
              <th scope="row">{a}</th>
              <td>{b}</td>
              <td>{c}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <p className="figure__source">Agreement is Spearman rank correlation with the published ranking: 1 means identical order.</p>
    </div>
  );
}
