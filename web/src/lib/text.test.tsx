import { readdirSync, readFileSync } from "node:fs";
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { MapTooltip } from "../components/MapTooltip";
import type { CellProps, SpeciesDetail, SpeciesSummary } from "../data/schema";
import { explain, summary } from "./explain";
import { level } from "./vocab";

const dir = "public/data/species";
const details: SpeciesDetail[] = readdirSync(dir).map((f) => JSON.parse(readFileSync(`${dir}/${f}`, "utf-8")));
const summaries: SpeciesSummary[] = JSON.parse(readFileSync("public/data/species.json", "utf-8"));

describe("vocab.level", () => {
  it("maps 0–1 to four plain steps", () => {
    expect(level(0)?.word).toBe("Low");
    expect(level(0.25)?.word).toBe("Moderate");
    expect(level(0.5)?.word).toBe("High");
    expect(level(0.99)?.word).toBe("Very high");
    expect(level(1)?.word).toBe("Very high");
  });
  it("returns null for missing values", () => {
    expect(level(null)).toBeNull();
    expect(level(NaN)).toBeNull();
  });
});

describe("explain / summary text", () => {
  it("covers all 51 species", () => expect(details.length).toBe(51));
  it.each(details.map((d) => [d.slug, d] as const))("%s has no undefined/NaN text", (_slug, d) => {
    const texts = [...Object.values(explain(d)), summary(d, 29)];
    for (const t of texts) {
      expect(t.length).toBeGreaterThan(0);
      expect(t).not.toMatch(/undefined|NaN|null|\[object/);
    }
  });
});

describe("MapTooltip counts", () => {
  const bySlug = new Map(summaries.map((s) => [s.slug, s]));
  const all = summaries.filter((s) => !s.gate);
  const ranked = [...all.filter((s) => s.tier !== "Lower").slice(0, 3), ...all.filter((s) => s.tier === "Lower").slice(0, 3)];
  const cell: CellProps = {
    h3: "x", effort: 12, pa: null, n_high: 0, n_watch: 0, n_lower: 0, n_cohort: 0,
    species: ranked.map((s) => s.slug),
  };
  const nPriority = ranked.filter((s) => s.tier === "High attention" || s.tier === "Watch").length;
  it("counts priority plants out of ranked plants", () => {
    render(<MapTooltip info={{ cell: { ...cell, n_high: nPriority }, x: 10, y: 10 }} bySlug={bySlug} mode="hotspots" width={1000} height={800} />);
    const head = document.querySelector(".map-tip__head")!;
    expect(head.textContent).toContain(`of the ${ranked.length} ranked plants here`);
    expect(head.querySelector("b")?.textContent).toBe(String(nPriority));
  });
  it("shows the survey count in effort mode and the empty state", () => {
    const { unmount } = render(<MapTooltip info={{ cell, x: 10, y: 10 }} bySlug={bySlug} mode="effort" width={1000} height={800} />);
    expect(screen.getByText(/plant records from botanists here/)).toBeTruthy();
    unmount();
    render(<MapTooltip info={{ cell: { ...cell, species: [] }, x: 10, y: 10 }} bySlug={bySlug} mode="hotspots" width={1000} height={800} />);
    expect(screen.getByText("No ranked plants recorded here")).toBeTruthy();
  });
});
