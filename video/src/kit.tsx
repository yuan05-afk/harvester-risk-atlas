// Version 4's pieces, in the app's Field Atlas grammar: a flat cool-grey ground, white sheets with hairlines, ink type
// that rises out of a mask (no blur, no glow, no gradients), and one drawn ink mark at a time to point the eye.
import React from 'react';
import { Img, staticFile } from 'remotion';
import { C, SANS, SERIF } from './lib/theme';
import { land, leave, progress, settle } from './lib/motion';
import geo from './geo.json';

export const PAPER = '#EFF1F3';
export const SHEET = '#FCFCFD';
export const RULE = '#D8DCE1';
export const RULE2 = '#AEB5BE';
export const CARD_SHADOW = '0 1px 0 rgba(21,24,28,0.06), 0 2px 5px rgba(21,24,28,0.05)';
export const LIFT = '0 2px 3px rgba(21,24,28,0.08), 0 16px 30px rgba(21,24,28,0.12)';

/** In and out of a mask: 0..1 for arriving, 0..1 for leaving. */
export function io(t: number, at: number, out?: number, dur = 0.5) {
  const p = progress(t, at - 0.02, at + dur, land);
  const q = out === undefined ? 0 : progress(t, out, out + 0.35, leave);
  return { p, q, shown: p > 0.001 && q < 0.999 };
}

/** A block that slides up into place and leaves upward. */
export const Rise: React.FC<{ t: number; at: number; out?: number; style?: React.CSSProperties; children: React.ReactNode; dist?: number }> = ({ t, at, out, style, children, dist = 36 }) => {
  const a = io(t, at, out);
  if (!a.shown) return null;
  return <div style={{ position: 'absolute', ...style, opacity: Math.min(1, a.p * 1.4) * (1 - a.q), transform: `translateY(${((1 - a.p) * dist - a.q * dist).toFixed(2)}px)` }}>{children}</div>;
};

export type Tok = { w: string; at: number; serif?: boolean; blue?: boolean; c?: string };

/** Words timed to the voice, each rising out of its own mask. ^word in the accent, *word in upright Fraunces. */
export const Say: React.FC<{
  t: number; words: Tok[]; x: number; y: number; size: number; out?: number; align?: 'center' | 'left';
  color?: string; weight?: number; width?: number; accent?: string;
}> = ({ t, words, x, y, size, out, align = 'center', color = C.ink, weight = 600, width = 1500, accent = C.accent }) => {
  if (!words.length || t < words[0].at - 0.1) return null;
  if (out !== undefined && t > out + 0.7) return null;
  return (
    <div style={{ position: 'absolute', left: align === 'center' ? x - width / 2 : x, top: y, width, textAlign: align, transform: 'translateY(-50%)', fontFamily: SANS, fontWeight: weight, fontSize: size, lineHeight: 1.16, letterSpacing: -size * 0.022, color }}>
      {words.map((wd, i) => {
        const pin = progress(t, wd.at - 0.04, wd.at + 0.38, land);
        const pout = out !== undefined ? progress(t, out + i * 0.015, out + 0.3 + i * 0.015, leave) : 0;
        return (
          <span key={i} style={{ display: 'inline-block', overflow: 'hidden', verticalAlign: 'top', paddingBottom: size * 0.12, marginBottom: -size * 0.12, marginRight: size * 0.24 }}>
            <span style={{ display: 'inline-block', transform: `translateY(${((1 - pin) * 105 - pout * 105).toFixed(2)}%)`, fontFamily: wd.serif ? SERIF : SANS, fontWeight: wd.serif ? 600 : weight, color: wd.c ?? (wd.blue ? accent : color) }}>
              {wd.w}
            </span>
          </span>
        );
      })}
    </div>
  );
};

const fmt = (n: number) => Math.round(n).toLocaleString('en-US');

/** A number that counts up and lands on the spoken value, set in Fraunces, upright. */
export const Count: React.FC<{ t: number; at: number; out?: number; from?: number; to: number; dur?: number; x: number; y: number; size: number; color?: string; suffix?: string; align?: 'center' | 'left' }> = ({ t, at, out, from = 0, to, dur = 1.0, x, y, size, color = C.ink, suffix = '', align = 'center' }) => {
  const a = io(t, at, out);
  if (!a.shown) return null;
  const v = from + (to - from) * progress(t, at, at + dur, settle);
  return (
    <div style={{ position: 'absolute', left: align === 'center' ? x - 900 : x, top: y, width: 1800, textAlign: align, overflow: 'hidden' }}>
      <div style={{ transform: `translateY(${((1 - a.p) * 60 - a.q * 100).toFixed(2)}%)`, fontFamily: SERIF, fontWeight: 600, fontSize: size, lineHeight: 1.04, letterSpacing: -size * 0.03, color, fontVariantNumeric: 'lining-nums tabular-nums' }}>
        {fmt(v)}
        {suffix}
      </div>
    </div>
  );
};

/** A white sheet with a hairline, the app's panel. */
export const Sheet: React.FC<{ t: number; at: number; out?: number; x: number; y: number; w: number; h?: number; children: React.ReactNode; pad?: number }> = ({ t, at, out, x, y, w, h, children, pad = 40 }) => {
  const a = io(t, at, out, 0.55);
  if (!a.shown) return null;
  return (
    <div style={{ position: 'absolute', left: x, top: y, width: w, height: h, padding: pad, boxSizing: 'border-box', background: SHEET, border: `1px solid ${RULE}`, borderRadius: 4, boxShadow: CARD_SHADOW, opacity: Math.min(1, a.p * 1.5) * (1 - a.q), transform: `translateY(${((1 - a.p) * 40 - a.q * 40).toFixed(2)}px)` }}>
      {children}
    </div>
  );
};

/** A hand-drawn ink ellipse around a box (screen px), drawn on, then lifted off. The film's only pointer. */
export const Ring: React.FC<{ t: number; at: number; out: number; x: number; y: number; w: number; h: number; color?: string; width?: number }> = ({ t, at, out, x, y, w, h, color = C.accent, width = 5 }) => {
  const p = progress(t, at, at + 0.55, settle);
  const q = progress(t, out, out + 0.3, leave);
  if (p <= 0 || q >= 1) return null;
  const cx = x + w / 2;
  const cy = y + h / 2;
  const rx = w / 2 + 26;
  const ry = h / 2 + 18;
  // One loop and a little overshoot past the start, as a pen would.
  const pts = Array.from({ length: 73 }, (_, i) => {
    const a = -Math.PI * 0.62 + (i / 72) * Math.PI * 2.12;
    const wob = 1 + 0.025 * Math.sin(i * 0.5);
    return `${(cx + rx * wob * Math.cos(a)).toFixed(1)},${(cy + ry * wob * Math.sin(a) * (1 + i * 0.0008)).toFixed(1)}`;
  });
  const L = Math.PI * (rx + ry) * 1.06;
  return (
    <svg width={1920} height={1080} style={{ position: 'absolute', left: 0, top: 0, pointerEvents: 'none', opacity: 1 - q }}>
      <polyline points={pts.join(' ')} fill="none" stroke={color} strokeWidth={width} strokeLinecap="round" strokeLinejoin="round" strokeDasharray={L} strokeDashoffset={L * (1 - p)} />
    </svg>
  );
};

/** A drawn underline. */
export const Under: React.FC<{ t: number; at: number; out: number; x: number; y: number; w: number; color?: string }> = ({ t, at, out, x, y, w, color = C.accent }) => {
  const p = progress(t, at, at + 0.4, settle);
  const q = progress(t, out, out + 0.3, leave);
  if (p <= 0 || q >= 1) return null;
  return (
    <svg width={1920} height={1080} style={{ position: 'absolute', left: 0, top: 0, pointerEvents: 'none', opacity: 1 - q }}>
      <path d={`M${x},${y} q${w / 2},${-6} ${w},${2}`} fill="none" stroke={color} strokeWidth={6} strokeLinecap="round" strokeDasharray={w * 1.1} strokeDashoffset={w * 1.1 * (1 - p)} />
    </svg>
  );
};

/** A photo print with its credit line. */
export const Photo: React.FC<{ t: number; at: number; out?: number; src: string; x: number; y: number; w: number; h: number; credit?: string }> = ({ t, at, out, src, x, y, w, h, credit }) => {
  const a = io(t, at, out, 0.7);
  if (!a.shown) return null;
  const s = 1.06 - 0.06 * progress(t, at, at + 3, settle);
  return (
    <div style={{ position: 'absolute', left: x, top: y, width: w, opacity: Math.min(1, a.p * 1.3) * (1 - a.q), transform: `translateY(${((1 - a.p) * 30 - a.q * 30).toFixed(2)}px)` }}>
      <div style={{ width: w, height: h, borderRadius: 4, overflow: 'hidden', boxShadow: LIFT }}>
        <Img src={staticFile(`photos/${src}.jpg`)} style={{ width: '100%', height: '100%', objectFit: 'cover', transform: `scale(${s.toFixed(4)})` }} />
      </div>
      {credit && <div style={{ marginTop: 10, fontFamily: SANS, fontSize: 17, color: C.tertiary }}>{credit}</div>}
    </div>
  );
};

type Geo = { w: number; h: number; land: string[]; cells: [number, number, number][]; tongkat: [number, number][]; look: Record<string, [number, number]>; cell_r: number };
const G = geo as unknown as Geo;

const hexPts = (x: number, y: number, r: number) =>
  Array.from({ length: 6 }, (_, i) => {
    const a = (Math.PI / 180) * (60 * i - 30);
    return `${(x + r * Math.cos(a)).toFixed(1)},${(y + r * Math.sin(a)).toFixed(1)}`;
  }).join(' ');

/**
 * The Philippines from the app's own land outline and H3 cells. `effort` 0..1 shades every cell by survey effort
 * (well searched, 100+ plant records, in ink); `tongkat` 0..1 drops tongkat ali's five cells; `look` 0..1 marks the
 * islands Co's Digital Flora documents it on.
 */
export const PH: React.FC<{ t: number; x: number; y: number; scale: number; landIn?: number; effort?: number; tongkat?: number; look?: number; opacity?: number; tongkatAt?: number }> = ({ t, x, y, scale, landIn = 1, effort = 0, tongkat = 0, look = 0, opacity = 1, tongkatAt = 0 }) => {
  const r = G.cell_r * 1.02;
  return (
    <svg width={G.w * scale} height={G.h * scale} viewBox={`0 0 ${G.w} ${G.h}`} style={{ position: 'absolute', left: x, top: y, overflow: 'visible', opacity }}>
      <g opacity={landIn}>
        {G.land.map((d, i) => (
          <path key={i} d={d} fill={SHEET} stroke={RULE2} strokeWidth={1.2 / scale} />
        ))}
      </g>
      {effort > 0 &&
        G.cells.map(([cx, cy, e], i) => {
          const k = Math.min(1, Math.max(0, effort * 1.6 - (cy / G.h) * 0.6));
          if (k <= 0) return null;
          const well = e >= 100;
          return <polygon key={i} points={hexPts(cx, cy, r * 0.94)} fill={well ? C.ink : '#C9CFD6'} opacity={k * (well ? 0.85 : 0.75)} />;
        })}
      {tongkat > 0 &&
        G.tongkat.map(([cx, cy], i) => {
          const p = progress(t, tongkatAt + i * 0.14, tongkatAt + i * 0.14 + 0.4, land);
          if (p <= 0) return null;
          const s = 1 + (1 - p) * 2.2;
          return (
            <g key={i} opacity={p * tongkat}>
              <circle cx={cx} cy={cy} r={(r * 3.2 * s) / 1} fill="none" stroke={C.accent} strokeWidth={2.4 / scale} opacity={0.5} />
              <polygon points={hexPts(cx, cy, r * 1.6)} fill={C.accent} />
            </g>
          );
        })}
      {look > 0 &&
        Object.entries(G.look).map(([name, [cx, cy]], i) => {
          const p = Math.min(1, Math.max(0, look * 3 - i));
          if (p <= 0) return null;
          return (
            <g key={name} opacity={p}>
              <circle cx={cx} cy={cy} r={(14 + (1 - p) * 20) / scale * 1.6} fill="none" stroke={C.ink} strokeWidth={3 / scale} strokeDasharray={`${6 / scale} ${5 / scale}`} />
              <text x={cx + 26 / scale * 1.4} y={cy + 8 / scale} fontFamily={SANS} fontWeight={700} fontSize={28 / scale} fill={C.ink}>
                {name}
              </text>
            </g>
          );
        })}
    </svg>
  );
};
export const PH_W = G.w;
export const PH_H = G.h;
