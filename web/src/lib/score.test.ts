import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import type { Component } from "../data/schema";
import { aggregate, normalize, ranks, type Weights } from "./score";

type Parity = {
  components: Record<string, Record<Component, number | null>>;
  sets: { name: string; weights: Weights; ranks: Record<string, number | null> }[];
};
const parity: Parity = JSON.parse(readFileSync("public/data/parity.json", "utf-8"));

describe("score.ts matches the Python pipeline (golden parity.json)", () => {
  const slugs = Object.keys(parity.components);
  it("covers every scored plant and 3 weight sets", () => {
    expect(slugs.length).toBe(29);
    expect(parity.sets.length).toBe(3);
  });
  for (const set of parity.sets) {
    it(`reproduces weights and ranks: ${set.name}`, () => {
      const w = normalize(set.weights);
      for (const k of Object.keys(set.weights) as Component[]) expect(w[k]).toBeCloseTo(set.weights[k], 3);
      const r = ranks(slugs.map((s) => aggregate(parity.components[s], w)));
      expect(Object.fromEntries(slugs.map((s, i) => [s, r[i]]))).toEqual(set.ranks);
    });
  }
  it("falls back to defaults when all weights are zero or invalid", () => {
    expect(normalize({ R: 0, H: -1, E: NaN, C: 0 })).toEqual(normalize(parity.sets[0].weights));
  });
});
