import { Pause, Play } from "lucide-react";
import { motion } from "motion/react";
import { useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { HexMap } from "../components/HexMapLazy";
import { WithData } from "../components/Status";
import { useSeasons, useSpecies } from "../data/api";
import type { SeasonsIndex, SpeciesDetail } from "../data/schema";
import { useWidth } from "../lib/useWidth";
import { Disclosure } from "./Species";
import "../styles/seasons.css";

type Row = SeasonsIndex["species"][number];

const MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
const SHORT = MONTHS.map((m) => m.slice(0, 3));
/** PAGASA's two seasons: dry December to May, wet June to November. */
const isDry = (m: number) => m === 12 || m <= 5;
/** Plants with fewer records than this have no reliable pattern through the year. */
const MIN_N = 20;
/** Pseudo-count that keeps a month with two or three records from looking like a peak. */
const PRIOR = 3;

/**
 * Records in a month against the records survey effort predicts for it, evened out for small counts.
 * 1 is "as expected from when people go out looking", 2 is twice that.
 */
function activity(counts: number[], effort: number[]): number[] {
  const n = counts.reduce((a, b) => a + b, 0);
  const total = effort.reduce((a, b) => a + b, 0);
  return counts.map((c, i) => {
    const expected = (n * effort[i]) / total;
    return (c + PRIOR) / (expected + PRIOR);
  });
}

function describe(a: number): string {
  if (a >= 1.5) return `${a.toFixed(1)}× the records survey effort explains`;
  if (a <= 0.67) return "fewer records than survey effort explains";
  return "about what survey effort explains";
}

const plantLabel = (r: Pick<Row, "vernacular" | "name">) => (r.vernacular ? `${r.vernacular[0].toUpperCase()}${r.vernacular.slice(1)}` : r.name);

export function Seasons() {
  const seasons = useSeasons();
  return <WithData state={seasons}>{(data) => <SeasonsView data={data} />}</WithData>;
}

function SeasonsView({ data }: { data: SeasonsIndex }) {
  const [params, setParams] = useSearchParams();
  const rows = useMemo(
    () =>
      data.species
        .filter((r) => r.n >= MIN_N)
        .map((r) => ({ ...r, act: activity(r.counts, data.effort) }))
        .sort((a, b) => peak(a.act) - peak(b.act) || b.n - a.n),
    [data],
  );
  const fallback = rows.find((r) => r.slug === "mimosa-pudica") ?? rows[0];
  const slug = params.get("plant") ?? fallback.slug;
  const row = rows.find((r) => r.slug === slug) ?? fallback;
  const [month, setMonth] = useState(() => {
    const m = Number(params.get("m"));
    return m >= 1 && m <= 12 ? m : 1;
  });
  const [playing, setPlaying] = useState(false);
  const [group, setGroup] = useState<"all" | "native" | "introduced">("all");

  useEffect(() => {
    if (!playing) return;
    const id = window.setInterval(() => setMonth((m) => (m % 12) + 1), 1100);
    return () => window.clearInterval(id);
  }, [playing]);

  const pick = (s: string) => {
    const p = new URLSearchParams(params);
    p.set("plant", s);
    setParams(p, { replace: true });
  };
  const shown = rows.filter((r) => group === "all" || (group === "native" ? r.ph_status === "native" : r.ph_status === "introduced"));

  return (
    <div className="page seasons">
      <header className="page__head">
        <h1>A year in the field</h1>
        <p className="lede">
          Slide through the months and watch where each plant was recorded, and when observers saw it in flower or in
          fruit, through the dry season (December to May) and the wet season (June to November). Every month is weighed
          against how many people were out looking.
        </p>
      </header>

      <section className="season-stage" aria-label="One plant through the year">
        <div className="season-controls">
          <label className="season-pick">
            <span>Plant</span>
            <select value={row.slug} onChange={(e) => pick(e.target.value)}>
              {[...rows]
                .sort((a, b) => plantLabel(a).localeCompare(plantLabel(b)))
                .map((r) => (
                  <option key={r.slug} value={r.slug}>
                    {plantLabel(r)} ({r.name}), {r.n} records
                  </option>
                ))}
            </select>
          </label>
          <button
            type="button"
            className="season-play"
            onClick={() => setPlaying((p) => !p)}
            aria-pressed={playing}
            aria-label={playing ? "Pause the year" : "Play the year"}
          >
            {playing ? <Pause size={16} aria-hidden="true" /> : <Play size={16} aria-hidden="true" />}
            {playing ? "Pause" : "Play the year"}
          </button>
        </div>

        <MonthScrubber month={month} setMonth={(m) => (setPlaying(false), setMonth(m))} />

        <div className="season-grid">
          <PlantYear row={row} month={month} setMonth={(m) => (setPlaying(false), setMonth(m))} effort={data.effort} />
          <SeasonMap slug={row.slug} month={month} />
        </div>
      </section>

      <section className="season-calendar" aria-labelledby="calendar-title">
        <header className="season-calendar__head">
          <h2 id="calendar-title">Every plant, every month</h2>
          <p>
            Darker means more records than survey effort explains. A dot marks a month with flowering notes, a ring a
            month with fruiting notes. Sorted by each plant's strongest month; pick a row to follow that plant above.
          </p>
          <div className="segmented-pills" role="group" aria-label="Show">
            {(["all", "native", "introduced"] as const).map((g) => (
              <button key={g} type="button" aria-pressed={group === g} className={group === g ? "is-on" : ""} onClick={() => setGroup(g)}>
                {g === "all" ? "All plants" : g === "native" ? "Native" : "Introduced"}
              </button>
            ))}
          </div>
        </header>
        <Calendar rows={shown} month={month} selected={row.slug} onPick={pick} />
      </section>

      <section className="season-limits">
        <h2>What this can and cannot show</h2>
        <ul>
          <li>
            Records show when someone saw the plant, not when it grows. Philippine plant records peak from March to May,
            when field trips happen, so each month is divided by all vascular-plant records made in that month.
          </li>
          <li>
            Flowering and fruiting come only from observers who noted them, mostly on iNaturalist. Few records carry a
            note, so treat these as hints, not a calendar.
          </li>
          <li>
            Seed spread, die-back and harvest timing are not in any open dataset, so the page does not show them.
          </li>
          <li>Plants with fewer than {MIN_N} dated records are left out. The map uses the atlas's cleaned records only.</li>
        </ul>
        <Disclosure label="How the activity number is worked out">
          <p>
            For each month: (records of the plant + {PRIOR}) ÷ (records expected from effort + {PRIOR}). Expected
            records are the plant's total times that month's share of all Philippine vascular-plant records in GBIF.
            The {PRIOR} added to both sides keeps a month with two or three records from looking like a peak. Data:
            GBIF occurrence search, fetched {data.fetched}; seasons follow PAGASA.
          </p>
        </Disclosure>
      </section>
    </div>
  );
}

function peak(act: number[]): number {
  return act.indexOf(Math.max(...act));
}

function MonthScrubber({ month, setMonth }: { month: number; setMonth: (m: number) => void }) {
  return (
    <div className="season-scrub">
      <div className="season-scrub__bands" aria-hidden="true">
        <span style={{ gridColumn: "1 / 6" }}>Dry season</span>
        <span className="is-wet" style={{ gridColumn: "6 / 12" }}>
          Wet season
        </span>
        <span style={{ gridColumn: "12 / 13" }}>Dry</span>
      </div>
      <input
        type="range"
        min={1}
        max={12}
        step={1}
        value={month}
        onChange={(e) => setMonth(Number(e.target.value))}
        aria-label="Month"
        aria-valuetext={MONTHS[month - 1]}
      />
      <ol className="season-scrub__ticks" aria-hidden="true">
        {SHORT.map((m, i) => (
          <li key={m} className={i + 1 === month ? "is-on" : ""}>
            {m}
          </li>
        ))}
      </ol>
    </div>
  );
}

function PlantYear({
  row,
  month,
  setMonth,
  effort,
}: {
  row: Row & { act: number[] };
  month: number;
  setMonth: (m: number) => void;
  effort: number[];
}) {
  const [ref, width] = useWidth<HTMLDivElement>();
  const counts = row.counts;
  const a = row.act[month - 1];
  const h = 280;
  const m = { top: 14, right: 8, bottom: 40, left: 8 };
  const top = Math.max(2.5, ...row.act);
  const bw = (width - m.left - m.right) / 12;
  const y = (v: number) => m.top + (h - m.top - m.bottom) * (1 - v / top);
  const effMax = Math.max(...effort);

  return (
    <div className="season-year">
      <div className="season-readout" aria-live="polite">
        <p className="season-readout__month">{MONTHS[month - 1]}</p>
        <p className="season-readout__season">{isDry(month) ? "Dry season" : "Wet season"}</p>
        <p className="season-readout__line">
          <Link to={`/species/${row.slug}`}>{plantLabel(row)}</Link>: <span className="num">{counts[month - 1]}</span>{" "}
          {counts[month - 1] === 1 ? "record" : "records"}, {describe(a)}.
        </p>
        <p className="season-readout__line">
          {row.flowering[month - 1] || row.fruiting[month - 1]
            ? [
                row.flowering[month - 1] ? `seen in flower ${row.flowering[month - 1]}×` : "",
                row.fruiting[month - 1] ? `in fruit ${row.fruiting[month - 1]}×` : "",
              ]
                .filter(Boolean)
                .join(", ")
                .replace(/^./, (c) => c.toUpperCase()) + " this month."
            : "No flowering or fruiting notes this month."}
        </p>
      </div>
      <div ref={ref} className="season-chart">
        <svg width={width} height={h} role="img" aria-label={`${plantLabel(row)}: records by month against survey effort`}>
          {Array.from({ length: 12 }, (_, i) => (
            <rect
              key={`band${i}`}
              x={m.left + i * bw}
              y={m.top}
              width={bw}
              height={h - m.top - m.bottom}
              className={isDry(i + 1) ? "band band--dry" : "band"}
            />
          ))}
          {effort.map((e, i) => (
            <rect
              key={`eff${i}`}
              x={m.left + i * bw + bw * 0.12}
              y={h - m.bottom - 6}
              width={bw * 0.76 * (e / effMax)}
              height={3}
              className="effort-tick"
            />
          ))}
          <line x1={m.left} x2={width - m.right} y1={y(1)} y2={y(1)} className="expected" />
          {row.act.map((v, i) => (
            <motion.rect
              key={`bar${i}`}
              x={m.left + i * bw + bw * 0.22}
              width={bw * 0.56}
              initial={false}
              animate={{ y: y(v), height: Math.max(1, y(0) - y(v)) }}
              transition={{ duration: 0.45, ease: [0.2, 0.7, 0.2, 1] }}
              className={i + 1 === month ? "bar is-on" : "bar"}
              rx={1}
              onClick={() => setMonth(i + 1)}
            />
          ))}
          {row.flowering.map((f, i) =>
            f ? <circle key={`fl${i}`} cx={m.left + i * bw + bw / 2 - 6} cy={h - m.bottom + 14} r={4} className="mark-flower" /> : null,
          )}
          {row.fruiting.map((f, i) =>
            f ? <circle key={`fr${i}`} cx={m.left + i * bw + bw / 2 + 6} cy={h - m.bottom + 14} r={3.5} className="mark-fruit" /> : null,
          )}
          {SHORT.map((s, i) => (
            <text key={s} x={m.left + i * bw + bw / 2} y={h - 4} textAnchor="middle" className={i + 1 === month ? "tick is-on" : "tick"}>
              {width < 420 ? s[0] : s}
            </text>
          ))}
          <rect x={m.left + (month - 1) * bw} y={m.top} width={bw} height={h - m.top - m.bottom} className="cursor" />
        </svg>
        <ul className="legend">
          <li>
            <span className="legend__swatch season-swatch--bar" aria-hidden="true" />
            Records against effort
          </li>
          <li>
            <span className="expected-key" aria-hidden="true" />
            As expected from effort
          </li>
          <li>
            <span className="legend__swatch season-swatch--effort" aria-hidden="true" />
            All plant records that month
          </li>
          <li>
            <span className="season-dot" aria-hidden="true" />
            Flowering notes
          </li>
          <li>
            <span className="season-ring" aria-hidden="true" />
            Fruiting notes
          </li>
        </ul>
      </div>
    </div>
  );
}

function SeasonMap({ slug, month }: { slug: string; month: number }) {
  const sp = useSpecies(slug);
  const d: SpeciesDetail | null = sp.status === "ready" ? sp.data : null;
  const cells = d?.seasons;
  const member = useMemo(
    () => (cells ? { fine: cells.cells[String(month)] ?? [], coarse: cells.cells_r4[String(month)] ?? [] } : null),
    [cells, month],
  );
  const all = useMemo(() => (d ? { fine: d.cells, coarse: d.cells_r4 } : null), [d]);
  const n = member ? member.fine.length : 0;
  return (
    <figure className="season-map">
      <div className="season-map__frame">
        <HexMap
          mode="species"
          member={member}
          preview={all}
          bounds={d?.bounds ?? null}
          interactive={false}
          padding={28}
          label={`Where it was recorded in ${MONTHS[month - 1]}`}
        />
      </div>
      <figcaption>
        <span className="season-key season-key--month" aria-hidden="true" /> Recorded in {MONTHS[month - 1]}{" "}
        <span className="num">({n} {n === 1 ? "cell" : "cells"})</span>
        <span className="season-key season-key--all" aria-hidden="true" /> Any month
      </figcaption>
    </figure>
  );
}

function Calendar({ rows, month, selected, onPick }: { rows: (Row & { act: number[] })[]; month: number; selected: string; onPick: (s: string) => void }) {
  const shade = (v: number) => (v >= 2 ? "c4" : v >= 1.5 ? "c3" : v >= 1.15 ? "c2" : v > 0.85 ? "c1" : "c0");
  return (
    <div className="calendar" role="table" aria-label="Activity by month for every plant">
      <div className="calendar__row calendar__row--head" role="row">
        <span role="columnheader" className="calendar__name">
          Plant
        </span>
        {SHORT.map((s, i) => (
          <span key={s} role="columnheader" className={`calendar__month${i + 1 === month ? " is-on" : ""}${isDry(i + 1) ? " is-dry" : ""}`}>
            {s[0]}
            <span className="sr-only">{s.slice(1)}</span>
          </span>
        ))}
      </div>
      {rows.map((r) => (
        <button
          type="button"
          role="row"
          key={r.slug}
          className={`calendar__row${r.slug === selected ? " is-selected" : ""}`}
          onClick={() => onPick(r.slug)}
          aria-pressed={r.slug === selected}
        >
          <span role="rowheader" className="calendar__name">
            {plantLabel(r)}
            {r.ph_status === "introduced" ? <span className="calendar__tag">introduced</span> : null}
          </span>
          {r.act.map((v, i) => (
            <span key={i} role="cell" className={`calendar__cell ${shade(v)}${i + 1 === month ? " is-on" : ""}`} title={`${MONTHS[i]}: ${describe(v)}`}>
              {r.flowering[i] ? <i className="calendar__flower" aria-hidden="true" /> : null}
              {r.fruiting[i] ? <i className="calendar__fruit" aria-hidden="true" /> : null}
              <span className="sr-only">
                {MONTHS[i]}: {describe(v)}
                {r.flowering[i] ? ", flowering notes" : ""}
                {r.fruiting[i] ? ", fruiting notes" : ""}
              </span>
            </span>
          ))}
        </button>
      ))}
    </div>
  );
}
