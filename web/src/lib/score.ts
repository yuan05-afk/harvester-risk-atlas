/**
 * Score arithmetic for the weight explorer. Mirrors harvester_risk_atlas.index:
 * `normalize` clips negatives and rescales to 1 (defaults when all zero);
 * `aggregate` is a weighted mean over finite components with weights rescaled
 * over what is present. Ranks: 1 = highest, ties share the best rank ("min").
 * src/lib/score.test.ts checks this against a golden file from the pipeline.
 */
import type { Component } from "../data/schema";

export type Weights = Record<Component, number>;
export const KEYS: Component[] = ["R", "H", "E", "C"];
export const DEFAULT_WEIGHTS: Weights = { R: 1 / 3, H: 1 / 3, E: 1 / 3, C: 0 };

export function normalize(w: Partial<Weights> | null | undefined): Weights {
  const clipped = KEYS.map((k) => {
    const v = Number(w?.[k] ?? 0);
    return Number.isFinite(v) && v > 0 ? v : 0;
  });
  const total = clipped.reduce((a, b) => a + b, 0);
  if (total <= 0) return { ...DEFAULT_WEIGHTS };
  return Object.fromEntries(KEYS.map((k, i) => [k, clipped[i] / total])) as Weights;
}

export function aggregate(values: Record<Component, number | null>, weights: Weights): number | null {
  let num = 0;
  let den = 0;
  for (const k of KEYS) {
    const v = values[k];
    const w = weights[k];
    if (v !== null && Number.isFinite(v) && w > 0) {
      num += v * w;
      den += w;
    }
  }
  return den > 0 ? num / den : null;
}

export function ranks(scores: (number | null)[]): (number | null)[] {
  return scores.map((s) => {
    if (s === null) return null;
    return 1 + scores.filter((o) => o !== null && o > s).length;
  });
}

/** Slider weights as a URL value, "R,H,E,C" (e.g. "1,1,1,0"); null when they are the published ones. */
export function weightsToParam(w: Weights): string | null {
  const text = KEYS.map((k) => String(w[k])).join(",");
  return text === "1,1,1,0" ? null : text;
}

/** Inverse of weightsToParam. Anything malformed falls back to the published equal weights. */
export function weightsFromParam(p: string | null): Weights {
  const parts = (p ?? "").split(",");
  if (parts.length !== KEYS.length) return { R: 1, H: 1, E: 1, C: 0 };
  const nums = parts.map((x) => (x.trim() === "" ? NaN : Number(x)));
  if (nums.some((n) => !Number.isFinite(n) || n < 0 || n > 4)) return { R: 1, H: 1, E: 1, C: 0 };
  return Object.fromEntries(KEYS.map((k, i) => [k, Math.round(nums[i] * 4) / 4])) as Weights;
}
