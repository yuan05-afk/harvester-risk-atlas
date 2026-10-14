import { ArrowLeft, ArrowRight, ChevronDown, FileText, Map as MapIcon, ShieldQuestion } from "lucide-react";
import { motion } from "motion/react";
import { useMemo, useState, type ReactNode } from "react";
import { Link, useParams } from "react-router-dom";
import { ClimateRange } from "../components/charts/ClimateRange";
import { RecordHistory, RecordHistoryTable } from "../components/charts/RecordHistory";
import { StripPlots } from "../components/charts/StripPlots";
import type { CellSet, HoverInfo } from "../components/HexMap";
import { HexMap } from "../components/HexMapLazy";
import { MapTooltip } from "../components/MapTooltip";
import { PlantPhoto } from "../components/PlantPhoto";
import { ReasonTiles } from "../components/Reasons";
import { Stamp } from "../components/Stamp";
import { WithData } from "../components/Status";
import { useSpecies, useSpeciesList } from "../data/api";
import type { SpeciesDetail, SpeciesSummary } from "../data/schema";
import { explain, summary } from "../lib/explain";
import { fmtDate, fmtInt, fmtPct, fmtScore } from "../lib/format";
import { useWidth } from "../lib/useWidth";
import { COMPONENT_META, DAO_LABEL, gateReason, nativeLabel, rankSentence, SCORED_COMPONENTS } from "../lib/vocab";
import { NotFound } from "./NotFound";

export function Species() {
  const { slug } = useParams();
  const detail = useSpecies(slug);
  const list = useSpeciesList();
  if (detail.status === "error" && detail.error.kind === "missing") return <NotFound what="plant" />;
  return (
    <WithData state={list}>
      {(cohort) => <WithData state={detail}>{(d) => <Profile key={d.slug} d={d} cohort={cohort} />}</WithData>}
    </WithData>
  );
}

const rise = {
  initial: { opacity: 0, y: 16 },
  whileInView: { opacity: 1, y: 0 },
  viewport: { once: true, margin: "-60px" },
  transition: { duration: 0.45, ease: [0.2, 0.7, 0.2, 1] as const },
};

function Profile({ d, cohort }: { d: SpeciesDetail; cohort: SpeciesSummary[] }) {
  const scored = cohort.filter((s) => !s.gate).sort((a, b) => (a.rank ?? 0) - (b.rank ?? 0) || a.name.localeCompare(b.name));
  const nScored = scored.length;
  const why = explain(d);
  const bySlug = useMemo(() => new Map(cohort.map((s) => [s.slug, s])), [cohort]);
  const idx = scored.findIndex((s) => s.slug === d.slug);
  const prev = idx > 0 ? scored[idx - 1] : null;
  const next = idx >= 0 && idx < scored.length - 1 ? scored[idx + 1] : null;
  const member: CellSet = useMemo(() => ({ fine: d.cells, coarse: d.cells_r4 }), [d]);
  const [hover, setHover] = useState<HoverInfo>(null);
  const [mapRef, mapW] = useWidth<HTMLDivElement>(700);
  const title = d.vernacular ? d.vernacular.split(" / ")[0] : d.name;

  return (
    <article className="profile">
      <nav className="crumbs" aria-label="Breadcrumb">
        <Link to="/plants">Plants</Link>
        <span aria-hidden="true">/</span>
        <span aria-current="page">{title}</span>
      </nav>

      <header className="profile-hero">
        <motion.div className="profile-hero__media" initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}>
          <PlantPhoto s={d} ratio="4 / 3" credit="below" eager />
          <Stamp tier={d.tier} rank={d.rank} of={d.rank !== null ? nScored : undefined} size={120} className="profile-hero__stamp" />
        </motion.div>
        <motion.div className="profile-hero__text" initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.08 }}>
          <p className="profile-hero__kicker">
            {d.family} family. {nativeLabel(d)}.
          </p>
          <h1 className="profile-hero__name">
            {d.vernacular ? <span className="profile-hero__vern">{d.vernacular}</span> : null}
            <i className="binomial profile-hero__sci">{d.name}</i>
          </h1>
          <p className="profile-hero__summary">{summary(d, nScored)}</p>
          {d.rank !== null ? <p className="profile-hero__rank">{rankSentence(d, nScored)}</p> : null}
          <ul className="tags">
            {d.endemic ? <li>Grows only in the Philippines</li> : null}
            {d.dao ? <li>DENR list: {DAO_LABEL[d.dao] ?? d.dao}</li> : null}
            {d.use_context ? <li className="tags__use">{d.use_context.replace(/\s*—.*$/, "")}</li> : null}
          </ul>
          <div className="actions">
            <Link to={`/species/${d.slug}/brief`} className="button button--primary">
              <FileText size={18} aria-hidden="true" /> Field brief
            </Link>
            <Link to={`/atlas?sp=${d.slug}`} className="button">
              <MapIcon size={18} aria-hidden="true" /> Show on the atlas
            </Link>
          </div>
          {d.review.needed ? (
            <p className="review-note">
              <ShieldQuestion size={16} aria-hidden="true" /> Awaiting expert review. Its place on the list, or the
              facts behind it, may still change.
            </p>
          ) : null}
        </motion.div>
      </header>

      <Section title="Why it ranks here" lead={d.gate ? undefined : "Three things decide a plant's place. The bigger the bar, the more that part pushes it up the list."}>
        {d.gate ? (
          <div className="notice-sheet">
            <ShieldQuestion size={28} aria-hidden="true" />
            <div>
              <h3>{gateReason(d)}, so it is not ranked</h3>
              <p>
                {d.gate === "not_native"
                  ? "The World Checklist of Vascular Plants does not list it as native to the Philippines. The atlas ranks native plants gathered from the wild. Its records and map are kept for reference."
                  : `After checking, its reliable records fall in fewer than 5 areas (${d.n_cells}). That is too little to rank it fairly, and it does not mean the plant is common or safe.`}
              </p>
            </div>
          </div>
        ) : (
          <>
            <ReasonTiles values={d.components} sentences={why} highlight={d.driver || undefined} />
            <Disclosure label={`Compare with the other ${nScored - 1} ranked plants`}>
              <StripPlots species={d} cohort={cohort} />
            </Disclosure>
            <Disclosure label="Show the numbers">
              <ComponentTable d={d} />
            </Disclosure>
          </>
        )}
      </Section>

      <Section title="Where it grows" lead={`Recorded in ${fmtInt(d.n_cells)} areas from ${fmtInt(d.n_clean)} reliable records. Exact spots are never shown.`}>
        <div className="where">
          <div className="where__map" ref={mapRef}>
            <HexMap
              mode="species"
              member={member}
              bounds={d.bounds}
              onHover={setHover}
              label={`Map of the areas where ${title} was recorded`}
            />
            <MapTooltip info={hover} bySlug={bySlug} mode="species" width={mapW} height={460} />
          </div>
          <dl className="where__facts">
            <div>
              <dt>Protected</dt>
              <dd>
                <b className="num">{fmtPct(d.pa_share)}</b> of the area where it grows
              </dd>
            </div>
            {d.forest_loss_rate !== null && d.habitat !== "open" ? (
              <div>
                <dt>Forest lost</dt>
                <dd>
                  <b className="num">{fmtPct(d.forest_loss_rate)}</b> in its provinces, 2001 to 2023
                </dd>
              </div>
            ) : null}
            <div>
              <dt>Provinces</dt>
              <dd>
                <ul className="chips">
                  {d.provinces.slice(0, 10).map((p) => (
                    <li key={p.name}>{p.name}</li>
                  ))}
                  {d.provinces.length > 10 ? <li className="chips__more">+{d.provinces.length - 10} more</li> : null}
                </ul>
              </dd>
            </div>
          </dl>
        </div>
      </Section>

      <Section
        title="Who has recorded it, and when"
        lead="Old records are mostly pressed specimens in herbaria; recent ones are mostly photos from the field. A change in numbers shows who was looking, not how many plants there are."
      >
        <div className="sheet pad">
          <RecordHistory history={d.history} />
          <Disclosure label="Show as a table">
            <RecordHistoryTable history={d.history} />
          </Disclosure>
        </div>
      </Section>

      <Section title="Climate outlook" lead="Expected warming where it grows by 2041 to 2060. Shown for context only: it is about the same for every plant, so it does not change the ranking.">
        <div className="sheet pad">
          <ClimateRange species={d} cohort={cohort} />
        </div>
      </Section>

      <Section title="Sources">
        <Disclosure label="Every input, with where it comes from">
          <EvidenceTable d={d} />
        </Disclosure>
      </Section>

      <nav className="pager" aria-label="Other plants">
        {prev ? (
          <Link to={`/species/${prev.slug}`} className="pager__link">
            <ArrowLeft size={18} aria-hidden="true" />
            <span>
              <small>Ranked higher</small>
              {prev.vernacular || prev.name}
            </span>
          </Link>
        ) : (
          <span />
        )}
        {next ? (
          <Link to={`/species/${next.slug}`} className="pager__link pager__link--next">
            <span>
              <small>Ranked lower</small>
              {next.vernacular || next.name}
            </span>
            <ArrowRight size={18} aria-hidden="true" />
          </Link>
        ) : null}
      </nav>
    </article>
  );
}

function Section({ title, lead, children }: { title: string; lead?: string; children: ReactNode }) {
  return (
    <motion.section className="profile-section" {...rise}>
      <header className="profile-section__head">
        <h2>{title}</h2>
        {lead ? <p>{lead}</p> : null}
      </header>
      {children}
    </motion.section>
  );
}

export function Disclosure({ label, children }: { label: string; children: ReactNode }) {
  return (
    <details className="disclosure">
      <summary>
        <ChevronDown size={16} aria-hidden="true" />
        {label}
      </summary>
      <div className="disclosure__body">{children}</div>
    </details>
  );
}

function ComponentTable({ d }: { d: SpeciesDetail }) {
  return (
    <div className="table-wrap">
      <table className="data-table">
        <thead>
          <tr>
            <th scope="col">Part</th>
            <th scope="col" className="num">
              Value, 0 to 1
            </th>
          </tr>
        </thead>
        <tbody>
          {SCORED_COMPONENTS.map((k) => (
            <tr key={k}>
              <th scope="row">{COMPONENT_META[k].label}</th>
              <td className="num">{fmtScore(d.components[k])}</td>
            </tr>
          ))}
          <tr>
            <th scope="row">Score (equal weights)</th>
            <td className="num">
              {fmtScore(d.score)} <span className="cell-sub">likely between {fmtScore(d.score_ci[0])} and {fmtScore(d.score_ci[1])}</span>
            </td>
          </tr>
          <tr>
            <th scope="row">Chance of being in the top quarter</th>
            <td className="num">{fmtPct(d.p_top)}</td>
          </tr>
        </tbody>
      </table>
    </div>
  );
}

function EvidenceTable({ d }: { d: SpeciesDetail }) {
  const dropped = (d.cleaning.n_fetched ?? 0) - (d.cleaning.n_kept ?? 0);
  const rows: [string, ReactNode, ReactNode][] = [
    [
      "Records",
      `${fmtInt(d.n_records)} from the Philippines; ${fmtInt(d.cleaning.n_kept)} kept after checks, ${fmtInt(dropped)} set aside (mostly duplicates and vague locations)`,
      `GBIF, retrieved ${fmtDate(d.gbif.fetched_at)}`,
    ],
    ["Native status", nativeLabel(d), `World Checklist of Vascular Plants, retrieved ${fmtDate(d.wcvp.fetched_at)}`],
    [
      "How it is harvested",
      d.traits ? `${d.traits.parts_used}; ${d.traits.habitat_note}` : "No published source yet",
      d.traits ? (
        <a href={d.traits.source_url} target="_blank" rel="noreferrer">
          {d.traits.source}
          {d.traits.verified ? "" : ", being checked"}
        </a>
      ) : (
        "—"
      ),
    ],
    ["Protected areas", `${fmtPct(d.pa_share)} of the area where it grows`, "WDPCA Philippines (UNEP-WCMC)"],
    [
      "Forest loss",
      d.forest_loss_rate === null ? "—" : `${fmtPct(d.forest_loss_rate)} of 2000 tree cover lost by 2023, in its provinces`,
      "Hansen et al. 2013, Global Forest Watch",
    ],
    ["National threatened list", d.dao ? DAO_LABEL[d.dao] ?? d.dao : "Not listed", "DENR DAO 2026-20"],
    ["IUCN Red List", "Not retrieved for this version; no category is shown or guessed", "IUCN Red List"],
    [
      "Photo",
      d.photo
        ? `${d.photo.kind === "specimen" ? "Herbarium specimen, cropped. " : ""}${d.photo.creator}, ${d.photo.licence}`
        : "No openly licensed photo found",
      d.photo ? (
        <a href={d.photo.page} target="_blank" rel="noreferrer">
          {d.photo.kind === "specimen" ? "GBIF specimen record" : "iNaturalist"}
        </a>
      ) : (
        "—"
      ),
    ],
  ];
  return (
    <table className="data-table data-table--evidence">
      <thead>
        <tr>
          <th scope="col">Input</th>
          <th scope="col">What we found</th>
          <th scope="col">Source</th>
        </tr>
      </thead>
      <tbody>
        {rows.map(([a, b, c]) => (
          <tr key={a}>
            <th scope="row">{a}</th>
            <td>{b}</td>
            <td className="evidence__source">{c}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
