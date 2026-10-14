import type { Component, SpeciesDetail } from "../data/schema";
import { fmtPct } from "./format";
import { PART_LABEL } from "./vocab";

const LIFE_FORM: Record<string, string> = {
  tree: "a slow-growing tree",
  palm: "a palm",
  liana: "a woody climber",
  shrub: "a shrub",
  fern: "a fern",
  herb: "a fast-growing herb",
  herbaceous_vine: "a fast-growing vine",
};

const unique = (xs: string[]) => [...new Set(xs)];
const list = (xs: string[]) => (xs.length < 2 ? xs.join("") : `${xs.slice(0, -1).join(", ")} and ${xs[xs.length - 1]}`);

/** One or two plain sentences per scored part, built only from the plant's own evidence. */
export function explain(d: SpeciesDetail): Record<Exclude<Component, "C">, string> {
  const rarity = (() => {
    const out: string[] = [];
    if (d.n_surveyed_ph > 0) {
      out.push(
        `Found in ${d.n_cells_surveyed} of the ${d.n_surveyed_ph} places botanists have searched well (${fmtPct(d.reporting_rate)}).`,
      );
    }
    if (d.endemic) out.push("It grows wild nowhere else on Earth.");
    else if (d.native_regions > 0)
      out.push(`It is native to ${d.native_regions} ${d.native_regions === 1 ? "region" : "regions"} of the world.`);
    return out.join(" ") || "Its range could not be measured.";
  })();

  const harvest = (() => {
    const t = d.traits;
    if (!t) return "No published source yet says how it is harvested, so this part is left out.";
    const harmful = unique(t.part_classes.filter((p) => ["underground", "bark", "whole_plant"].includes(p)).map((p) => PART_LABEL[p]));
    const parts = harmful.length
      ? `Harvesters take its ${list(harmful)}, which can kill or weaken the plant.`
      : `Harvesters take its ${list(unique(t.part_classes.map((p) => PART_LABEL[p])).slice(0, 2))}, which the plant can regrow.`;
    const form = LIFE_FORM[t.life_form] ?? t.life_form;
    const source = t.sourcing === "wild_only" ? "gathered from the wild rather than farmed" : "also grown in gardens and farms";
    return `${parts} It is ${form}, ${source}.`;
  })();

  const habitat = (() => {
    const out: string[] = [];
    if (d.pa_share !== null) out.push(`${fmtPct(d.pa_share)} of the area where it grows is protected.`);
    if (d.habitat === "open") out.push("It grows in open ground, so forest loss does not count against it.");
    else if (d.forest_loss_rate !== null) {
      out.push(`Forest in its provinces shrank by ${fmtPct(d.forest_loss_rate)} between 2001 and 2023.`);
    }
    return out.join(" ") || "Pressure on its habitat could not be measured.";
  })();

  return { R: rarity, H: harvest, E: habitat };
}

/** A one-paragraph summary for the top of a plant's page. */
export function summary(d: SpeciesDetail, nScored: number): string {
  const name = d.vernacular ? capitalise(d.vernacular.split(" / ")[0]) : d.name;
  if (d.gate === "not_native") {
    return `${name} is not ranked because it is not native to the Philippines. The atlas ranks native plants that are gathered from the wild.`;
  }
  if (d.gate === "insufficient_data") {
    return `${name} is not ranked: there are too few reliable records to place it fairly. That does not mean it is common or safe.`;
  }
  const tierWords: Record<string, string> = {
    "High attention": "one of the plants most in need of attention",
    Watch: "a plant to keep watching",
    Lower: "of lower concern than most",
  };
  return `${name} is ${tierWords[d.tier] ?? "ranked"} among the ${nScored} native medicinal plants in the atlas.`;
}

function capitalise(s: string) {
  return s.charAt(0).toUpperCase() + s.slice(1);
}
