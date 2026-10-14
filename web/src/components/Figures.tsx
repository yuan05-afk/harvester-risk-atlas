import { motion, useReducedMotion } from "motion/react";
import type { ReactNode, SVGProps } from "react";
import type { Component } from "../data/schema";

/*
 * The atlas's own drawings, in the manner of a field guide's plates: pen lines
 * in ink, with the one thing each figure is about inked in its own colour.
 * They replace stock icons. Every figure is decorative; the words beside it
 * carry the meaning.
 */

const INK = "var(--ink)";
const FAINT = "var(--ink-3)";

/** A pointy-top hexagon path centred on (x, y). */
function hex(x: number, y: number, r: number) {
  const pts = Array.from({ length: 6 }, (_, k) => {
    const a = ((-90 + 60 * k) * Math.PI) / 180;
    return `${(x + r * Math.cos(a)).toFixed(2)} ${(y + r * Math.sin(a)).toFixed(2)}`;
  });
  return `M${pts.join("L")}Z`;
}

/** An almond leaf from a base point, pointing along angle `deg`. */
function leaf(bx: number, by: number, deg: number, len: number, w: number) {
  const a = (deg * Math.PI) / 180;
  const tx = bx + len * Math.cos(a);
  const ty = by + len * Math.sin(a);
  const mx = (bx + tx) / 2;
  const my = (by + ty) / 2;
  const px = -Math.sin(a) * w;
  const py = Math.cos(a) * w;
  return `M${bx} ${by}Q${(mx + px).toFixed(1)} ${(my + py).toFixed(1)} ${tx.toFixed(1)} ${ty.toFixed(1)}Q${(mx - px).toFixed(1)} ${(my - py).toFixed(1)} ${bx} ${by}Z`;
}

/** Draws its path in, once, when scrolled into view. */
function Pen({ d, delay = 0, ...rest }: { d: string; delay?: number } & SVGProps<SVGPathElement>) {
  const reduce = useReducedMotion();
  if (reduce) return <path d={d} {...rest} />;
  return (
    <motion.path
      d={d}
      initial={{ pathLength: 0, opacity: 0 }}
      whileInView={{ pathLength: 1, opacity: 1 }}
      viewport={{ once: true, margin: "-40px" }}
      transition={{ pathLength: { duration: 0.9, delay, ease: [0.4, 0, 0.2, 1] }, opacity: { duration: 0.1, delay } }}
      {...(rest as object)}
    />
  );
}

/** Fades a filled shape in after the pen has passed. */
function Wash({ children, delay = 0.6 }: { children: ReactNode; delay?: number }) {
  const reduce = useReducedMotion();
  if (reduce) return <g>{children}</g>;
  return (
    <motion.g
      initial={{ opacity: 0 }}
      whileInView={{ opacity: 1 }}
      viewport={{ once: true, margin: "-40px" }}
      transition={{ duration: 0.5, delay }}
    >
      {children}
    </motion.g>
  );
}

/** A handwritten-style note with a leader line, as on an annotated plate. */
function Note({ x, y, tx, ty, children, anchor = "start" }: { x: number; y: number; tx: number; ty: number; children: string; anchor?: "start" | "end" }) {
  return (
    <Wash delay={1.1}>
      <path d={`M${x} ${y}L${tx} ${ty}`} stroke={FAINT} strokeWidth="0.8" fill="none" />
      <circle cx={tx} cy={ty} r="1.6" fill={INK} />
      <text x={anchor === "start" ? x + 3 : x - 3} y={y + 3.5} textAnchor={anchor} className="fig__note">
        {children}
      </text>
    </Wash>
  );
}

function RarityFigure() {
  const r = 13;
  const cells: { x: number; y: number; state: "searched" | "found" | "unsearched" }[] = [];
  const found = new Set(["1,2", "2,5"]);
  const unsearched = new Set(["0,0", "0,6", "3,0", "3,1", "3,6", "2,6"]);
  for (let j = 0; j < 4; j++) {
    for (let i = 0; i < 7; i++) {
      const key = `${j},${i}`;
      cells.push({
        x: 46 + i * 22.5 + (j % 2) * 11.25,
        y: 30 + j * 19.5,
        state: found.has(key) ? "found" : unsearched.has(key) ? "unsearched" : "searched",
      });
    }
  }
  return (
    <>
      {cells.map((c, n) =>
        c.state === "unsearched" ? (
          <path key={n} d={hex(c.x, c.y, r)} fill="none" stroke={FAINT} strokeWidth="0.8" strokeDasharray="2 2.5" />
        ) : (
          <Pen key={n} d={hex(c.x, c.y, r)} fill="none" stroke={INK} strokeWidth="1.1" delay={n * 0.025} />
        ),
      )}
      <Wash>
        {cells
          .filter((c) => c.state === "found")
          .map((c, n) => (
            <path key={n} d={hex(c.x, c.y, r - 2.5)} fill="var(--accent)" />
          ))}
      </Wash>
      <Note x={196} y={128} tx={158.5} ty={69}>
        found here
      </Note>
      <Note x={22} y={128} tx={102} ty={89}>
        searched, not found
      </Note>
    </>
  );
}

function HarvestFigure() {
  const ground = 76;
  return (
    <>
      <Pen d={`M24 ${ground}C70 ${ground - 2} 160 ${ground + 2} 216 ${ground}`} stroke={INK} strokeWidth="1.2" fill="none" />
      {/* soil stipple */}
      <Wash delay={0.3}>
        {[
          [40, 84], [58, 92], [78, 86], [170, 88], [190, 95], [205, 84], [150, 100], [88, 104], [62, 110], [184, 112],
        ].map(([x, y], n) => (
          <circle key={n} cx={x} cy={y} r="0.9" fill={FAINT} />
        ))}
      </Wash>
      {/* stem and leaves in ink */}
      <Pen d={`M120 ${ground}C119 60 123 42 120 18`} stroke={INK} strokeWidth="1.4" fill="none" />
      {[
        leaf(120, 64, -150, 30, 7),
        leaf(121, 52, -28, 32, 7),
        leaf(120, 38, -155, 26, 6),
        leaf(121, 28, -35, 24, 5.5),
        leaf(120, 19, -95, 14, 4),
      ].map((d, n) => (
        <Pen key={n} d={d} stroke={INK} strokeWidth="1.1" fill="var(--sheet)" delay={0.3 + n * 0.1} />
      ))}
      {/* bark scored on the stem */}
      <Wash delay={0.9}>
        <path d="M116 68l8 -3M116 72l8 -3" stroke="var(--accent)" strokeWidth="1.8" strokeLinecap="round" />
      </Wash>
      {/* the root, the part harvest takes, inked in colour */}
      {[
        `M120 ${ground}C121 92 118 108 121 132`,
        "M120 88C110 94 100 96 88 104",
        "M121 96C132 100 142 104 152 114",
        "M119 108C112 114 106 118 98 126",
        "M121 116C128 120 134 124 140 132",
        "M88 104C82 106 78 110 74 116",
      ].map((d, n) => (
        <Pen key={n} d={d} stroke="var(--accent)" strokeWidth={n === 0 ? 2.4 : 1.6} strokeLinecap="round" fill="none" delay={0.6 + n * 0.08} />
      ))}
      <Note x={168} y={58} tx={125} ty={67} >
        bark
      </Note>
      <Note x={168} y={128} tx={146} ty={112}>
        roots
      </Note>
    </>
  );
}

function Tree({ x, y, stump = false }: { x: number; y: number; stump?: boolean }) {
  if (stump) {
    // A felled tree: a cut stump with its rings showing.
    return (
      <g stroke="var(--accent)" strokeWidth="1.3" fill="var(--sheet)" strokeLinejoin="round">
        <path d={`M${x - 5} ${y}h10M${x - 3.5} ${y}v-5h7v5`} />
        <ellipse cx={x} cy={y - 5} rx="3.5" ry="1.4" />
      </g>
    );
  }
  return (
    <g stroke={INK} strokeWidth="1" fill="var(--sheet)">
      <path d={`M${x} ${y}v-6`} />
      <circle cx={x} cy={y - 11} r="5.2" />
    </g>
  );
}

function HabitatFigure() {
  const r = 23;
  const w = r * Math.sqrt(3);
  const cells = [
    { x: 60, y: 46, protectedArea: true, trees: [false, false, false] },
    { x: 60 + w, y: 46, protectedArea: false, trees: [false, true, false] },
    { x: 60 + 2 * w, y: 46, protectedArea: false, trees: [true, false, true] },
    { x: 60 + 3 * w, y: 46, protectedArea: false, trees: [true, true, true] },
    { x: 60 + w / 2, y: 46 + 1.5 * r, protectedArea: true, trees: [false, false, false] },
    { x: 60 + 1.5 * w, y: 46 + 1.5 * r, protectedArea: false, trees: [true, false, false] },
    { x: 60 + 2.5 * w, y: 46 + 1.5 * r, protectedArea: false, trees: [true, true, false] },
  ];
  const spots = [
    [-10, 11],
    [0, -1],
    [10, 11],
  ];
  return (
    <>
      <defs>
        <pattern id="fig-pa-hatch" width="5" height="5" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
          <path d="M0 0v5" stroke="var(--accent)" strokeWidth="1.2" opacity="0.4" />
        </pattern>
      </defs>
      <Wash delay={0.2}>
        {cells
          .filter((c) => c.protectedArea)
          .map((c, n) => (
            <path key={n} d={hex(c.x, c.y, r)} fill="url(#fig-pa-hatch)" />
          ))}
      </Wash>
      {cells.map((c, n) => (
        <Pen key={n} d={hex(c.x, c.y, r)} fill="none" stroke={INK} strokeWidth="1.1" delay={n * 0.06} />
      ))}
      {cells
        .filter((c) => c.protectedArea)
        .map((c, n) => (
          <Pen key={n} d={hex(c.x, c.y, r - 3)} fill="none" stroke="var(--accent)" strokeWidth="1.4" strokeDasharray="4 3" delay={0.5} />
        ))}
      <Wash delay={0.8}>
        {cells.flatMap((c, n) =>
          c.trees.map((stump, t) => <Tree key={`${n}-${t}`} x={c.x + spots[t][0]} y={c.y + spots[t][1]} stump={stump} />),
        )}
      </Wash>
      <Note x={20} y={130} tx={68} ty={94}>
        protected
      </Note>
      <Note x={214} y={130} tx={170} ty={92}>
        forest lost
      </Note>
    </>
  );
}

function ClimateFigure() {
  const curve = (dx: number) =>
    `M${30 + dx} 100C${60 + dx} 100 ${72 + dx} 34 ${100 + dx} 34C${128 + dx} 34 ${140 + dx} 100 ${170 + dx} 100`;
  return (
    <>
      <Pen d="M24 100H220" stroke={INK} strokeWidth="1.1" fill="none" />
      {[40, 70, 100, 130, 160, 190].map((x) => (
        <path key={x} d={`M${x} 100v4`} stroke={FAINT} strokeWidth="0.8" />
      ))}
      <Pen d={curve(0)} stroke={INK} strokeWidth="1.3" fill="none" />
      <Pen d={curve(26)} stroke="var(--accent)" strokeWidth="1.8" strokeDasharray="5 3" fill="none" delay={0.5} />
      <Wash delay={1}>
        <path d="M100 26H122" stroke="var(--accent)" strokeWidth="1.4" markerEnd="url(#fig-arrow)" />
      </Wash>
      <defs>
        <marker id="fig-arrow" viewBox="0 0 6 6" refX="5" refY="3" markerWidth="6" markerHeight="6" orient="auto">
          <path d="M0 0L6 3L0 6" fill="var(--accent)" />
        </marker>
      </defs>
      <Note x={22} y={128} tx={62} ty={78}>
        today
      </Note>
      <Note x={200} y={128} tx={170} ty={82}>
        2050, about +1.5 °C
      </Note>
    </>
  );
}

const FIGURES: Record<Component, () => ReactNode> = {
  R: RarityFigure,
  H: HarvestFigure,
  E: HabitatFigure,
  C: ClimateFigure,
};

/** A plate-sized drawing that explains one measure. */
export function ComponentFigure({ k, color }: { k: Component; color: string }) {
  const Figure = FIGURES[k];
  return (
    <svg className="fig" viewBox="0 0 240 140" style={{ ["--accent" as string]: color }} aria-hidden="true" focusable="false">
      <Figure />
    </svg>
  );
}

/** A small mark for the same measure, for headings and tiles. */
export function ComponentGlyph({ k, color, size = 28 }: { k: Component; color: string; size?: number }) {
  return (
    <svg className="glyph" viewBox="0 0 32 32" width={size} height={size} style={{ ["--accent" as string]: color }} aria-hidden="true" focusable="false">
      <g fill="none" stroke={INK} strokeWidth="1.3" strokeLinejoin="round" strokeLinecap="round">
        {k === "R" ? (
          <>
            <path d={hex(9.5, 10, 6.5)} />
            <path d={hex(21.5, 10, 6.5)} />
            <path d={hex(15.5, 20.5, 6.5)} />
            <path d={hex(15.5, 20.5, 4)} fill="var(--accent)" stroke="none" />
          </>
        ) : k === "H" ? (
          <>
            <path d="M3 17H29" />
            <path d="M16 17V5" />
            <path d={leaf(16, 12, -150, 8, 2.6)} />
            <path d={leaf(16, 8, -30, 8, 2.6)} />
            <path d="M16 17C16 21 15.5 25 16 29M16 21C13 22 11 23 9 26M16 23C19 24 21 25 23 28" stroke="var(--accent)" strokeWidth="1.8" />
          </>
        ) : k === "E" ? (
          <>
            <path d={hex(16, 16, 12)} />
            <path d="M6 9C4 15 6 23 12 25C16 26 16 18 14 14C12 10 13 5 9 5C7 5 6 7 6 9Z" stroke="var(--accent)" strokeDasharray="2.5 2" />
            <path d="M20 22v-3" />
            <circle cx="20" cy="16.5" r="2.6" fill="var(--sheet)" />
            <path d="M23.5 23h4M24.3 23v-2.6h2.4V23" stroke="var(--accent)" strokeWidth="1.5" />
          </>
        ) : (
          <>
            <path d="M3 25H29" />
            <path d="M4 25C9 25 9 10 13 10C17 10 17 25 22 25" />
            <path d="M10 25C15 25 15 10 19 10C23 10 23 25 28 25" stroke="var(--accent)" strokeDasharray="2.5 1.8" strokeWidth="1.6" />
          </>
        )}
      </g>
    </svg>
  );
}

/** Pen-drawn glyphs for the mobile tab bar, in the same hand as the figures. */
export function NavGlyph({ name }: { name: "overview" | "atlas" | "plants" | "how" }) {
  return (
    <svg className="nav-glyph" viewBox="0 0 24 24" width="24" height="24" aria-hidden="true" focusable="false">
      <g fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round" strokeLinecap="round">
        {name === "overview" ? (
          <>
            {/* a field compass: the overview */}
            <circle cx="12" cy="12" r="8.5" />
            <path d="M12 2v2M12 20v2M2 12h2M20 12h2" />
            <path d="M12 6.5L14.2 12L12 17.5L9.8 12Z" />
            <path d="M12 6.5L14.2 12H9.8Z" className="nav-glyph__fill" />
          </>
        ) : name === "atlas" ? (
          <>
            <path d={hex(8, 8, 5)} />
            <path d={hex(16.7, 8, 5)} />
            <path d={hex(12.35, 15.5, 5)} className="nav-glyph__fill" />
          </>
        ) : name === "plants" ? (
          <>
            <path d="M12 21V8" />
            <path d={leaf(12, 15, -150, 8, 2.8)} />
            <path d={leaf(12, 11, -30, 8, 2.8)} className="nav-glyph__fill" />
            <path d={leaf(12, 8, -90, 5, 1.8)} />
          </>
        ) : (
          <>
            <path d="M12 4v16M7 20h10" />
            <path d="M4 7h16" />
            <path d="M4 7l-2.5 6h5zM20 7l-2.5 6h5z" />
            <path d="M1.5 13a2.5 1.4 0 0 0 5 0M17.5 13a2.5 1.4 0 0 0 5 0" className="nav-glyph__fill" />
          </>
        )}
      </g>
    </svg>
  );
}

/** A verdict written in the margin: a tick, a caution, or a wavering line. */
export function VerdictMark({ kind }: { kind: "ok" | "limit" | "weak" }) {
  const d =
    kind === "ok"
      ? "M5 17C8 19 10 22 11 25C14 17 19 10 27 5"
      : kind === "limit"
        ? "M16 5C15.6 11 16.4 15 16 20M16 25.5v0.5"
        : "M4 17C8 11 11 11 14 16C17 21 20 21 24 15C25.5 13 27 12.5 28 13";
  return (
    <svg className={`verdict-mark verdict-mark--${kind}`} viewBox="0 0 32 32" width="30" height="30" aria-hidden="true" focusable="false">
      <Pen d={d} fill="none" stroke="currentColor" strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}
