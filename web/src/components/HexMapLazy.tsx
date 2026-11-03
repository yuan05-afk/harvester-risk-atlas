import { lazy, Suspense, useEffect, useRef, useState, type ComponentProps } from "react";
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

/** True once the element comes within a screen of the viewport (e.g. a map below the fold on a phone). */
function useNearView<T extends Element>() {
  const ref = useRef<T>(null);
  const [near, setNear] = useState(false);
  useEffect(() => {
    const el = ref.current;
    if (!el || near) return;
    if (!("IntersectionObserver" in window)) return setNear(true);
    const io = new IntersectionObserver(([e]) => e.isIntersecting && setNear(true), { rootMargin: "100% 0px" });
    io.observe(el);
    return () => io.disconnect();
  }, [near]);
  return [ref, near] as const;
}

export function HexMap(props: ComponentProps<typeof HexMapType>) {
  const idle = useIdle(1500);
  const [ref, near] = useNearView<HTMLDivElement>();
  const loading = <div ref={ref} className="hexmap hexmap--loading" role="img" aria-label={`${props.label} (loading)`} />;
  return idle && near ? <Suspense fallback={loading}><HexMapInner {...props} /></Suspense> : loading;
}
