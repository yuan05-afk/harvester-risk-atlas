import type { ReactNode } from "react";
import { Link } from "react-router-dom";
import type { SpeciesSummary } from "../data/schema";
import { fmtInt } from "../lib/format";
import { COMPONENT_META, DAO_LABEL, gateReason, nativeLabel } from "../lib/vocab";
import { RankInterval } from "./RankInterval";
import { TierChip } from "./TierChip";

/**
 * A herbarium-style label: the binomial, its Filipino name, and typed fields.
 * Every field is data; nothing decorative.
 */
export function SpecimenLabel({
  s,
  nScored,
  link = true,
  headingLevel = 3,
  footer,
  compact = false,
}: {
  s: SpeciesSummary;
  nScored: number;
  link?: boolean;
  headingLevel?: 2 | 3;
  footer?: ReactNode;
  /** Short form for lists: name, tier, rank with interval, main driver. */
  compact?: boolean;
}) {
  const Heading = `h${headingLevel}` as const;
  const name = <i className="binomial">{s.name}</i>;
  if (compact) {
    const driver = s.driver ? COMPONENT_META[s.driver as "R" | "H" | "E"] : null;
    return (
      <article className={`specimen specimen--compact tier-edge tier-edge--${tierKey(s.tier)}`}>
        <Heading className="specimen__name">{link ? <Link to={`/species/${s.slug}`}>{name}</Link> : name}</Heading>
        {s.vernacular ? <p className="specimen__vern">{s.vernacular}</p> : null}
        {s.rank !== null ? (
          <div className="specimen__rank specimen__rank--compact">
            <span className="num">
              Rank {Math.round(s.rank)} of {nScored}, 90% interval {s.rank_ci[0]}–{s.rank_ci[1]}
            </span>
            <RankInterval rank={s.rank} ci={s.rank_ci} n={nScored} tier={s.tier} fluid />
          </div>
        ) : null}
        <p className="specimen__tags">
          {s.endemic ? <span>Endemic</span> : null}
          {s.dao ? <span>{DAO_LABEL[s.dao] ?? s.dao} (DENR)</span> : null}
          {driver ? <span>Driven by {driver.short.toLowerCase()}</span> : null}
        </p>
      </article>
    );
  }
  return (
    <article className={`specimen tier-edge tier-edge--${tierKey(s.tier)}`}>
      <Heading className="specimen__name">{link ? <Link to={`/species/${s.slug}`}>{name}</Link> : name}</Heading>
      {s.vernacular ? <p className="specimen__vern">{s.vernacular}</p> : null}
      <dl className="specimen__fields">
        <div>
          <dt>Family</dt>
          <dd>{s.family || "—"}</dd>
        </div>
        <div>
          <dt>Status</dt>
          <dd>{nativeLabel(s)}</dd>
        </div>
        {s.dao ? (
          <div>
            <dt>National list</dt>
            <dd>{DAO_LABEL[s.dao] ?? s.dao}</dd>
          </div>
        ) : null}
        <div>
          <dt>Records</dt>
          <dd className="num">
            {fmtInt(s.n_clean)} usable of {fmtInt(s.n_records)}
          </dd>
        </div>
        <div className="specimen__priority">
          <dt>Priority</dt>
          <dd>
            <TierChip tier={s.tier} reason={s.gate ? gateReason(s) : undefined} />
            {s.rank !== null ? (
              <span className="specimen__rank">
                <span className="num">
                  Rank {Math.round(s.rank)} of {nScored}
                </span>
                <RankInterval rank={s.rank} ci={s.rank_ci} n={nScored} tier={s.tier} width={132} />
                <span className="specimen__ci num">
                  90% interval {s.rank_ci[0]}–{s.rank_ci[1]}
                </span>
              </span>
            ) : null}
          </dd>
        </div>
      </dl>
      {footer}
    </article>
  );
}

export function tierKey(t: SpeciesSummary["tier"]): string {
  return t === "High attention" ? "high" : t === "Watch" ? "watch" : t === "Lower" ? "lower" : "none";
}
