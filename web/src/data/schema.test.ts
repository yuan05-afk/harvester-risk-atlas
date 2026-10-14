import { readdirSync, readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import { SCHEMAS } from "./schema";

// Production does not validate at run time (see SCHEMAS), so this is the guard:
// every JSON file the pipeline writes must match what the app expects.
const read = (p: string) => JSON.parse(readFileSync(`public/data/${p}`, "utf-8"));
const check = (kind: keyof typeof SCHEMAS, p: string) => {
  const r = SCHEMAS[kind].safeParse(read(p));
  expect(r.success ? "ok" : `${p}: ${r.error.issues[0]?.path.join(".")} ${r.error.issues[0]?.message}`).toBe("ok");
};

describe("shipped data matches the schemas", () => {
  it("species list, manifest, validation", () => {
    check("speciesList", "species.json");
    check("manifest", "manifest.json");
    check("validation", "validation.json");
  });
  it("all 51 species files", () => {
    const files = readdirSync("public/data/species");
    expect(files.length).toBe(51);
    for (const f of files) check("species", `species/${f}`);
  });
  it("map layers", () => {
    check("cells", "geo/cells.geojson");
    check("cells", "geo/cells_r4.geojson");
    check("geo", "geo/land.geojson");
  });
});
