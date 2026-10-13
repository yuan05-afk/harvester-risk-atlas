import type { Tier } from "../data/schema";

const KEY: Record<Tier, string> = {
  "High attention": "high",
  Watch: "watch",
  Lower: "lower",
  "Not scored": "none",
};

/** Tier swatch plus its name. Colour is never the only cue. */
export function TierChip({ tier, compact = false, reason }: { tier: Tier; compact?: boolean; reason?: string }) {
  return (
    <span className={`tier tier--${KEY[tier]}${compact ? " tier--compact" : ""}`}>
      <span className="tier__swatch" aria-hidden="true" />
      <span className="tier__name">{tier}</span>
      {reason ? <span className="tier__reason">{reason}</span> : null}
    </span>
  );
}
