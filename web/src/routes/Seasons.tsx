import { Pause, Play } from "lucide-react";
import { motion } from "motion/react";
import { useEffect, useLayoutEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { Link, useSearchParams } from "react-router-dom";
import type { HoverInfo } from "../components/HexMap";
import { HexMap } from "../components/HexMapLazy";
import { WithData } from "../components/Status";
import { useSeasons, useSpecies } from "../data/api";
import type { SeasonsIndex, SpeciesDetail } from "../data/schema";
import { fmtInt } from "../lib/format";
import { useWidth } from "../lib/useWidth";
import { Disclosure } from "./Species";
import "../styles/seasons.css";
import "../styles/seasons-calendar.css";

type Row = SeasonsIndex["species"][number];
type Plant = Row & { act: number[] };

const MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
const SHORT = MONTHS.map((m) => m.slice(0, 3));
/** PAGASA's two seasons: dry December to May, wet June to November. */
const isDry = (m: number) => m === 12 || m <= 5;
const seasonOf = (m: number) => (isDry(m) ? "Dry season" : "Wet season");
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

function expectedIn(row: Row, i: number, effort: number[]): number {
  const total = effort.reduce((a, b) => a + b, 0);
  return (row.n * effort[i]) / total;
}

/** The five steps of the calendar's scale; the readout, tooltips and legend all use these words. */
const LEVELS = [
  { key: "c0", label: "Fewer than effort explains", test: (a: number) => a <= 0.85 },
  { key: "c1", label: "About what effort explains", test: (a: number) => a < 1.15 },
  { key: "c2", label: "A little more than effort explains", test: (a: number) => a < 1.5 },
  { key: "c3", label: "1.5 to 2 times what effort explains", test: (a: number) => a < 2 },
  { key: "c4", label: "2 times or more what effort explains", test: () => true },
] as const;
const level = (a: number) => LEVELS.find((l) => l.test(a))!;

function describe(a: number): string {
  if (a >= 1.5) return `${a.toFixed(1)}× the records survey effort explains`;
  if (a <= 0.85) return "fewer records than survey effort explains";
  if (a >= 1.15) return "a little more than survey effort explains";
  return "about what survey effort explains";
}

const plantLabel = (r: Pick<Row, "vernacular" | "name">) => (r.vernacular ? `${r.vernacular[0].toUpperCase()}${r.vernacular.slice(1)}` : r.name);
const reduceMotion = () => typeof window !== "undefined" && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

// ------------------------------------------------------------------------------------------------ tooltip
type Tip = { x: number; y: number; body: ReactNode } | null;

/** A label that follows the pointer (or sits by a focused control), kept inside the window. */
function FloatTip({ tip }: { tip: Tip }) {
  const ref = useRef<HTMLDivElement>(null);
  const [size, setSize] = useState({ w: 280, h: 220 });
  useLayoutEffect(() => {
    const r = ref.current?.getBoundingClientRect();
    if (r && (Math.abs(r.height - size.h) > 1 || Math.abs(r.width - size.w) > 1)) setSize({ w: r.width, h: r.height });
  });
  if (!tip) return null;
  const vw = window.innerWidth;
  const vh = window.innerHeight;
  // Below and right of the pointer; flipped to the other side where it would leave the window.
  const left = tip.x + 16 + size.w > vw - 8 ? Math.max(8, tip.x - size.w - 12) : tip.x + 16;
  const top = tip.y + 16 + size.h > vh - 8 ? Math.max(72, tip.y - size.h - 12) : tip.y + 16;
  return (
    <div ref={ref} className="season-tip" style={{ left, top, width: 280 }} role="tooltip">
      {tip.body}
    </div>
  );
}

/** Pointer and keyboard handlers that open the tooltip for one element. */
function tipHandlers(setTip: (t: Tip) => void, body: () => ReactNode) {
  return {
    onPointerEnter: (e: React.PointerEvent) => setTip({ x: e.clientX, y: e.clientY, body: body() }),
    onPointerMove: (e: React.PointerEvent) => setTip({ x: e.clientX, y: e.clientY, body: body() }),
    onPointerLeave: () => setTip(null),
    onFocus: (e: React.FocusEvent) => {
      const r = (e.currentTarget as Element).getBoundingClientRect();
      setTip({ x: r.right, y: r.bottom, body: body() });
    },
    onBlur: () => setTip(null),
  };
}

/** What one plant did in one month, in words. */
function MonthFacts({ row, i, effort, hint }: { row: Plant; i: number; effort: number[]; hint?: string }) {
  const a = row.act[i];
  const lv = level(a);
  const exp = expectedIn(row, i, effort);
  return (
    <>
      <p className="season-tip__head">
        <b>{plantLabel(row)}</b> · {MONTHS[i]}
      </p>
      <p className="season-tip__sub">
        {seasonOf(i + 1)}
        {row.ph_status === "introduced" ? " · introduced plant" : ""}
      </p>
      <p className="season-tip__row">
        <span className={`season-tip__swatch calendar__cell ${lv.key}`} aria-hidden="true" />
        <span>{lv.label}</span>
      </p>
      <dl className="season-tip__facts">
        <dt>Records this month</dt>
        <dd className="num">{fmtInt(row.counts[i])}</dd>
        <dt>Expected from effort</dt>
        <dd className="num">{exp < 10 ? exp.toFixed(1) : fmtInt(exp)}</dd>
        <dt>Flowering notes</dt>
        <dd className="num">{row.flowering[i] || "none"}</dd>
        <dt>Fruiting notes</dt>
        <dd className="num">{row.fruiting[i] || "none"}</dd>
      </dl>
      {hint ? <p className="season-tip__hint">{hint}</p> : null}
    </>
  );
}

export function Seasons() {
  const seasons = useSeasons();
  return <WithData state={seasons}>{(data) => <SeasonsView data={data} />}</WithData>;
}

function SeasonsView({ data }: { data: SeasonsIndex }) {
  const [params, setParams] = useSearchParams();
  const rows = useMemo(
    () => data.species.filter((r) => r.n >= MIN_N).map((r) => ({ ...r, act: activity(r.counts, data.effort) })),
    [data],
  );
  const fallback = rows.find((r) => r.slug === "mimosa-pudica") ?? rows[0];
  const slug = params.get("plant") ?? fallback.slug;
  const row = rows.find((r) => r.slug === slug) ?? fallback;
  const [month, setMonthState] = useState(() => {
    const m = Number(params.get("m"));
    return m >= 1 && m <= 12 ? m : 1;
  });
  const [playing, setPlaying] = useState(false);
  const [group, setGroup] = useState<"all" | "native" | "introduced">("all");
  const [sort, setSort] = useState<"peak" | "name" | "records">("peak");
  const [tip, setTip] = useState<Tip>(null);
  const stage = useRef<HTMLElement>(null);

  useEffect(() => {
    if (!playing) return;
    const id = window.setInterval(() => setMonthState((m) => (m % 12) + 1), 1100);
    return () => window.clearInterval(id);
  }, [playing]);

  // The tooltip never outlives a scroll: the element under it has moved.
  useEffect(() => {
    if (!tip) return;
    const hide = () => setTip(null);
    window.addEventListener("scroll", hide, { passive: true });
    return () => window.removeEventListener("scroll", hide);
  }, [tip]);

  const setMonth = (m: number) => {
    setPlaying(false);
    setMonthState(m);
  };
  const pick = (s: string, m?: number) => {
    const p = new URLSearchParams(params);
    p.set("plant", s);
    if (m) p.set("m", String(m));
    setParams(p, { replace: true });
    if (m) setMonth(m);
  };
  /** From the calendar: follow that plant and month in the stage above. */
  const follow = (s: string, m: number) => {
    pick(s, m);
    setTip(null);
    stage.current?.scrollIntoView({ behavior: reduceMotion() ? "auto" : "smooth", block: "start" });
  };

  const shown = rows
    .filter((r) => group === "all" || (group === "native" ? r.ph_status === "native" : r.ph_status === "introduced"))
    .sort((a, b) =>
      sort === "name"
        ? plantLabel(a).localeCompare(plantLabel(b))
        : sort === "records"
          ? b.n - a.n
          : peak(a.act) - peak(b.act) || b.n - a.n,
    );

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

      <section ref={stage} className="season-stage" aria-label="One plant through the year">
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

        <MonthScrubber month={month} setMonth={setMonth} effort={data.effort} setTip={setTip} />

        <div className="season-grid">
          <PlantYear row={row} month={month} setMonth={setMonth} effort={data.effort} setTip={setTip} />
          <SeasonMap slug={row.slug} month={month} name={plantLabel(row)} />
        </div>
      </section>

      <section className="season-calendar" aria-labelledby="calendar-title">
        <header className="season-calendar__head">
          <h2 id="calendar-title">Every plant, every month</h2>
          <p>
            Each square is one plant in one month. Its colour says how many records that month holds against what survey
            effort would predict. Point at a square for its numbers; click or tap it to see that plant and month on the map
            above.
          </p>
        </header>

        <div className="calendar-tools">
          <div className="segmented-pills" role="group" aria-label="Which plants">
            {(["all", "native", "introduced"] as const).map((g) => (
              <button key={g} type="button" aria-pressed={group === g} className={group === g ? "is-on" : ""} onClick={() => setGroup(g)}>
                {g === "all" ? `All plants (${rows.length})` : g === "native" ? "Native" : "Introduced"}
              </button>
            ))}
          </div>
          <label className="calendar-sort">
            <span>Sort by</span>
            <select value={sort} onChange={(e) => setSort(e.target.value as typeof sort)}>
              <option value="peak">Strongest month</option>
              <option value="name">Name, A to Z</option>
              <option value="records">Most records</option>
            </select>
          </label>
        </div>

        <CalendarLegend />

        <Calendar rows={shown} month={month} selected={row.slug} effort={data.effort} onFollow={follow} onPick={(s) => pick(s)} setTip={setTip} />
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
            One expedition or bioblitz can make a month stand out for one plant; the effort correction cannot remove that.
          </li>
          <li>Seed spread, die-back and harvest timing are not in any open dataset, so the page does not show them.</li>
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
      <FloatTip tip={tip} />
    </div>
  );
}

function peak(act: number[]): number {
  return act.indexOf(Math.max(...act));
}

function EffortFacts({ i, effort }: { i: number; effort: number[] }) {
  const total = effort.reduce((a, b) => a + b, 0);
  return (
    <>
      <p className="season-tip__head">
        <b>{MONTHS[i]}</b> · {seasonOf(i + 1)}
      </p>
      <p>
        <b className="num">{fmtInt(effort[i])}</b> plant records of any kind were made in the Philippines in {MONTHS[i]} (
        {Math.round((100 * effort[i]) / total)}% of the year's).
      </p>
      <p className="season-tip__hint">Busier months need more records before a plant stands out.</p>
    </>
  );
}

function MonthScrubber({
  month,
  setMonth,
  effort,
  setTip,
}: {
  month: number;
  setMonth: (m: number) => void;
  effort: number[];
  setTip: (t: Tip) => void;
}) {
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
      <div className="season-scrub__ticks">
        {SHORT.map((m, i) => (
          <button
            key={m}
            type="button"
            tabIndex={-1}
            className={i + 1 === month ? "is-on" : ""}
            onClick={() => setMonth(i + 1)}
            aria-label={MONTHS[i]}
            {...tipHandlers(setTip, () => <EffortFacts i={i} effort={effort} />)}
          >
            {m}
          </button>
        ))}
      </div>
    </div>
  );
}

function PlantYear({
  row,
  month,
  setMonth,
  effort,
  setTip,
}: {
  row: Plant;
  month: number;
  setMonth: (m: number) => void;
  effort: number[];
  setTip: (t: Tip) => void;
}) {
  const [ref, width] = useWidth<HTMLDivElement>();
  const [hover, setHover] = useState<number | null>(null);
  // A new plant (picked from the calendar below) starts with no hovered month.
  useEffect(() => setHover(null), [row.slug]);
  const counts = row.counts;
  const a = row.act[month - 1];
  const h = 280;
  const m = { top: 14, right: 8, bottom: 40, left: 34 };
  const top = Math.max(2.5, ...row.act);
  const bw = (width - m.left - m.right) / 12;
  const y = (v: number) => m.top + (h - m.top - m.bottom) * (1 - v / top);
  const effMax = Math.max(...effort);
  const ticks = [1, 2, 3, 4].filter((v) => v <= top);

  return (
    <div className="season-year">
      <div className="season-readout" aria-live="polite">
        <p className="season-readout__month">{MONTHS[month - 1]}</p>
        <p className="season-readout__season">{seasonOf(month)}</p>
        <p className="season-readout__line">
          <Link to={`/species/${row.slug}`}>{plantLabel(row)}</Link>: <span className="num">{counts[month - 1]}</span>{" "}
          {counts[month - 1] === 1 ? "record" : "records"} against{" "}
          <span className="num">{Math.round(expectedIn(row, month - 1, effort))}</span> expected, {describe(a)}.
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
        <p className="season-chart__title">Records each month, against what survey effort predicts</p>
        <svg width={width} height={h} role="img" aria-label={`${plantLabel(row)}: records by month against survey effort`} onPointerLeave={() => (setHover(null), setTip(null))}>
          {Array.from({ length: 12 }, (_, i) => (
            <rect key={`band${i}`} x={m.left + i * bw} y={m.top} width={bw} height={h - m.top - m.bottom} className={isDry(i + 1) ? "band band--dry" : "band"} />
          ))}
          {ticks.map((v) => (
            <g key={v}>
              <line x1={m.left} x2={width - m.right} y1={y(v)} y2={y(v)} className={v === 1 ? "expected" : "grid"} />
              <text x={m.left - 6} y={y(v) + 4} textAnchor="end" className="tick num">
                {v}×
              </text>
            </g>
          ))}
          {effort.map((e, i) => (
            <rect key={`eff${i}`} x={m.left + i * bw + bw * 0.12} y={h - m.bottom - 6} width={bw * 0.76 * (e / effMax)} height={3} className="effort-tick" />
          ))}
          {row.act.map((v, i) => (
            <motion.rect
              key={`bar${i}`}
              x={m.left + i * bw + bw * 0.22}
              width={bw * 0.56}
              initial={false}
              animate={{ y: y(v), height: Math.max(1, y(0) - y(v)) }}
              transition={{ duration: 0.45, ease: [0.2, 0.7, 0.2, 1] }}
              className={`bar${i + 1 === month ? " is-on" : ""}${hover === i ? " is-hover" : ""}`}
              rx={1}
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
              {width < 460 ? s[0] : s}
            </text>
          ))}
          <rect x={m.left + (month - 1) * bw} y={m.top} width={bw} height={h - m.top - m.bottom} className="cursor" />
          {/* One hit area per month: hover for the numbers, click to show the month on the map. */}
          {Array.from({ length: 12 }, (_, i) => (
            <rect
              key={`hit${i}`}
              x={m.left + i * bw}
              y={0}
              width={bw}
              height={h}
              className="hit"
              onClick={() => setMonth(i + 1)}
              onPointerEnter={(e) => {
                setHover(i);
                setTip({ x: e.clientX, y: e.clientY, body: <MonthFacts row={row} i={i} effort={effort} hint={i + 1 === month ? undefined : "Click to show this month on the map"} /> });
              }}
              onPointerMove={(e) => setTip({ x: e.clientX, y: e.clientY, body: <MonthFacts row={row} i={i} effort={effort} hint={i + 1 === month ? undefined : "Click to show this month on the map"} /> })}
            />
          ))}
        </svg>
        <ul className="legend">
          <li>
            <span className="legend__swatch season-swatch--bar" aria-hidden="true" />
            Records against effort (month on the map)
          </li>
          <li>
            <span className="expected-key" aria-hidden="true" />
            1×: as expected from effort
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

function SeasonMap({ slug, month, name }: { slug: string; month: number; name: string }) {
  const sp = useSpecies(slug);
  const d: SpeciesDetail | null = sp.status === "ready" ? sp.data : null;
  const cells = d?.seasons;
  const member = useMemo(
    () => (cells ? { fine: cells.cells[String(month)] ?? [], coarse: cells.cells_r4[String(month)] ?? [] } : null),
    [cells, month],
  );
  const all = useMemo(() => (d ? { fine: d.cells, coarse: d.cells_r4 } : null), [d]);
  const [hover, setHover] = useState<HoverInfo>(null);
  const frame = useRef<HTMLDivElement>(null);
  const n = member ? member.fine.length : 0;
  const here = hover && member ? member.fine.includes(hover.cell.h3) || member.coarse.includes(hover.cell.h3) : false;
  const ever = hover && all ? all.fine.includes(hover.cell.h3) || all.coarse.includes(hover.cell.h3) : false;
  const months =
    hover && cells
      ? Object.entries(cells.cells)
          .filter(([m, list]) => list.includes(hover.cell.h3) || (cells.cells_r4[m] ?? []).includes(hover.cell.h3))
          .map(([m]) => SHORT[Number(m) - 1])
      : [];
  return (
    <figure className="season-map">
      <div ref={frame} className="season-map__frame">
        <HexMap
          mode="species"
          member={member}
          preview={all}
          bounds={d?.bounds ?? null}
          interactive={false}
          padding={28}
          onHover={setHover}
          label={`Where ${name} was recorded in ${MONTHS[month - 1]}`}
        />
        {hover && (here || ever) ? (
          <div className="map-tip" style={tipAt(hover, frame.current)} aria-hidden="true">
            <p className="map-tip__head">
              {here ? (
                <>
                  <b>{name}</b> recorded in this area in <b>{MONTHS[month - 1]}</b>.
                </>
              ) : (
                <>
                  <b>{name}</b> recorded here, but not in {MONTHS[month - 1]}.
                </>
              )}
            </p>
            {months.length ? <p className="season-tip__hint">Months with records here: {months.join(", ")}</p> : null}
            <p className="season-tip__hint">Areas are about 250 km² (zoomed in) or 1,770 km² (whole country); never exact spots.</p>
          </div>
        ) : null}
      </div>
      <figcaption>
        <span className="season-key season-key--month" aria-hidden="true" /> Recorded in {MONTHS[month - 1]}{" "}
        <span className="num">({n} {n === 1 ? "area" : "areas"})</span>
        <span className="season-key season-key--all" aria-hidden="true" /> Recorded in other months
      </figcaption>
    </figure>
  );
}

function CalendarLegend() {
  return (
    <div className="calendar-legend" aria-label="How to read the calendar">
      <div className="calendar-legend__scale">
        <span className="calendar-legend__title">Records against survey effort</span>
        <ol>
          {LEVELS.map((l) => (
            <li key={l.key}>
              <span className={`calendar-legend__swatch calendar__cell ${l.key}`} aria-hidden="true" />
              {l.label.replace(" what effort explains", "").replace(" than effort explains", "")}
            </li>
          ))}
        </ol>
      </div>
      <ul className="calendar-legend__marks">
        <li>
          <span className="calendar-legend__swatch calendar__cell c1" aria-hidden="true">
            <i className="calendar__flower" />
          </span>
          Flowering notes
        </li>
        <li>
          <span className="calendar-legend__swatch calendar__cell c1" aria-hidden="true">
            <i className="calendar__fruit" />
          </span>
          Fruiting notes
        </li>
        <li>
          <span className="calendar-legend__swatch calendar__cell c1 is-on" aria-hidden="true" />
          Month shown on the map
        </li>
      </ul>
    </div>
  );
}

function Calendar({
  rows,
  month,
  selected,
  effort,
  onFollow,
  onPick,
  setTip,
}: {
  rows: Plant[];
  month: number;
  selected: string;
  effort: number[];
  onFollow: (slug: string, m: number) => void;
  onPick: (slug: string) => void;
  setTip: (t: Tip) => void;
}) {
  const [hot, setHot] = useState<{ r: string; m: number } | null>(null);
  return (
    <div className="calendar" role="table" aria-label="Records against survey effort, by plant and month" onPointerLeave={() => setHot(null)}>
      <div className="calendar__row calendar__row--seasons" role="presentation" aria-hidden="true">
        <span />
        <span className="calendar__season" style={{ gridColumn: "2 / 7" }}>
          Dry season
        </span>
        <span className="calendar__season is-wet" style={{ gridColumn: "7 / 13" }}>
          Wet season
        </span>
        <span className="calendar__season" style={{ gridColumn: "13 / 14" }}>
          Dry
        </span>
      </div>
      <div className="calendar__row calendar__row--head" role="row">
        <span role="columnheader" className="calendar__name">
          Plant <span className="calendar__count">records</span>
        </span>
        {SHORT.map((s, i) => (
          <span
            key={s}
            role="columnheader"
            className={`calendar__month${i + 1 === month ? " is-on" : ""}${hot?.m === i ? " is-hot" : ""}${isDry(i + 1) ? " is-dry" : ""}`}
            {...tipHandlers(setTip, () => <EffortFacts i={i} effort={effort} />)}
          >
            <span className="calendar__abbr">{s}</span>
            <span className="calendar__letter" aria-hidden="true">
              {s[0]}
            </span>
          </span>
        ))}
      </div>
      {rows.map((r) => (
        <div key={r.slug} role="row" className={`calendar__row${r.slug === selected ? " is-selected" : ""}${hot?.r === r.slug ? " is-hot" : ""}`}>
          <span role="rowheader" className="calendar__name">
            <button type="button" className="calendar__plant" onClick={() => onPick(r.slug)} aria-pressed={r.slug === selected} title={`${r.name}: show this plant above`}>
              <span className="calendar__label">{plantLabel(r)}</span>
              {r.ph_status === "introduced" ? <span className="calendar__tag">introduced</span> : null}
            </button>
            <span className="calendar__count num">{fmtInt(r.n)}</span>
          </span>
          {r.act.map((v, i) => (
            <span key={i} role="cell" className="calendar__slot">
              <button
                type="button"
                className={`calendar__cell ${level(v).key}${i + 1 === month && r.slug === selected ? " is-on" : ""}${i + 1 === month ? " is-col" : ""}`}
                aria-label={`${plantLabel(r)}, ${MONTHS[i]}: ${r.counts[i]} records, ${describe(v)}${r.flowering[i] ? `, ${r.flowering[i]} flowering notes` : ""}${r.fruiting[i] ? `, ${r.fruiting[i]} fruiting notes` : ""}. Show on the map.`}
                onClick={() => onFollow(r.slug, i + 1)}
                {...tipHandlers(setTip, () => <MonthFacts row={r} i={i} effort={effort} hint="Click to see this plant and month on the map" />)}
                onPointerEnter={(e) => {
                  setHot({ r: r.slug, m: i });
                  setTip({ x: e.clientX, y: e.clientY, body: <MonthFacts row={r} i={i} effort={effort} hint="Click to see this plant and month on the map" /> });
                }}
              >
                {r.flowering[i] ? <i className="calendar__flower" aria-hidden="true" /> : null}
                {r.fruiting[i] ? <i className="calendar__fruit" aria-hidden="true" /> : null}
              </button>
            </span>
          ))}
        </div>
      ))}
    </div>
  );
}

/** The map tooltip beside the pointer, flipped to stay inside the map frame. */
function tipAt(hover: NonNullable<HoverInfo>, frame: HTMLDivElement | null): React.CSSProperties {
  const w = frame?.clientWidth ?? 400;
  const h = frame?.clientHeight ?? 500;
  return {
    left: hover.x > w - 260 ? Math.max(6, hover.x - 254) : hover.x + 14,
    top: hover.y > h - 160 ? Math.max(6, hover.y - 150) : hover.y + 14,
    width: 240,
  };
}
