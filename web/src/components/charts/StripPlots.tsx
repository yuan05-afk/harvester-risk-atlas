import { median } from "d3-array";
import { scaleLinear } from "d3-scale";
import { useState } from "react";
import type { SpeciesSummary } from "../../data/schema";
import { useWidth } from "../../lib/useWidth";
import { COMPONENT_META, SCORED_COMPONENTS } from "../../lib/vocab";

/**
 * One row per weighted component: every scored species as a faint dot on 0–1,
 * the cohort median as a tick, and the selected species as a large dot.
 */
export function StripPlots({ species, cohort }: { species: SpeciesSummary; cohort: SpeciesSummary[] }) {
  const [ref, width] = useWidth<HTMLDivElement>();
  const [hover, setHover] = useState<{ k: string; s: SpeciesSummary } | null>(null);
  const labelW = width < 520 ? 0 : 150;
  const x = scaleLinear().domain([0, 1]).range([labelW + 8, width - 12]);
  const rowH = width < 520 ? 58 : 44;
  const scored = cohort.filter((s) => !s.gate);

  return (
    <div ref={ref} className="strips">
      {SCORED_COMPONENTS.map((k) => {
        const meta = COMPONENT_META[k];
        const vals = scored.map((s) => s.components[k]).filter((v): v is number => v !== null);
        const med = median(vals) ?? 0;
        const mine = species.components[k];
        const top = width < 520 ? 22 : 10;
        return (
          <div key={k} className="strips__row">
            <svg
              width={width}
              height={rowH}
              role="img"
              aria-label={`${meta.label}: ${mine === null ? "not measured" : mine.toFixed(2)}; cohort median ${med.toFixed(2)}`}
            >
              {labelW === 0 ? (
                <text x={8} y={14} className="strips__label">
                  {meta.label}
                </text>
              ) : (
                <text x={0} y={top + 12} className="strips__label">
                  {meta.label}
                </text>
              )}
              <line x1={x(0)} x2={x(1)} y1={top + 8} y2={top + 8} className="strips__track" />
              <line x1={x(med)} x2={x(med)} y1={top} y2={top + 16} className="strips__median" />
              {scored.map((s) => {
                const v = s.components[k];
                if (v === null || s.slug === species.slug) return null;
                return (
                  <circle
                    key={s.slug}
                    cx={x(v)}
                    cy={top + 8}
                    r={4}
                    className="strips__dot"
                    onMouseEnter={() => setHover({ k, s })}
                    onMouseLeave={() => setHover(null)}
                  />
                );
              })}
              {mine !== null ? (
                <g>
                  <circle cx={x(mine)} cy={top + 8} r={7.5} fill={meta.color} stroke="var(--sheet)" strokeWidth={2} />
                  <text x={x(mine)} y={top + 32} textAnchor="middle" className="strips__value num">
                    {mine.toFixed(2)}
                  </text>
                </g>
              ) : (
                <text x={x(0.5)} y={top + 12} textAnchor="middle" className="strips__missing">
                  Not measured for this species
                </text>
              )}
              {hover && hover.k === k ? (
                <text x={x(hover.s.components[k] ?? 0)} y={top - 2} textAnchor="middle" className="strips__hover">
                  {hover.s.vernacular || hover.s.name} {hover.s.components[k]?.toFixed(2)}
                </text>
              ) : null}
            </svg>
          </div>
        );
      })}
      <p className="strips__key">
        <span className="strips__key-dot" aria-hidden="true" /> other scored species
        <span className="strips__key-tick" aria-hidden="true" /> cohort median
        <span>0 = lowest priority, 1 = highest</span>
      </p>
    </div>
  );
}
