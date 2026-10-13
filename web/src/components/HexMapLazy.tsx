import { lazy, Suspense, type ComponentProps } from "react";
import type { HexMap as HexMapType } from "./HexMap";

// MapLibre is the heaviest dependency; it loads after the page's text is on screen.
const HexMapInner = lazy(() => import("./HexMap").then((m) => ({ default: m.HexMap })));

export function HexMap(props: ComponentProps<typeof HexMapType>) {
  return (
    <Suspense fallback={<div className="hexmap hexmap--loading" role="img" aria-label={`${props.label} (loading)`} />}>
      <HexMapInner {...props} />
    </Suspense>
  );
}
