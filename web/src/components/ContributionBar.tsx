import type { Component } from "../data/schema";
import type { Weights } from "../lib/score";
import { COMPONENT_META, SCORED_COMPONENTS } from "../lib/vocab";

/**
 * How much each weighted component adds to the score: segment width = weight × value,
 * on a 0–1 scale, with a 2 px sheet gap between segments and direct labels.
 * Missing components are listed, not drawn.
 */
export function ContributionBar({
  values,
  weights,
  width = 480,
  labels = true,
}: {
  values: Record<Component, number | null>;
  weights: Weights;
  width?: number;
  labels?: boolean;
}) {
  const present = SCORED_COMPONENTS.filter((k) => values[k] !== null && weights[k] > 0);
  const missing = SCORED_COMPONENTS.filter((k) => values[k] === null && weights[k] > 0);
  // Rescale weights over what is present, as the index does.
  const wSum = present.reduce((a, k) => a + weights[k], 0) || 1;
  const parts = present.map((k) => ({ k, v: ((values[k] as number) * weights[k]) / wSum }));
  const total = parts.reduce((a, p) => a + p.v, 0);
  const h = 18;
  const gap = 2;
  let x = 0;
  return (
    <figure className="contrib">
      <svg
        width="100%"
        viewBox={`0 0 ${width} ${h}`}
        preserveAspectRatio="none"
        role="img"
        aria-label={`Score ${total.toFixed(2)} of 1: ${parts
          .map((p) => `${COMPONENT_META[p.k].label} adds ${p.v.toFixed(2)}`)
          .join(", ")}`}
        className="contrib__svg"
      >
        <rect x={0} y={0} width={width} height={h} className="contrib__track" rx={4} />
        {parts.map((p) => {
          const w = Math.max(0, p.v * width - gap);
          const el = <rect key={p.k} x={x} y={0} width={w} height={h} fill={COMPONENT_META[p.k].color} rx={3} />;
          x += p.v * width;
          return el;
        })}
      </svg>
      {labels && (
        <figcaption className="contrib__legend">
          {parts.map((p) => (
            <span key={p.k} className="contrib__item">
              <span className="contrib__swatch" style={{ background: COMPONENT_META[p.k].color }} aria-hidden="true" />
              {COMPONENT_META[p.k].short} <b className="num">+{p.v.toFixed(2)}</b>
            </span>
          ))}
          {missing.map((k) => (
            <span key={k} className="contrib__item contrib__item--missing">
              {COMPONENT_META[k].short} not measured
            </span>
          ))}
          <span className="contrib__total">
            Score <b className="num">{total.toFixed(2)}</b>
          </span>
        </figcaption>
      )}
    </figure>
  );
}
