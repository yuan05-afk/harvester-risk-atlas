import { motion, useReducedMotion } from "motion/react";
import { useId } from "react";
import type { Tier } from "../data/schema";
import { TIER_LABEL, TIER_META } from "../lib/vocab";

/**
 * The priority stamp: a round, slightly worn rubber stamp in the tier's ink,
 * like the determination stamps on herbarium sheets. The ring carries the
 * tier in words; the centre carries the rank. Colour is never the only cue.
 */
export function Stamp({
  tier,
  rank,
  of,
  size = 96,
  animate = true,
  className = "",
}: {
  tier: Tier;
  rank: number | null;
  of?: number;
  size?: number;
  animate?: boolean;
  className?: string;
}) {
  const id = useId().replace(/:/g, "");
  const reduce = useReducedMotion();
  const label = TIER_LABEL[tier].toUpperCase();
  const ink = TIER_META[tier].color;
  const ranked = rank !== null;
  const r = Math.round(rank ?? 0);
  const desc = ranked ? `${TIER_LABEL[tier]}, ranked ${r}${of ? ` of ${of}` : ""}` : TIER_LABEL[tier];

  const svg = (
    <svg viewBox="0 0 120 120" width={size} height={size} role="img" aria-label={desc}>
      <defs>
        <filter id={`ink-${id}`} x="-10%" y="-10%" width="120%" height="120%">
          <feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="2" seed="7" result="n" />
          <feDisplacementMap in="SourceGraphic" in2="n" scale="1.6" result="d" />
          <feTurbulence type="fractalNoise" baseFrequency="0.35" numOctaves="1" seed="3" result="w" />
          <feColorMatrix in="w" type="matrix" values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 -2.2 1.65" result="wear" />
          <feComposite in="d" in2="wear" operator="in" />
        </filter>
        <path id={`ring-top-${id}`} d="M 18 60 A 42 42 0 0 1 102 60" />
        <path id={`ring-bottom-${id}`} d="M 14 60 A 46 46 0 0 0 106 60" />
      </defs>
      {/* The paper disc it is pressed onto, so the ink reads on photographs too. */}
      <circle className="stamp__paper" cx="60" cy="60" r="59.5" />
      <g filter={`url(#ink-${id})`} fill={ink} stroke={ink}>
        <circle cx="60" cy="60" r="56" fill="none" strokeWidth="3.2" />
        <circle cx="60" cy="60" r="49" fill="none" strokeWidth="1.2" />
        <text className="stamp__ring" stroke="none">
          <textPath href={`#ring-top-${id}`} startOffset="50%" textAnchor="middle">
            {label}
          </textPath>
        </text>
        <text className="stamp__ring stamp__ring--small" stroke="none">
          <textPath href={`#ring-bottom-${id}`} startOffset="50%" textAnchor="middle">
            HARVESTER RISK ATLAS
          </textPath>
        </text>
        {ranked ? (
          <>
            <text x="60" y="70" textAnchor="middle" className="stamp__rank" stroke="none">
              {r}
            </text>
            {of ? (
              <text x="60" y="86" textAnchor="middle" className="stamp__of" stroke="none">
                of {of}
              </text>
            ) : null}
          </>
        ) : (
          <line x1="44" x2="76" y1="62" y2="62" strokeWidth="3" strokeLinecap="round" />
        )}
      </g>
    </svg>
  );

  if (!animate || reduce) {
    return <span className={`stamp stamp--${TIER_META[tier].key} ${className}`}>{svg}</span>;
  }
  return (
    <motion.span
      className={`stamp stamp--${TIER_META[tier].key} ${className}`}
      initial={{ scale: 1.5, opacity: 0, rotate: -2 }}
      whileInView={{ scale: 1, opacity: 1, rotate: -8 }}
      viewport={{ once: true, margin: "-40px" }}
      transition={{ type: "spring", stiffness: 520, damping: 22, mass: 0.6 }}
    >
      {svg}
    </motion.span>
  );
}
