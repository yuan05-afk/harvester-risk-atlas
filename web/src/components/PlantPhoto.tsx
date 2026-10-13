import { useState } from "react";
import type { SpeciesSummary } from "../data/schema";

const BASE = import.meta.env.BASE_URL;

/**
 * A plant photograph, mounted like a print on a herbarium sheet, with its
 * credit. Plants without an openly licensed photo get a drawn placeholder.
 */
export function PlantPhoto({
  s,
  ratio = "4 / 3",
  credit = "hover",
  className = "",
  eager = false,
  decorative = false,
}: {
  s: Pick<SpeciesSummary, "name" | "vernacular" | "photo">;
  ratio?: string;
  credit?: "hover" | "below" | "none";
  className?: string;
  eager?: boolean;
  /** True when the names are already written next to the photo (cards, rows). */
  decorative?: boolean;
}) {
  const [failed, setFailed] = useState(false);
  const p = s.photo;
  return (
    <figure className={`plant-photo plant-photo--credit-${credit} ${className}`} style={{ aspectRatio: ratio }}>
      {p && !failed ? (
        <img
          src={`${BASE}${p.src}`}
          alt={decorative ? "" : `${s.vernacular || s.name} (${s.name})`}
          loading={eager ? "eager" : "lazy"}
          decoding="async"
          onError={() => setFailed(true)}
        />
      ) : (
        <div className="plant-photo__placeholder" aria-hidden="true">
          <svg viewBox="0 0 64 64" width="44" height="44">
            <path
              d="M32 54c-9-4-13-14-10-24 2-7 6-12 10-16 4 4 8 10 10 16 3 10-1 20-10 24z"
              fill="var(--highlight)"
              stroke="var(--ink)"
              strokeWidth="2"
            />
            <path d="M32 54V22" stroke="var(--ink)" strokeWidth="2" strokeLinecap="round" />
          </svg>
          <span>No open photo yet</span>
        </div>
      )}
      {p && !failed && credit !== "none" ? (
        <figcaption className="plant-photo__credit">
          <a href={p.page} target="_blank" rel="noreferrer">
            {p.creator || "iNaturalist observer"}
          </a>
          , {p.licence}, via iNaturalist
        </figcaption>
      ) : null}
    </figure>
  );
}
