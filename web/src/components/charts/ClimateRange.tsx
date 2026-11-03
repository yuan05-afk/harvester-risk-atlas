import { scaleLinear } from "d3-scale";
import type { SpeciesSummary } from "../../data/schema";
import { fmtTemp } from "../../lib/format";
import { useWidth } from "../../lib/useWidth";

/**
 * Projected warming at the species' cells, 2041–2060 under SSP2-4.5: the five-model
 * median (dot) and range (bar), against the same range for every scored species.
 */
export function ClimateRange({ species, cohort }: { species: SpeciesSummary; cohort: SpeciesSummary[] }) {
  const [ref, width] = useWidth<HTMLDivElement>();
  const { dT, dT_range } = species.climate;
  if (dT === null) return <p className="empty-note">Too few cells to sample climate projections.</p>;
  const all = cohort.filter((s) => !s.gate && s.climate.dT !== null);
  const lo = Math.min(...all.map((s) => s.climate.dT_range[0] ?? 0));
  const hi = Math.max(...all.map((s) => s.climate.dT_range[1] ?? 0));
  const x = scaleLinear().domain([0, 3]).range([12, width - 12]);
  const h = 72;
  return (
    <div ref={ref}>
      <svg
        width={width}
        height={h}
        role="img"
        aria-label={`Warming ${fmtTemp(dT)}, models range ${fmtTemp(dT_range[0])} to ${fmtTemp(dT_range[1])}; all scored species ${fmtTemp(lo)} to ${fmtTemp(hi)}`}
      >
        <rect x={x(lo)} y={14} width={x(hi) - x(lo)} height={12} className="climate__cohort" rx={2} />
        <line x1={x(dT_range[0] ?? dT)} x2={x(dT_range[1] ?? dT)} y1={20} y2={20} className="climate__range" />
        <circle cx={x(dT)} cy={20} r={6} className="climate__dot" />
        <text x={x(dT)} y={42} textAnchor="middle" className="strips__value num">
          {fmtTemp(dT)}
        </text>
        {[0, 1, 2, 3].map((t) => (
          <text key={t} x={x(t)} y={64} textAnchor="middle" className="tick num">
            {t === 0 ? "0 °C" : `+${t}`}
          </text>
        ))}
      </svg>
      <p className="figure__note">
        Grey band: the range across every scored species. Dot: five-model median. Line: lowest to highest model.
      </p>
    </div>
  );
}
