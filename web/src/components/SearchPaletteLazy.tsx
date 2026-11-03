import { lazy, Suspense, useState } from "react";

const Palette = lazy(() => import("./SearchPalette").then((m) => ({ default: m.SearchPalette })));

/**
 * The search palette, fetched the first time it is opened so its dialog and
 * fuzzy-search code stay out of the first page load.
 */
export function SearchPalette({ open, onOpenChange }: { open: boolean; onOpenChange: (o: boolean) => void }) {
  const [wanted, setWanted] = useState(open);
  if (open && !wanted) setWanted(true);
  if (!wanted) return null;
  return (
    <Suspense fallback={null}>
      <Palette open={open} onOpenChange={onOpenChange} />
    </Suspense>
  );
}
