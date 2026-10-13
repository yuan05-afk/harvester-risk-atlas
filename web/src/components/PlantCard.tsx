import { motion } from "motion/react";
import { Link } from "react-router-dom";
import type { SpeciesSummary } from "../data/schema";
import { shortReason, TIER_LABEL, TIER_META } from "../lib/vocab";
import { PlantPhoto } from "./PlantPhoto";
import { Stamp } from "./Stamp";

/**
 * A plant as a small herbarium sheet: photograph, the priority stamp pressed
 * onto its corner, names, and one plain reason. The whole card is the link.
 */
export function PlantCard({
  s,
  nScored,
  size = "regular",
  onHover,
}: {
  s: SpeciesSummary;
  nScored: number;
  size?: "regular" | "large";
  onHover?: (slug: string | null) => void;
}) {
  return (
    <motion.article
      className={`plant-card plant-card--${size}`}
      whileHover={{ y: -4 }}
      transition={{ type: "spring", stiffness: 400, damping: 30 }}
      onMouseEnter={() => onHover?.(s.slug)}
      onMouseLeave={() => onHover?.(null)}
    >
      <Link to={`/species/${s.slug}`} className="plant-card__link">
        <div className="plant-card__media">
          <PlantPhoto s={s} credit="none" decorative />
          <Stamp tier={s.tier} rank={s.rank} of={s.rank !== null ? nScored : undefined} size={size === "large" ? 92 : 74} className="plant-card__stamp" />
        </div>
        <div className="plant-card__text">
          <h3 className="plant-card__name">
            <span className="plant-card__vern">{s.vernacular || <i className="binomial">{s.name}</i>}</span>
            {s.vernacular ? <i className="binomial plant-card__sci">{s.name}</i> : null}
          </h3>
          <p className="plant-card__reason">{shortReason(s)}</p>
        </div>
      </Link>
    </motion.article>
  );
}

/** A slim list row with a thumbnail, used in the atlas panel and search. */
export function PlantRow({
  s,
  active = false,
  showTier = true,
  onSelect,
  onHover,
}: {
  s: SpeciesSummary;
  active?: boolean;
  /** Off in lists already grouped under a tier heading. */
  showTier?: boolean;
  onSelect: (slug: string) => void;
  onHover?: (slug: string | null) => void;
}) {
  return (
    <button
      type="button"
      className={`plant-row${active ? " is-active" : ""}`}
      onClick={() => onSelect(s.slug)}
      onMouseEnter={() => onHover?.(s.slug)}
      onMouseLeave={() => onHover?.(null)}
      onFocus={() => onHover?.(s.slug)}
      onBlur={() => onHover?.(null)}
    >
      <PlantPhoto s={s} credit="none" ratio="1 / 1" className="plant-row__thumb" decorative />
      <span className="plant-row__names">
        <span className="plant-row__vern">{s.vernacular || s.name}</span>
        <i className="binomial plant-row__sci">{s.name}</i>
      </span>
      {showTier ? (
        <span className="plant-row__tier">
          <span className={`dot dot--${TIER_META[s.tier].key}`} aria-hidden="true" />
          <span>{TIER_LABEL[s.tier]}</span>
          {s.rank !== null ? <span className="plant-row__rank num">No. {Math.round(s.rank)}</span> : null}
        </span>
      ) : s.rank !== null ? (
        <span className="plant-row__rank plant-row__rank--solo num">No. {Math.round(s.rank)}</span>
      ) : null}
    </button>
  );
}
