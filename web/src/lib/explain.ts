import type { Component, SpeciesDetail } from "../data/schema";
import { fmtPct } from "./format";
import { HABITAT_LABEL, PART_LABEL } from "./vocab";

const LIFE_FORM: Record<string, string> = {
  tree: "a tree",
  palm: "a palm",
  liana: "a woody climber",
  shrub: "a shrub",
  fern: "a fern",
  herb: "a herb",
  herbaceous_vine: "a herbaceous vine",
};

/** One plain sentence per scored component, built only from the species' own evidence. */
export function explain(d: SpeciesDetail): Record<Exclude<Component, "C">, string> {
  const range = (() => {
    const bits: string[] = [];
    if (d.n_surveyed_ph > 0) {
      bits.push(
        `Recorded in ${d.n_cells_surveyed} of the ${d.n_surveyed_ph} well-surveyed grid cells in the Philippines (${fmtPct(
          d.reporting_rate,
        )})`,
      );
    }
    if (d.endemic) bits.push("found nowhere else in the world");
    else if (d.native_regions > 0)
      bits.push(`native to ${d.native_regions} region${d.native_regions === 1 ? "" : "s"} worldwide`);
    return bits.length ? `${bits.join("; ")}.` : "Range could not be measured.";
  })();

  const harvest = (() => {
    const t = d.traits;
    if (!t) return "No cited source on how it is harvested yet, so this part is not scored.";
    const destructive = t.part_classes.filter((p) => ["underground", "bark", "whole_plant"].includes(p));
    const parts = destructive.length
      ? `Harvest can take its ${[...new Set(destructive.map((p) => PART_LABEL[p]))].join(" and ")}`
      : `Harvest takes its ${[...new Set(t.part_classes.map((p) => PART_LABEL[p]))].slice(0, 2).join(" and ")}`;
    const form = LIFE_FORM[t.life_form] ?? t.life_form;
    const source = t.sourcing === "wild_only" ? "and supply comes from the wild" : "and it is also cultivated";
    return `${parts}; it is ${form}, ${source}.`;
  })();

  const habitat = (() => {
    const pa = d.pa_share === null ? null : `${fmtPct(d.pa_share)} of the area of its cells lies inside protected areas`;
    const habitatName = HABITAT_LABEL[d.habitat] ?? "";
    let forest = "";
    if (d.forest_loss_rate !== null && d.habitat && d.habitat !== "open") {
      forest = `its provinces lost ${fmtPct(d.forest_loss_rate)} of tree cover from 2001 to 2023`;
    } else if (d.habitat === "open") {
      forest = "it grows in open ground, so forest loss is not counted against it";
    }
    const parts = [pa, forest].filter(Boolean);
    const lead = habitatName ? `${habitatName} plant. ` : "";
    return parts.length ? `${lead}${capitalise(parts.join("; "))}.` : "Habitat exposure could not be measured.";
  })();

  return { R: range, H: harvest, E: habitat };
}

function capitalise(s: string) {
  return s.charAt(0).toUpperCase() + s.slice(1);
}
