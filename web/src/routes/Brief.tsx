import { ArrowLeft, Printer } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { z } from "zod";
import { Mark } from "../components/Mark";
import { PlantPhoto } from "../components/PlantPhoto";
import { LevelMeter } from "../components/Reasons";
import { Stamp } from "../components/Stamp";
import { WithData } from "../components/Status";
import { load, useSpecies, useSpeciesList } from "../data/api";
import type { SpeciesDetail } from "../data/schema";
import { explain, summary } from "../lib/explain";
import { fmtDate, fmtInt, fmtPct } from "../lib/format";
import { COMPONENT_META, DAO_LABEL, level, rankSentence, SCORED_COMPONENTS } from "../lib/vocab";
import { NotFound } from "./NotFound";

export function Brief() {
  const { slug } = useParams();
  const detail = useSpecies(slug);
  const list = useSpeciesList();
  useEffect(() => {
    document.body.classList.add("is-brief");
    return () => document.body.classList.remove("is-brief");
  }, []);
  if (detail.status === "error" && detail.error.kind === "missing") return <NotFound what="plant" />;
  return (
    <WithData state={list}>
      {(cohort) => (
        <WithData state={detail}>{(d) => <BriefSheet d={d} nScored={cohort.filter((s) => !s.gate).length} />}</WithData>
      )}
    </WithData>
  );
}

/** Practical steps, chosen by which parts score high. Advice for planning, never a permit. */
function actions(d: SpeciesDetail): string[] {
  const out: string[] = [];
  const hi = (k: "R" | "H" | "E") => (level(d.components[k])?.index ?? 0) >= 2;
  if (d.dao) {
    out.push(
      `It is on DENR's national list of threatened plants (${DAO_LABEL[d.dao] ?? d.dao}). Collecting or trading it from the wild needs a DENR permit.`,
    );
  } else {
    out.push("Before collecting, check DENR's current list of threatened plants (DAO 2026-20) and local rules.");
  }
  if (hi("H")) {
    out.push("Where the use allows, take leaves, fruit or fallen bark instead of roots, rhizomes or whole plants, and leave mature plants standing.");
    out.push("Grow it from seed or cuttings in community nurseries so that less is taken from the wild.");
  }
  if (hi("E")) {
    out.push("Ask the local protected area office (PAMB) or CENRO whether a site is protected before gathering there.");
  }
  if (hi("R")) {
    out.push("Photograph and record any plant you find (place, date) on iNaturalist: each record makes its range clearer.");
  }
  out.push("Share what you see with your LGU or DENR office: harvest amounts are the evidence this atlas lacks.");
  return out;
}

function BriefSheet({ d, nScored }: { d: SpeciesDetail; nScored: number }) {
  const why = explain(d);
  const title = d.vernacular ? d.vernacular.split(" / ")[0] : d.name;
  useEffect(() => {
    document.title = `Field brief: ${title} (${d.name})`;
    return () => {
      document.title = "Harvester Risk Atlas";
    };
  }, [title, d.name]);

  return (
    <div className="brief-wrap">
      <div className="brief-tools">
        <Link to={`/species/${d.slug}`} className="button">
          <ArrowLeft size={16} aria-hidden="true" /> Back to {title}
        </Link>
        <button type="button" className="button button--primary" onClick={() => window.print()}>
          <Printer size={16} aria-hidden="true" /> Print or save as PDF
        </button>
      </div>

      <article className="brief">
        <header className="brief__top">
          <div className="brief__brand">
            <Mark size={28} />
            <span>Harvester Risk Atlas</span>
          </div>
          <span className="brief__kind">Field brief, {fmtDate(new Date().toISOString())}</span>
        </header>

        <section className="brief__hero">
          <div className="brief__photo">
            <PlantPhoto s={d} ratio="4 / 3" credit="below" eager />
          </div>
          <div className="brief__id">
            <h1>
              {d.vernacular ? <span>{d.vernacular}</span> : null}
              <i className="binomial">{d.name}</i>
            </h1>
            <p className="brief__family">{d.family} family</p>
            <div className="brief__stamp">
              <Stamp tier={d.tier} rank={d.rank} of={d.rank !== null ? nScored : undefined} size={104} animate={false} />
              <div>
                <p>{summary(d, nScored)}</p>
                {d.rank !== null ? <p className="brief__rank">{rankSentence(d, nScored)}</p> : null}
              </div>
            </div>
          </div>
        </section>

        {!d.gate ? (
          <section className="brief__why">
            <h2>Why</h2>
            <ul>
              {SCORED_COMPONENTS.map((k) => (
                <li key={k}>
                  <div className="brief__why-head">
                    <b>{COMPONENT_META[k].label}</b>
                    <LevelMeter value={d.components[k]} color={COMPONENT_META[k].color} label={COMPONENT_META[k].label} />
                  </div>
                  <p>{why[k]}</p>
                </li>
              ))}
            </ul>
          </section>
        ) : null}

        <section className="brief__where">
          <div>
            <h2>Where it grows</h2>
            <p>
              Recorded in {fmtInt(d.n_cells)} areas across {d.provinces.length} provinces
              {d.pa_share !== null ? `, ${fmtPct(d.pa_share)} of it protected` : ""}. Most records:{" "}
              {d.provinces
                .slice(0, 5)
                .map((p) => p.name)
                .join(", ") || "none"}
              .
            </p>
            <p className="brief__fine">Areas of about 1,770 km². Exact locations are withheld to protect the plant.</p>
            {/* Actions sit beside the map so the sheet fits on one A4 page. */}
            <section className="brief__do">
              <h2>What you can do</h2>
              <ol>
                {actions(d).map((a) => (
                  <li key={a}>{a}</li>
                ))}
              </ol>
            </section>
          </div>
          <MiniMap cells={d.cells_r4} />
        </section>

        <footer className="brief__foot">
          <p>
            For research and education. Not medical advice, not a harvest permit, not a Red List assessment.
          </p>
          <p>
            Sources: GBIF occurrence records; World Checklist of Vascular Plants; WDPCA Philippines; Global Forest Watch;
            Stuart, Philippine Medicinal Plants; DENR DAO 2026-20.
            {d.photo ? ` Photo: ${d.photo.creator}, ${d.photo.licence}, iNaturalist.` : ""} Full page:{" "}
            {window.location.origin}
            {import.meta.env.BASE_URL}species/{d.slug}
          </p>
        </footer>
      </article>
    </div>
  );
}

const Geo = z.object({
  features: z.array(
    z.object({ id: z.string().optional(), geometry: z.object({ type: z.string(), coordinates: z.any() }) }),
  ),
});
type GeoT = z.infer<typeof Geo>;

/** A static SVG map for print: Philippine land and the plant's areas. */
function MiniMap({ cells }: { cells: string[] }) {
  const [land, setLand] = useState<GeoT | null>(null);
  const [hex, setHex] = useState<GeoT | null>(null);
  useEffect(() => {
    load("geo/land.geojson", Geo).then(setLand, () => setLand(null));
    load("geo/cells_r4.geojson", Geo).then(setHex, () => setHex(null));
  }, []);
  const W = 220;
  const H = 300;
  const [w, s, e, n] = [116.4, 4.4, 127.0, 21.2];
  const k = Math.cos((12.5 * Math.PI) / 180);
  const scale = Math.min(W / ((e - w) * k), H / (n - s));
  const x = (lon: number) => (lon - w) * k * scale;
  const y = (lat: number) => (n - lat) * scale;
  const path = (g: { type: string; coordinates: number[][][] | number[][][][] }) => {
    const polys = (g.type === "Polygon" ? [g.coordinates] : g.coordinates) as number[][][][];
    return polys
      .map((poly) => poly.map((ring) => ring.map(([lo, la], i) => `${i ? "L" : "M"}${x(lo).toFixed(1)},${y(la).toFixed(1)}`).join("") + "Z").join(""))
      .join("");
  };
  const set = useMemo(() => new Set(cells), [cells]);
  return (
    <svg className="brief__map" viewBox={`0 0 ${W} ${H}`} role="img" aria-label={`Map: ${cells.length} areas where it was recorded`}>
      {land?.features.map((f, i) => <path key={i} d={path(f.geometry)} className="mini-land" />)}
      {hex?.features
        .filter((f) => f.id && set.has(f.id))
        .map((f) => <path key={f.id} d={path(f.geometry)} className="mini-cell" />)}
    </svg>
  );
}
