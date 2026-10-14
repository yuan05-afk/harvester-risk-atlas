import type { Component, SpeciesSummary, Tier } from "../data/schema";

/**
 * Reader-facing words. The data keeps its technical tier names; every screen
 * shows these instead.
 */
export const TIER_LABEL: Record<Tier, string> = {
  "High attention": "Needs attention now",
  Watch: "Keep watch",
  Lower: "Lower concern",
  "Not scored": "Not ranked",
};

export const TIER_META: Record<Tier, { color: string; key: string; blurb: string }> = {
  "High attention": {
    color: "var(--tier-high)",
    key: "high",
    blurb: "Almost certainly among the top quarter of plants needing care.",
  },
  Watch: {
    color: "var(--tier-watch)",
    key: "watch",
    blurb: "Often among the top quarter, but the evidence is less certain.",
  },
  Lower: {
    color: "var(--tier-lower)",
    key: "lower",
    blurb: "Rarely among the top quarter on current evidence.",
  },
  "Not scored": {
    color: "var(--tier-none)",
    key: "none",
    blurb: "Listed so you can look it up, but not ranked.",
  },
};

export const TIER_ORDER: Tier[] = ["High attention", "Watch", "Lower", "Not scored"];

export const COMPONENT_META: Record<
  Component,
  { label: string; short: string; color: string; question: string; scored: boolean }
> = {
  R: {
    label: "Rarity",
    short: "Rarity",
    color: "var(--c-range)",
    question: "How seldom it turns up where botanists have looked, and how small its native range is.",
    scored: true,
  },
  H: {
    label: "Harvest harm",
    short: "Harvest",
    color: "var(--c-harvest)",
    question: "Whether harvesting takes roots, bark or the whole plant, from a slow-growing plant taken from the wild.",
    scored: true,
  },
  E: {
    label: "Habitat pressure",
    short: "Habitat",
    color: "var(--c-habitat)",
    question: "Whether the places it grows are unprotected, in provinces losing forest.",
    scored: true,
  },
  C: {
    label: "Climate change",
    short: "Climate",
    color: "var(--c-climate)",
    question: "Projected warming where it grows. Shown, but not counted: it is about the same for every plant.",
    scored: false,
  },
};

export const SCORED_COMPONENTS = ["R", "H", "E"] as const;

/** Four plain steps for a 0–1 component value. */
export const LEVELS = ["Low", "Moderate", "High", "Very high"] as const;
export function level(v: number | null): { index: number; word: string } | null {
  if (v === null || !Number.isFinite(v)) return null;
  const index = Math.min(3, Math.floor(v * 4));
  return { index, word: LEVELS[index] };
}

export function ordinal(n: number): string {
  const s = ["th", "st", "nd", "rd"];
  const v = n % 100;
  return `${n}${s[(v - 20) % 10] || s[v] || s[0]}`;
}

/** "Ranked 2nd of 29. It could be anywhere from 1st to 5th." */
export function rankSentence(s: Pick<SpeciesSummary, "rank" | "rank_ci">, n: number): string {
  if (s.rank === null) return "Not ranked.";
  const r = Math.round(s.rank);
  const [lo, hi] = s.rank_ci;
  const base = `Ranked ${ordinal(r)} of ${n}.`;
  if (lo === null || hi === null || lo === hi) return base;
  return `${base} It could be anywhere from ${ordinal(lo)} to ${ordinal(hi)}.`;
}

export function gateReason(s: Pick<SpeciesSummary, "gate" | "ph_status">): string {
  if (s.gate === "insufficient_data") return "Too few records to rank";
  if (s.gate === "not_native") {
    if (s.ph_status === "introduced") return "Introduced to the Philippines";
    if (s.ph_status === "not_found") return "Name not found in the plant checklist";
    return "Not listed as native to the Philippines";
  }
  return "";
}

export function nativeLabel(s: Pick<SpeciesSummary, "ph_status" | "endemic">): string {
  if (s.ph_status === "native") return s.endemic ? "Found only in the Philippines" : "Native to the Philippines";
  if (s.ph_status === "introduced") return "Introduced";
  if (s.ph_status === "not_found") return "Not in the checklist";
  return "Not listed as native";
}

export const DAO_LABEL: Record<string, string> = {
  CR: "Critically endangered",
  EN: "Endangered",
  VU: "Vulnerable",
  OTS: "Other threatened species",
};

export const HABITAT_LABEL: Record<string, string> = {
  forest: "Forest",
  mixed: "Thickets and forest",
  open: "Open ground",
};

export const PART_LABEL: Record<string, string> = {
  whole_plant: "whole plant",
  underground: "roots or rhizome",
  bark: "bark",
  stem: "stems",
  seed_fruit: "seeds or fruit",
  exudate: "sap or resin",
  leaf_flower: "leaves or flowers",
};

/** A one-line reason for cards: the main driver in plain words. */
export function shortReason(s: SpeciesSummary): string {
  if (s.gate) return gateReason(s);
  const bits: string[] = [];
  const lv = (k: "R" | "H" | "E") => level(s.components[k]);
  if ((lv("R")?.index ?? 0) >= 2) bits.push("rarely found");
  if ((lv("H")?.index ?? 0) >= 3) bits.push("harvest takes roots or bark");
  else if ((lv("H")?.index ?? 0) >= 2) bits.push("harvest can harm it");
  if ((lv("E")?.index ?? 0) >= 2) bits.push("its habitat is under pressure");
  if (!bits.length) return "Common, cultivated or well protected";
  const text = bits.join(", ");
  return text.charAt(0).toUpperCase() + text.slice(1);
}
