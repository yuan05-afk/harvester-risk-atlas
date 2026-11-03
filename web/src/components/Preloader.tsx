import { AnimatePresence, motion } from "motion/react";
import { useEffect, useMemo, useState } from "react";
import markSvg from "../assets/mark.svg?raw";

const SESSION_KEY = "hra-intro-seen";
const BASE = import.meta.env.BASE_URL;

// The mark is drawn in its own projection (see app/landing.py): x = (lon − 116.3)·15.4,
// y = (19.15 − lat)·15.4. Hexagons placed with the same formula sit on the islands.
const px = (lon: number) => (lon - 116.3) * 15.4;
const py = (lat: number) => (19.15 - lat) * 15.4;
const HEX_R = 3.7;
const hexPath = (cx: number, cy: number) =>
  Array.from({ length: 6 }, (_, i) => {
    const a = (Math.PI / 3) * i + Math.PI / 6;
    return `${i ? "L" : "M"}${(cx + HEX_R * Math.cos(a)).toFixed(1)},${(cy + HEX_R * Math.sin(a)).toFixed(1)}`;
  }).join("") + "Z";
const HEX_FILL = ["var(--tier-lower)", "var(--hot-1)", "var(--hot-2)", "var(--hot-3)", "var(--hot-4)"];

/** Inner paths of the mark SVG, without its outer <svg> wrapper. */
const MARK_INNER = markSvg.replace(/^<svg[^>]*>/, "").replace(/<\/svg>\s*$/, "");

/**
 * The pre-rendered Overview is on screen before the app starts. On a slow
 * connection the visitor is already reading it by then, so the intro would
 * interrupt rather than introduce: skip it (and count it as seen).
 */
const LATE_START_MS = 1500;

export function shouldPlayIntro(): boolean {
  if (typeof window === "undefined") return false;
  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return false;
  try {
    if (sessionStorage.getItem(SESSION_KEY) === "1") return false;
  } catch {
    return true;
  }
  if (document.getElementById("root")?.dataset.prerendered !== undefined && performance.now() > LATE_START_MS) {
    markSeen();
    return false;
  }
  return true;
}

function markSeen() {
  try {
    sessionStorage.setItem(SESSION_KEY, "1");
  } catch {
    /* private mode: the intro may play again next visit, which is harmless */
  }
}

/**
 * The opening: the archipelago draws itself, the hexagons where priority plants
 * were recorded bloom north to south, then the question appears and the sheet
 * lifts to reveal the page. About three seconds; Skip or Esc ends it at once.
 */
export function Preloader({ onDone }: { onDone: () => void }) {
  const [points, setPoints] = useState<[number, number, number][]>([]);
  const [open, setOpen] = useState(true);

  useEffect(() => {
    fetch(`${BASE}data/geo/hex_points.json`)
      .then((r) => (r.ok ? r.json() : []))
      .then(setPoints)
      .catch(() => setPoints([]));
  }, []);

  useEffect(() => {
    const finish = window.setTimeout(() => setOpen(false), 3600);
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && setOpen(false);
    window.addEventListener("keydown", onKey);
    document.documentElement.style.overflow = "hidden";
    return () => {
      window.clearTimeout(finish);
      window.removeEventListener("keydown", onKey);
      document.documentElement.style.overflow = "";
    };
  }, []);

  const hexes = useMemo(() => {
    const lats = points.map((p) => p[1]);
    const north = Math.max(...lats, 21);
    const south = Math.min(...lats, 4.5);
    return points.map(([lon, lat, pri]) => ({
      d: hexPath(px(lon), py(lat)),
      fill: HEX_FILL[Math.min(4, pri)],
      // North to south, with a little scatter so it reads as growth, not a wipe.
      delay: 1.0 + ((north - lat) / (north - south)) * 1.0 + ((lon * 7.3) % 1) * 0.12,
    }));
  }, [points]);

  return (
    <AnimatePresence
      onExitComplete={() => {
        markSeen();
        onDone();
      }}
    >
      {open ? (
        <motion.div
          className="intro"
          role="dialog"
          aria-modal="true"
          aria-label="Harvester Risk Atlas introduction"
          // Fades in over the pre-rendered page rather than snapping over it.
          initial={{ opacity: 0 }}
          animate={{ opacity: 1, transition: { duration: 0.25 } }}
          exit={{ clipPath: "inset(0 0 100% 0)", transition: { duration: 0.7, ease: [0.7, 0, 0.2, 1] } }}
        >
          <div className="intro__stage">
            <svg className="intro__map" viewBox="0 -36 236 268" aria-hidden="true">
              <g className="intro__mark" dangerouslySetInnerHTML={{ __html: MARK_INNER }} />
              <g>
                {/* ~260 hexagons: CSS animations, so the bloom runs off the main thread. */}
                {hexes.map((h, i) => (
                  <path
                    key={i}
                    className="intro__hex"
                    d={h.d}
                    fill={h.fill}
                    stroke="var(--paper)"
                    strokeWidth={0.6}
                    style={{ animationDelay: `${h.delay.toFixed(2)}s` }}
                  />
                ))}
              </g>
            </svg>
            <div className="intro__words">
              <motion.p
                className="intro__name"
                initial={{ opacity: 0, y: 14 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 1.5, duration: 0.6, ease: "easeOut" }}
              >
                Harvester Risk Atlas
              </motion.p>
              <motion.p
                className="intro__question"
                initial={{ opacity: 0, y: 14 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 2.0, duration: 0.6, ease: "easeOut" }}
              >
                Which wild medicinal plants of the Philippines need attention first?
              </motion.p>
            </div>
          </div>
          <motion.button
            type="button"
            className="intro__skip"
            onClick={() => setOpen(false)}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.6 }}
          >
            Skip intro
          </motion.button>
        </motion.div>
      ) : null}
    </AnimatePresence>
  );
}

export function replayIntro() {
  try {
    sessionStorage.removeItem(SESSION_KEY);
  } catch {
    /* ignore */
  }
  window.location.assign(`${BASE}`);
}
