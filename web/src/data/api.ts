import { useEffect, useState } from "react";
import type { Shapes } from "./schema";

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
export function load<K extends keyof Shapes>(path: string, kind: K): Promise<Shapes[K]> {
  const key = path;
  if (!cache.has(key)) {
    const p = fetch(BASE + path)
      .catch(() => {
        throw new DataError(`Could not reach ${path}. Check your connection and reload.`, "network");
      })
      .then(async (res) => {
        if (res.status === 404) throw new DataError(`${path} is not in this build.`, "missing");
        if (!res.ok) throw new DataError(`${path} returned ${res.status}.`, "network");
        // Hosts with an SPA fallback answer unknown files with index.html and a 200.
        if ((res.headers.get("content-type") ?? "").includes("text/html"))
          throw new DataError(`${path} is not in this build.`, "missing");
        const json: unknown = await res.json();
        if (import.meta.env.DEV) {
          const { SCHEMAS } = await import("./schema");
          const parsed = SCHEMAS[kind].safeParse(json);
          if (!parsed.success) {
            throw new DataError(`${path} does not match the expected format (${parsed.error.issues[0]?.path.join(".")}).`, "schema");
          }
        }
        return json as Shapes[K];
      });
    p.catch(() => cache.delete(key));
    cache.set(key, p);
  }
  return cache.get(key) as Promise<Shapes[K]>;
}

export type Loadable<T> = { status: "loading" } | { status: "ready"; data: T } | { status: "error"; error: DataError };

export function useData<K extends keyof Shapes>(path: string | null, kind: K): Loadable<Shapes[K]> {
  const [state, setState] = useState<Loadable<Shapes[K]>>({ status: "loading" });
  useEffect(() => {
    if (!path) return;
    let live = true;
    setState({ status: "loading" });
    load(path, kind).then(
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
  }, [path, kind]);
  return state;
}

export const useSpeciesList = () => useData("species.json", "speciesList");
export const useManifest = () => useData("manifest.json", "manifest");
export const useValidation = () => useData("validation.json", "validation");
export const useSpecies = (slug: string | undefined) => useData(slug ? `species/${slug}.json` : null, "species");

export function geoUrl(name: string): string {
  return `${BASE}geo/${name}`;
}

export const useCells = () => useData("geo/cells.geojson", "cells");
export const useCellsCoarse = () => useData("geo/cells_r4.geojson", "cells");
