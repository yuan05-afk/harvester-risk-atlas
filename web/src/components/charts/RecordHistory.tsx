import { max } from "d3-array";
import { scaleBand, scaleLinear } from "d3-scale";
import { useState } from "react";
import type { SpeciesDetail } from "../../data/schema";
import { useWidth } from "../../lib/useWidth";

export const RECORD_KINDS = [
  { key: "specimen", label: "Herbarium specimens", color: "var(--rec-specimen)" },
  { key: "literature", label: "Literature citations", color: "var(--rec-literature)" },
  { key: "observation", label: "Field observations", color: "var(--rec-observation)" },
  { key: "other", label: "Other", color: "var(--rec-other)" },
] as const;

/**
 * GBIF records per decade, stacked by who made them. Herbarium specimens dominate
 * early decades and phone observations recent ones, which is why a falling count
 * of specimens is not evidence of decline.
 */
export function RecordHistory({ history }: { history: SpeciesDetail["history"] }) {
  const [ref, width] = useWidth<HTMLDivElement>();
  const [hover, setHover] = useState<number | null>(null);
  if (history.length === 0) {
    return <p className="empty-note">None of this species' records carry a year.</p>;
  }
  const h = 180;
  const m = { top: 12, right: 8, bottom: 26, left: 34 };
  const decades = history.map((d) => d.decade);
  const x = scaleBand<number>()
    .domain(decades)
    .range([m.left, width - m.right])
    .paddingInner(0.25);
  const totals = history.map((d) => d.specimen + d.literature + d.observation + d.other);
  const y = scaleLinear()
    .domain([0, max(totals) ?? 1])
    .nice()
    .range([h - m.bottom, m.top]);
  const labelEvery = Math.ceil(decades.length / Math.max(1, Math.floor(width / 56)));

  return (
    <div ref={ref} className="history">
      <svg width={width} height={h} role="img" aria-label="Records per decade by record type; see the table view for values">
        {y.ticks(4).map((t) => (
          <g key={t}>
            <line x1={m.left} x2={width - m.right} y1={y(t)} y2={y(t)} className="grid" />
            <text x={m.left - 6} y={y(t) + 4} textAnchor="end" className="tick num">
              {t}
            </text>
          </g>
        ))}
        {history.map((d, i) => {
          let y0 = y(0);
          return (
            <g
              key={d.decade}
              onMouseEnter={() => setHover(i)}
              onMouseLeave={() => setHover(null)}
              opacity={hover === null || hover === i ? 1 : 0.55}
            >
              <rect x={x(d.decade)} y={m.top} width={x.bandwidth()} height={h - m.top - m.bottom} fill="transparent" />
              {RECORD_KINDS.map((k) => {
                const v = d[k.key];
                if (!v) return null;
                const top = y(y.invert(y0) + v);
                const rect = (
                  <rect
                    key={k.key}
                    x={x(d.decade)}
                    y={top}
                    width={x.bandwidth()}
                    height={Math.max(0, y0 - top - 2)}
                    fill={k.color}
                    rx={2}
                  />
                );
                y0 = top;
                return rect;
              })}
              {i % labelEvery === 0 ? (
                <text x={(x(d.decade) ?? 0) + x.bandwidth() / 2} y={h - 8} textAnchor="middle" className="tick num">
                  {d.decade}s
                </text>
              ) : null}
            </g>
          );
        })}
      </svg>
      <div className="history__foot">
        <ul className="legend">
          {RECORD_KINDS.filter((k) => history.some((d) => d[k.key] > 0)).map((k) => (
            <li key={k.key}>
              <span className="legend__swatch" style={{ background: k.color }} aria-hidden="true" />
              {k.label}
            </li>
          ))}
        </ul>
        <p className="history__readout num" aria-live="polite">
          {hover !== null
            ? `${history[hover].decade}s: ${totals[hover]} records (${history[hover].specimen} specimens, ${history[hover].literature} citations, ${history[hover].observation} observations)`
            : "Hover or tap a decade for counts."}
        </p>
      </div>
    </div>
  );
}

export function RecordHistoryTable({ history }: { history: SpeciesDetail["history"] }) {
  return (
    <table className="data-table">
      <thead>
        <tr>
          <th scope="col">Decade</th>
          {RECORD_KINDS.map((k) => (
            <th scope="col" key={k.key} className="num">
              {k.label}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {history.map((d) => (
          <tr key={d.decade}>
            <th scope="row">{d.decade}s</th>
            {RECORD_KINDS.map((k) => (
              <td key={k.key} className="num">
                {d[k.key]}
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
}
