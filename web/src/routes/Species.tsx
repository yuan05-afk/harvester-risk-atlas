import { FileText, Map as MapIcon } from "lucide-react";
import { Link, useParams } from "react-router-dom";
import { ClimateRange } from "../components/charts/ClimateRange";
import { RecordHistory, RecordHistoryTable } from "../components/charts/RecordHistory";
import { StripPlots } from "../components/charts/StripPlots";
import { ContributionBar } from "../components/ContributionBar";
import { FigureFrame } from "../components/FigureFrame";
import { HexMap } from "../components/HexMapLazy";
import { SpecimenLabel } from "../components/SpecimenLabel";
import { WithData } from "../components/Status";
import { useSpecies, useSpeciesList } from "../data/api";
import type { SpeciesDetail, SpeciesSummary } from "../data/schema";
import { explain } from "../lib/explain";
import { fmtDate, fmtInt, fmtPct, fmtScore } from "../lib/format";
import { DEFAULT_WEIGHTS } from "../lib/score";
import { COMPONENT_META, DAO_LABEL, gateReason, SCORED_COMPONENTS } from "../lib/vocab";
import { NotFound } from "./NotFound";

export function Species() {
  const { slug } = useParams();
  const detail = useSpecies(slug);
  const list = useSpeciesList();
  if (detail.status === "error" && detail.error.kind === "missing") return <NotFound what="plant" />;
  return (
    <WithData state={list}>
      {(cohort) => <WithData state={detail}>{(d) => <Profile d={d} cohort={cohort} />}</WithData>}
    </WithData>
  );
}

function Profile({ d, cohort }: { d: SpeciesDetail; cohort: SpeciesSummary[] }) {
  const nScored = cohort.filter((s) => !s.gate).length;
  const why = explain(d);
  const driver = d.driver ? COMPONENT_META[d.driver as "R" | "H" | "E"] : null;

  return (
    <div className="profile page">
      <aside className="profile__aside">
        <SpecimenLabel
          s={d}
          nScored={nScored}
          link={false}
          headingLevel={2}
          footer={
            <div className="specimen__actions">
              <Link to={`/species/${d.slug}/brief`} className="button button--primary">
                <FileText size={16} aria-hidden="true" /> Field brief
              </Link>
              <Link to={`/atlas?sp=${d.slug}`} className="button">
                <MapIcon size={16} aria-hidden="true" /> Show on atlas
              </Link>
            </div>
          }
        />
        {d.use_context ? <p className="profile__use">{d.use_context}</p> : null}
        {d.review.needed ? (
          <p className="notice">
            Awaiting expert review. {d.review.note}
          </p>
        ) : null}
      </aside>

      <div className="profile__main">
        {d.gate ? (
          <section className="sheet callout">
            <h2>{gateReason(d)}, so it is not ranked</h2>
            <p>
              {d.gate === "not_native"
                ? "The World Checklist of Vascular Plants does not list it as native to the Philippines. The atlas prioritises native plants harvested from the wild. Its records and map are shown for reference."
                : `After cleaning, its records fall in fewer than 5 grid cells (${d.n_cells}). That is too little to rank it fairly, which is not the same as being common or safe.`}
            </p>
          </section>
        ) : (
          <FigureFrame
            title="Why it ranks here"
            takeaway={
              driver
                ? `${driver.label} lifts it most above the other plants. ${d.partial ? "Part of the evidence is missing, so the score uses what is available." : ""}`
                : "No single part stands out above the other plants."
            }
            source="Score = mean of range restriction, harvest sensitivity and habitat exposure, weighted equally."
            table={<ComponentTable d={d} why={why} />}
          >
            <ContributionBar values={d.components} weights={DEFAULT_WEIGHTS} />
            <ul className="reasons">
              {SCORED_COMPONENTS.map((k) => (
                <li key={k}>
                  <span className="reasons__swatch" style={{ background: COMPONENT_META[k].color }} aria-hidden="true" />
                  <b>{COMPONENT_META[k].label}.</b> {why[k]}
                </li>
              ))}
            </ul>
            <h4 className="subhead">Against the other {nScored - 1} ranked plants</h4>
            <StripPlots species={d} cohort={cohort} />
          </FigureFrame>
        )}

        <FigureFrame
          title="Where it was recorded"
          takeaway={`${fmtInt(d.n_cells)} grid cells of about 250 km² each, from ${fmtInt(d.n_clean)} usable records. Exact locations are not shown.`}
          source="GBIF occurrence records, cleaned; protected areas from WDPCA Philippines (dashed outlines)."
          table={<ProvinceTable d={d} />}
        >
          <div className="profile__map">
            <HexMap
              mode="species"
              memberCells={d.cells}
              memberColor="var(--tier-high)"
              bounds={d.bounds}
              label={`Grid cells where ${d.name} was recorded`}
            />
          </div>
          <ul className="facts">
            <li>
              <b className="num">{fmtPct(d.pa_share)}</b> of the area of these cells is protected
            </li>
            {d.forest_loss_rate !== null ? (
              <li>
                <b className="num">{fmtPct(d.forest_loss_rate)}</b> tree cover lost 2001–2023 in its provinces
              </li>
            ) : null}
            <li>
              Recorded in <b className="num">{d.provinces.length}</b> provinces, most in{" "}
              {d.provinces
                .slice(0, 3)
                .map((p) => p.name)
                .join(", ") || "none"}
            </li>
          </ul>
        </FigureFrame>

        <FigureFrame
          title="Who recorded it, and when"
          takeaway="Old records are mostly herbarium specimens and recent ones mostly field observations, so changes in counts reflect who was looking, not how many plants there are."
          source={`All ${fmtInt(d.n_records)} GBIF records from the Philippines, before cleaning. Retrieved ${fmtDate(d.gbif.fetched_at)}.`}
          table={<RecordHistoryTable history={d.history} />}
        >
          <RecordHistory history={d.history} />
        </FigureFrame>

        <FigureFrame
          title="Climate outlook, 2041–2060"
          takeaway="Shown for context and not part of the score: the projected warming is about the same for every plant in the atlas."
          source="WorldClim 2.1 baseline and CMIP6 projections under SSP2-4.5, five climate models."
        >
          <ClimateRange species={d} cohort={cohort} />
        </FigureFrame>

        <section className="sheet evidence" aria-labelledby="evidence-title">
          <h3 id="evidence-title" className="figure__title">
            Evidence and sources
          </h3>
          <EvidenceTable d={d} />
        </section>
      </div>
    </div>
  );
}

function ComponentTable({ d, why }: { d: SpeciesDetail; why: ReturnType<typeof explain> }) {
  return (
    <table className="data-table">
      <thead>
        <tr>
          <th scope="col">Part</th>
          <th scope="col" className="num">
            Value (0–1)
          </th>
          <th scope="col">Basis</th>
        </tr>
      </thead>
      <tbody>
        {SCORED_COMPONENTS.map((k) => (
          <tr key={k}>
            <th scope="row">{COMPONENT_META[k].label}</th>
            <td className="num">{fmtScore(d.components[k])}</td>
            <td>{why[k]}</td>
          </tr>
        ))}
        <tr>
          <th scope="row">Score</th>
          <td className="num">{fmtScore(d.score)}</td>
          <td>
            90% range {fmtScore(d.score_ci[0])} to {fmtScore(d.score_ci[1])}
          </td>
        </tr>
      </tbody>
    </table>
  );
}

function ProvinceTable({ d }: { d: SpeciesDetail }) {
  return (
    <table className="data-table">
      <thead>
        <tr>
          <th scope="col">Province</th>
          <th scope="col" className="num">
            Usable records
          </th>
        </tr>
      </thead>
      <tbody>
        {d.provinces.map((p) => (
          <tr key={p.name}>
            <th scope="row">{p.name}</th>
            <td className="num">{p.records}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function EvidenceTable({ d }: { d: SpeciesDetail }) {
  const dropped = (d.cleaning.n_fetched ?? 0) - (d.cleaning.n_kept ?? 0);
  const rows: [string, string, string][] = [
    [
      "Occurrence records",
      `${fmtInt(d.n_records)} in the Philippines; ${fmtInt(d.cleaning.n_kept)} kept after cleaning, ${fmtInt(dropped)} dropped (mostly duplicates and imprecise coordinates)`,
      `GBIF, retrieved ${fmtDate(d.gbif.fetched_at)}`,
    ],
    [
      "Native status",
      d.ph_status === "native" ? (d.endemic ? "Native; endemic" : "Native") : d.ph_status.replace("_", " "),
      `World Checklist of Vascular Plants, retrieved ${fmtDate(d.wcvp.fetched_at)}`,
    ],
    [
      "How it is harvested",
      d.traits ? `${d.traits.parts_used}; ${d.traits.habitat_note}` : "No cited source yet",
      d.traits ? `${d.traits.source}${d.traits.verified ? "" : ", awaiting expert check"}` : "—",
    ],
    ["Protected areas", `${fmtPct(d.pa_share)} of occupied cell area`, "WDPCA Philippines (UNEP-WCMC)"],
    [
      "Forest loss",
      d.forest_loss_rate === null ? "—" : `${fmtPct(d.forest_loss_rate)} of 2000 tree cover lost by 2023`,
      "Hansen et al. 2013, Global Forest Watch",
    ],
    ["National threatened list", d.dao ? DAO_LABEL[d.dao] ?? d.dao : "Not listed", "DENR DAO 2026-20"],
    ["IUCN Red List", "Not retrieved in this build; no category is shown or guessed", "IUCN Red List API"],
  ];
  return (
    <table className="data-table data-table--evidence">
      <thead>
        <tr>
          <th scope="col">Input</th>
          <th scope="col">Value</th>
          <th scope="col">Source</th>
        </tr>
      </thead>
      <tbody>
        {rows.map(([a, b, c]) => (
          <tr key={a}>
            <th scope="row">{a}</th>
            <td>{b}</td>
            <td className="evidence__source">
              {a === "How it is harvested" && d.traits ? (
                <a href={d.traits.source_url} target="_blank" rel="noreferrer">
                  {c}
                </a>
              ) : (
                c
              )}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
