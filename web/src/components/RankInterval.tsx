import type { Tier } from "../data/schema";
import { TIER_META } from "../lib/vocab";

/**
 * Median rank (dot) and 90% interval (line) on a 1..n axis, rank 1 at the left.
 * The same glyph appears in labels, tables and the caterpillar chart.
 */
export function RankInterval({
  rank,
  ci,
  n,
  tier,
  width = 160,
  showAxis = false,
  fluid = false,
}: {
  rank: number | null;
  ci: [number | null, number | null];
  n: number;
  tier: Tier;
  width?: number;
  showAxis?: boolean;
  /** Stretch to the container width (the glyph keeps its proportions). */
  fluid?: boolean;
}) {
  if (rank === null || n < 2) return null;
  const pad = 6;
  const h = showAxis ? 30 : 14;
  const x = (r: number) => pad + ((r - 1) / (n - 1)) * (width - 2 * pad);
  const [lo, hi] = [ci[0] ?? rank, ci[1] ?? rank];
  const color = TIER_META[tier].color;
  return (
    <svg
      className="rank-interval"
      width={fluid ? "100%" : width}
      height={h}
      viewBox={`0 0 ${width} ${h}`}
      preserveAspectRatio="xMinYMid meet"
      role="img"
      aria-label={`Rank ${Math.round(rank)} of ${n}; 90% interval ${lo} to ${hi}`}
    >
      <line x1={pad} x2={width - pad} y1={7} y2={7} className="rank-interval__track" />
      <line x1={x(lo)} x2={x(hi)} y1={7} y2={7} stroke={color} strokeWidth={3} strokeLinecap="round" />
      <circle cx={x(rank)} cy={7} r={4.5} fill={color} stroke="var(--sheet)" strokeWidth={2} />
      {showAxis && (
        <g className="rank-interval__axis">
          <text x={pad} y={26} textAnchor="start">
            Rank 1
          </text>
          <text x={width - pad} y={26} textAnchor="end">
            {n}
          </text>
        </g>
      )}
    </svg>
  );
}
