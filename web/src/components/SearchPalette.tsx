import * as Dialog from "@radix-ui/react-dialog";
import Fuse from "fuse.js";
import { Search } from "lucide-react";
import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useSpeciesList } from "../data/api";
import type { SpeciesSummary } from "../data/schema";
import { TIER_LABEL, TIER_META } from "../lib/vocab";
import { PlantPhoto } from "./PlantPhoto";

/** Find a plant by scientific name, Filipino name or family. Opens with "/" or Ctrl/⌘ K. */
export function SearchPalette({ open, onOpenChange }: { open: boolean; onOpenChange: (o: boolean) => void }) {
  const list = useSpeciesList();
  const [query, setQuery] = useState("");
  const [active, setActive] = useState(0);
  const navigate = useNavigate();

  const fuse = useMemo(
    () =>
      list.status === "ready"
        ? new Fuse(list.data, {
            keys: [
              { name: "name", weight: 2 },
              { name: "vernacular", weight: 2 },
              { name: "family", weight: 0.5 },
            ],
            threshold: 0.35,
            ignoreLocation: true,
          })
        : null,
    [list],
  );

  const results: SpeciesSummary[] = useMemo(() => {
    if (list.status !== "ready") return [];
    if (!query.trim()) return list.data.filter((s) => s.tier === "High attention" || s.tier === "Watch");
    return fuse ? fuse.search(query).slice(0, 8).map((r) => r.item) : [];
  }, [query, fuse, list]);

  const go = (s: SpeciesSummary) => {
    onOpenChange(false);
    setQuery("");
    navigate(`/species/${s.slug}`);
  };

  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay className="palette__overlay" />
        <Dialog.Content className="palette" aria-describedby={undefined}>
          <Dialog.Title className="sr-only">Find a plant</Dialog.Title>
          <div className="palette__field">
            <Search size={18} aria-hidden="true" />
            <input
              autoFocus
              className="palette__input"
              placeholder="Scientific or Filipino name, e.g. kalingag"
              value={query}
              role="combobox"
              aria-expanded="true"
              aria-controls="palette-results"
              aria-activedescendant={results[active] ? `opt-${results[active].slug}` : undefined}
              onChange={(e) => {
                setQuery(e.target.value);
                setActive(0);
              }}
              onKeyDown={(e) => {
                if (e.key === "ArrowDown") {
                  e.preventDefault();
                  setActive((a) => Math.min(a + 1, results.length - 1));
                } else if (e.key === "ArrowUp") {
                  e.preventDefault();
                  setActive((a) => Math.max(a - 1, 0));
                } else if (e.key === "Enter" && results[active]) {
                  go(results[active]);
                }
              }}
            />
          </div>
          <p className="palette__hint">{query.trim() ? `${results.length} ${results.length === 1 ? "match" : "matches"}` : "Plants that need attention or watching"}</p>
          <ul id="palette-results" role="listbox" className="palette__list">
            {results.map((s, i) => (
              <li
                key={s.slug}
                id={`opt-${s.slug}`}
                role="option"
                aria-selected={i === active}
                className={`palette__item${i === active ? " is-active" : ""}`}
                onMouseEnter={() => setActive(i)}
                onClick={() => go(s)}
              >
                <PlantPhoto s={s} ratio="1 / 1" credit="none" className="palette__thumb" />
                <span className="palette__names">
                  <span className="palette__vern">{s.vernacular || s.name}</span>
                  <i className="binomial">{s.name}</i>
                </span>
                <span className="palette__tier">
                  <span className={`dot dot--${TIER_META[s.tier].key}`} aria-hidden="true" />
                  {TIER_LABEL[s.tier]}
                </span>
              </li>
            ))}
            {query.trim() && results.length === 0 && (
              <li className="palette__empty">
                No plant in the atlas matches “{query}”. Try a Filipino name, or browse the{" "}
                <a
                  href="#"
                  onClick={(e) => {
                    e.preventDefault();
                    onOpenChange(false);
                    navigate("/plants");
                  }}
                >
                  full list
                </a>
                .
              </li>
            )}
          </ul>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
