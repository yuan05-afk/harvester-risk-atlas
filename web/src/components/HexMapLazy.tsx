import { lazy, Suspense, useEffect, useState, type ComponentProps } from "react";
import type { HexMap as HexMapType } from "./HexMap";

// MapLibre is the heaviest dependency; it loads after the page's text is on screen.
const HexMapInner = lazy(() => import("./HexMap").then((m) => ({ default: m.HexMap })));

/** Starts the map once the browser is idle, so headings and text paint first. */
function useIdle(timeout: number) {
  const [idle, setIdle] = useState(false);
  useEffect(() => {
    const go = () => setIdle(true);
    // Safari lacks requestIdleCallback; fall back to a short timer.
    const ric = (window as { requestIdleCallback?: (cb: () => void, o: { timeout: number }) => number }).requestIdleCallback;
    const id = ric ? ric(go, { timeout }) : window.setTimeout(go, 200);
    return () => (ric ? window.cancelIdleCallback(id) : window.clearTimeout(id));
  }, [timeout]);
  return idle;
}

export function HexMap(props: ComponentProps<typeof HexMapType>) {
  const idle = useIdle(1500);
  const loading = <div className="hexmap hexmap--loading" role="img" aria-label={`${props.label} (loading)`} />;
  return idle ? <Suspense fallback={loading}><HexMapInner {...props} /></Suspense> : loading;
}
