import { useEffect, useState } from "react";
import { z } from "zod";
import { CellProps, Manifest, SpeciesDetail, SpeciesSummary, Validation } from "./schema";

const BASE = `${import.meta.env.BASE_URL}data/`;

export class DataError extends Error {
  constructor(
    message: string,
    readonly kind: "network" | "missing" | "schema",
  ) {
    super(message);
  }
}

const cache = new Map<string, Promise<unknown>>();

/** Fetch a JSON file once per session and validate it against its schema. */
export function load<T>(path: string, schema: z.ZodType<T>): Promise<T> {
  const key = path;
  if (!cache.has(key)) {
    const p = fetch(BASE + path)
      .catch(() => {
        throw new DataError(`Could not reach ${path}. Check your connection and reload.`, "network");
      })
      .then(async (res) => {
        if (res.status === 404) throw new DataError(`${path} is not in this build.`, "missing");
        if (!res.ok) throw new DataError(`${path} returned ${res.status}.`, "network");
        const parsed = schema.safeParse(await res.json());
        if (!parsed.success) {
          throw new DataError(`${path} does not match the expected format (${parsed.error.issues[0]?.path.join(".")}).`, "schema");
        }
        return parsed.data;
      });
    p.catch(() => cache.delete(key));
    cache.set(key, p);
  }
  return cache.get(key) as Promise<T>;
}

export type Loadable<T> = { status: "loading" } | { status: "ready"; data: T } | { status: "error"; error: DataError };

export function useData<T>(path: string | null, schema: z.ZodType<T>): Loadable<T> {
  const [state, setState] = useState<Loadable<T>>({ status: "loading" });
  useEffect(() => {
    if (!path) return;
    let live = true;
    setState({ status: "loading" });
    load(path, schema).then(
      (data) => live && setState({ status: "ready", data }),
      (error: unknown) =>
        live &&
        setState({
          status: "error",
          error: error instanceof DataError ? error : new DataError(String(error), "network"),
        }),
    );
    return () => {
      live = false;
    };
  }, [path, schema]);
  return state;
}

const SpeciesList = z.array(SpeciesSummary);

export const useSpeciesList = () => useData("species.json", SpeciesList);
export const useManifest = () => useData("manifest.json", Manifest);
export const useValidation = () => useData("validation.json", Validation);
export const useSpecies = (slug: string | undefined) =>
  useData(slug ? `species/${slug}.json` : null, SpeciesDetail);

export function geoUrl(name: string): string {
  return `${BASE}geo/${name}`;
}

const CellCollection = z.object({
  type: z.literal("FeatureCollection"),
  features: z.array(z.object({ id: z.string(), properties: CellProps })),
});
export const useCells = () => useData("geo/cells.geojson", CellCollection);
export const useCellsCoarse = () => useData("geo/cells_r4.geojson", CellCollection);
