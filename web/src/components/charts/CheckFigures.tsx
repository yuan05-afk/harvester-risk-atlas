/*
 * Small figures for the robustness ledger on How it works. Each draws the one
 * number its row reports, on a scale a reader can judge by eye. The row's text
 * states the same numbers, so the figures are hidden from assistive tech.
 */

const W = 300;
const X0 = 18;
const X1 = W - 18;

type Mark = { value: number; label: string; color?: string };

/** Agreement between two orderings (Spearman), on a 0.5 to 1 scale. */
export function AgreementScale({ marks }: { marks: Mark[] }) {
  const lo = 0.5;
  const x = (v: number) => X0 + ((Math.max(lo, Math.min(1, v)) - lo) / (1 - lo)) * (X1 - X0);
  const axisY = 52;
  return (
    <svg className="check-fig" viewBox={`0 0 ${W} 74`} aria-hidden="true" focusable="false">
      <defs>
        <pattern id="agree-hatch" width="4" height="4" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
          <path d="M0 0v4" stroke="var(--rule-strong)" strokeWidth="1" />
        </pattern>
      </defs>
      <rect x={x(0.9)} y={axisY - 7} width={x(1) - x(0.9)} height="14" fill="url(#agree-hatch)" />
      <line x1={X0} x2={X1} y1={axisY} y2={axisY} stroke="var(--ink)" strokeWidth="1" />
      {[0.5, 0.75, 1].map((v) => (
        <g key={v}>
          <line x1={x(v)} x2={x(v)} y1={axisY} y2={axisY + 4} stroke="var(--ink)" strokeWidth="1" />
          <text x={x(v)} y={axisY + 16} textAnchor={v === 1 ? "end" : v === 0.5 ? "start" : "middle"} className="check-fig__tick">
            {v === 1 ? "1 · same order" : v.toFixed(2).replace(/0$/, "")}
          </text>
        </g>
      ))}
      {/* Labels stack from the right: the rightmost mark takes the top row and every
          label ends at its own mark, so no leader line crosses another label. */}
      {[...marks].sort((a, b) => b.value - a.value).map((m, i) => {
        const cx = x(m.value);
        const ly = 12 + i * 13;
        const anchor = cx < X0 + 110 ? "start" : "end";
        return (
          <g key={m.label}>
            <line x1={cx} x2={cx} y1={ly + 3} y2={axisY - 6} stroke="var(--ink-3)" strokeWidth="0.8" />
            <circle cx={cx} cy={axisY} r="5" fill={m.color ?? "var(--ink)"} stroke="var(--sheet)" strokeWidth="1.5" />
            <text x={cx} y={ly} textAnchor={anchor} className="check-fig__label">
              {m.label} <tspan className="check-fig__value">{m.value.toFixed(2)}</tspan>
            </text>
          </g>
        );
      })}
    </svg>
  );
}

/** Where the listed plants sit among all ranks, against a chance average. */
export function RankStrip({ ranks, n }: { ranks: number[]; n: number }) {
  const x = (r: number) => X0 + ((r - 1) / (n - 1)) * (X1 - X0);
  const axisY = 46;
  const seen = new Map<number, number>();
  const mean = ranks.reduce((a, b) => a + b, 0) / ranks.length;
  const chance = (n + 1) / 2;
  return (
    <svg className="check-fig" viewBox={`0 0 ${W} 74`} aria-hidden="true" focusable="false">
      {Array.from({ length: n }, (_, i) => (
        <line key={i} x1={x(i + 1)} x2={x(i + 1)} y1={axisY - 3} y2={axisY + 3} stroke="var(--rule-strong)" strokeWidth="1" />
      ))}
      <line x1={X0} x2={X1} y1={axisY} y2={axisY} stroke="var(--ink)" strokeWidth="1" />
      <line x1={x(chance)} x2={x(chance)} y1={12} y2={axisY + 8} stroke="var(--ink-3)" strokeDasharray="3 3" />
      <text x={x(chance) + 4} y={14} className="check-fig__tick">
        chance {Math.round(chance)}
      </text>
      <line x1={x(mean)} x2={x(mean)} y1={12} y2={axisY + 8} stroke="var(--tier-high)" strokeWidth="1.4" />
      <text x={x(mean) - 4} y={14} textAnchor="end" className="check-fig__label">
        listed plants, on average {Math.round(mean)}
      </text>
      {ranks.map((r, i) => {
        const k = seen.get(r) ?? 0;
        seen.set(r, k + 1);
        return <circle key={i} cx={x(r)} cy={axisY - 9 - k * 9} r="4" fill="var(--tier-high)" stroke="var(--sheet)" strokeWidth="1.2" />;
      })}
      <text x={X0} y={axisY + 20} className="check-fig__tick">
        1st
      </text>
      <text x={X1} y={axisY + 20} textAnchor="end" className="check-fig__tick">
        {n}th
      </text>
    </svg>
  );
}

/** How wide a typical rank range is, drawn on the full list of ranks. */
export function IntervalGlyph({ width, n }: { width: number; n: number }) {
  const x = (r: number) => X0 + ((r - 1) / (n - 1)) * (X1 - X0);
  const axisY = 44;
  const mid = Math.round(n / 2);
  const lo = mid - width / 2;
  const hi = mid + width / 2;
  return (
    <svg className="check-fig" viewBox={`0 0 ${W} 74`} aria-hidden="true" focusable="false">
      <line x1={X0} x2={X1} y1={axisY} y2={axisY} stroke="var(--ink-3)" strokeWidth="1" />
      {Array.from({ length: n }, (_, i) => (
        <line key={i} x1={x(i + 1)} x2={x(i + 1)} y1={axisY - 2} y2={axisY + 2} stroke="var(--rule-strong)" strokeWidth="1" />
      ))}
      <line x1={x(lo)} x2={x(hi)} y1={axisY} y2={axisY} stroke="var(--ink)" strokeWidth="5" strokeLinecap="round" />
      <circle cx={x(mid)} cy={axisY} r="5.5" fill="var(--highlight)" stroke="var(--ink)" strokeWidth="1.5" />
      <path d={`M${x(lo)} 24v6M${x(lo)} 27H${x(hi)}M${x(hi)} 24v6`} stroke="var(--ink)" strokeWidth="1" fill="none" />
      <text x={x(mid)} y={18} textAnchor="middle" className="check-fig__label">
        about {width} places
      </text>
      <text x={X0} y={axisY + 20} className="check-fig__tick">
        1st
      </text>
      <text x={X1} y={axisY + 20} textAnchor="end" className="check-fig__tick">
        {n}th
      </text>
    </svg>
  );
}
