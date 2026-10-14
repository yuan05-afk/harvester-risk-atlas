import { scaleLinear } from "d3-scale";
import { Link } from "react-router-dom";
import type { SpeciesSummary } from "../../data/schema";
import { useWidth } from "../../lib/useWidth";
import { TIER_META } from "../../lib/vocab";

/**
 * Every scored species, ordered by median rank: dot = median, line = 90% interval.
 * Rank 1 (highest priority) on the left. Overlapping lines are the point: those
 * species cannot be told apart on current evidence.
 */
export function Caterpillar({
  species,
  highlight,
  rankOverride,
}: {
  species: SpeciesSummary[];
  highlight?: string;
  rankOverride?: Map<string, number>;
}) {
  const [ref, width] = useWidth<HTMLDivElement>(800);
  const scored = species.filter((s) => s.rank !== null);
  const n = scored.length;
  const narrow = width < 640;
  const labelW = narrow ? 0 : 230;
  const plotW = Math.max(160, width - labelW);
  const x = scaleLinear()
    .domain([1, n])
    .range([10, plotW - 10]);
  const rows = [...scored].sort((a, b) => (a.rank ?? 0) - (b.rank ?? 0) || a.name.localeCompare(b.name));
  const ticks = [1, 5, 10, 15, 20, 25, n].filter((t, i, arr) => t <= n && arr.indexOf(t) === i);

  return (
    <div ref={ref} className="caterpillar">
      <div className="caterpillar__axis" style={{ marginLeft: labelW }} aria-hidden="true">
        <svg width={plotW} height={22}>
          {ticks.map((t) => (
            <g key={t} transform={`translate(${x(t)},0)`}>
              <line y1={16} y2={22} className="caterpillar__tick" />
              <text y={12} textAnchor="middle" className="caterpillar__ticklabel">
                {t}
              </text>
            </g>
          ))}
        </svg>
      </div>
      <ol className="caterpillar__rows">
        {rows.map((s) => {
          const [lo, hi] = [s.rank_ci[0] ?? s.rank!, s.rank_ci[1] ?? s.rank!];
          const alt = rankOverride?.get(s.slug);
          const color = TIER_META[s.tier].color;
          return (
            <li key={s.slug} className={`caterpillar__row${s.slug === highlight ? " is-highlight" : ""}`}>
              <Link to={`/species/${s.slug}`} className="caterpillar__link">
                <span className="caterpillar__name" style={{ width: narrow ? "100%" : labelW }}>
                  <i className="binomial">{s.name}</i>
                  <span className="caterpillar__vern">{s.vernacular}</span>
                </span>
                <svg
                  width={plotW}
                  height={22}
                  role="img"
                  aria-label={`${s.tier}. Median rank ${s.rank}, 90% interval ${lo} to ${hi}${
                    alt !== undefined ? `; ${alt} under your weights` : ""
                  }`}
                >
                  {ticks.map((t) => (
                    <line key={t} x1={x(t)} x2={x(t)} y1={0} y2={22} className="caterpillar__grid" />
                  ))}
                  <line x1={x(lo)} x2={x(hi)} y1={11} y2={11} stroke={color} strokeWidth={3} strokeLinecap="round" />
                  <circle cx={x(s.rank!)} cy={11} r={5} fill={color} stroke="var(--sheet)" strokeWidth={2} />
                  {alt !== undefined && alt !== s.rank ? (
                    <path
                      d={`M${x(alt)},4 l5,7 l-5,7 l-5,-7 z`}
                      className="caterpillar__alt"
                      aria-hidden="true"
                    />
                  ) : null}
                </svg>
              </Link>
            </li>
          );
        })}
      </ol>
    </div>
  );
}
