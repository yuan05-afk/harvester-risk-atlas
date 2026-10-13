import type { Component, SpeciesSummary, Tier } from "../data/schema";

export const COMPONENT_META: Record<Component, { label: string; short: string; color: string; question: string }> = {
  R: {
    label: "Range restriction",
    short: "Range",
    color: "var(--c-range)",
    question: "How rarely is it found, where botanists have looked, and how small is its native range?",
  },
  H: {
    label: "Harvest sensitivity",
    short: "Harvest",
    color: "var(--c-harvest)",
    question: "Does harvesting take roots, bark or the whole plant, from a slow-growing plant, mostly from the wild?",
  },
  E: {
    label: "Habitat exposure",
    short: "Habitat",
    color: "var(--c-habitat)",
    question: "Do the places it grows lie outside protected areas, in provinces losing forest?",
  },
  C: {
    label: "Climate exposure",
    short: "Climate",
    color: "var(--c-climate)",
    question: "Will its current places warm past the warmest it now occupies? Reported, not weighted.",
  },
};

export const SCORED_COMPONENTS = ["R", "H", "E"] as const;

export const TIER_META: Record<Tier, { color: string; blurb: string }> = {
  "High attention": {
    color: "var(--tier-high)",
    blurb: "Ranks in the top quarter in at least 80% of simulations.",
  },
  Watch: {
    color: "var(--tier-watch)",
    blurb: "Ranks in the top quarter in 30–80% of simulations.",
  },
  Lower: {
    color: "var(--tier-lower)",
    blurb: "Rarely ranks in the top quarter.",
  },
  "Not scored": {
    color: "var(--tier-none)",
    blurb: "Shown for reference; not ranked.",
  },
};

export const TIER_ORDER: Tier[] = ["High attention", "Watch", "Lower", "Not scored"];

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
  if (s.ph_status === "native") return s.endemic ? "Endemic to the Philippines" : "Native to the Philippines";
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
