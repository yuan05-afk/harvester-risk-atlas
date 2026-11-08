// The film's own pieces, in the app's grammar: counters that land on the spoken number, photo plates, the hexagon
// (the app's unit of truth), the rank strip that becomes a range, and the page rail for the demo.
import React from 'react';
import { Img, staticFile } from 'remotion';
import { C, FLOAT_SHADOW, SANS, SERIF } from './lib/theme';
import { land, leave, noise, progress, settle } from './lib/motion';

/** Where an element sits while it lands (out of blur, slightly below and larger) and leaves (up into blur). */
export function arrive(t: number, at: number, out?: number, dur = 0.45) {
  const p = progress(t, at - 0.03, at + dur, land);
  const q = out === undefined ? 0 : progress(t, out, out + 0.32, leave);
  return { opacity: p * (1 - q), blur: (1 - p) * 14 + q * 12, dy: (1 - p) * 26 - q * 30, scale: 1 + (1 - p) * 0.08, shown: p > 0.001 && q < 0.999 };
}
export const look = (a: ReturnType<typeof arrive>): React.CSSProperties => ({
  opacity: a.opacity,
  filter: a.blur > 0.05 ? `blur(${a.blur.toFixed(2)}px)` : undefined,
  transform: `translateY(${a.dy.toFixed(2)}px) scale(${a.scale.toFixed(4)})`,
});

const fmt = (n: number) => Math.round(n).toLocaleString('en-US');

/** A hero number that steps per frame and lands on the spoken value. */
export const Counter: React.FC<{
  t: number; at: number; out: number; from?: number; to: number; dur?: number; y: number; size: number;
  prefix?: string; suffix?: string; color?: string; label?: React.ReactNode; labelAt?: number; dark?: boolean;
}> = ({ t, at, out, from = 0, to, dur = 1.1, y, size, prefix = '', suffix = '', color = C.ink, label, labelAt, dark }) => {
  const a = arrive(t, at, out);
  if (!a.shown) return null;
  const v = from + (to - from) * progress(t, at, at + dur, settle);
  const l = arrive(t, labelAt ?? at + 0.5, out);
  return (
    <div style={{ position: 'absolute', left: 0, right: 0, top: y, textAlign: 'center' }}>
      <div style={{ ...look(a), fontFamily: SERIF, fontWeight: 600, fontSize: size, lineHeight: 1, letterSpacing: -size * 0.03, color, fontVariantNumeric: 'lining-nums tabular-nums' }}>
        {prefix}
        {fmt(v)}
        {suffix}
      </div>
      {label && (
        <div style={{ ...look(l), marginTop: 26, fontFamily: SANS, fontWeight: 500, fontSize: 46, letterSpacing: -0.8, color: dark ? '#C9CED5' : C.secondary }}>{label}</div>
      )}
    </div>
  );
};

/** A photo mounted like a print, with its credit. */
export const Plate: React.FC<{
  t: number; at: number; out?: number; src: string; x: number; y: number; w: number; h: number; credit?: string; dim?: number; scaleIn?: number;
}> = ({ t, at, out, src, x, y, w, h, credit, dim = 0, scaleIn = 1.12 }) => {
  const a = arrive(t, at, out, 0.7);
  if (!a.shown) return null;
  const s = 1 + (scaleIn - 1) * (1 - progress(t, at, at + 1.6, settle));
  return (
    <div style={{ position: 'absolute', left: x - w / 2, top: y - h / 2, width: w, height: h + (credit ? 34 : 0), ...look(a) }}>
      <div style={{ width: w, height: h, borderRadius: 10, overflow: 'hidden', boxShadow: FLOAT_SHADOW, background: '#222' }}>
        <Img src={staticFile(`photos/${src}.jpg`)} style={{ width: '100%', height: '100%', objectFit: 'cover', transform: `scale(${s.toFixed(4)})`, filter: dim ? `brightness(${1 - dim * 0.55}) blur(${dim * 6}px)` : undefined }} />
      </div>
      {credit && <div style={{ marginTop: 10, fontFamily: SANS, fontSize: 17, color: C.tertiary, textAlign: 'center' }}>{credit}</div>}
    </div>
  );
};

/** Pointy-top hexagon path for a cell of radius r centred at (0, 0). */
const hexPath = (r: number) =>
  Array.from({ length: 6 }, (_, i) => {
    const a = (Math.PI / 180) * (60 * i - 30);
    return `${i ? 'L' : 'M'}${(r * Math.cos(a)).toFixed(2)},${(r * Math.sin(a)).toFixed(2)}`;
  }).join(' ') + ' Z';

/** One hexagon that drops in from oversize and lands. */
export const Hex: React.FC<{ t: number; at: number; out?: number; x: number; y: number; r: number; fill: string; stroke?: string }> = ({ t, at, out, x, y, r, fill, stroke }) => {
  const p = progress(t, at - 0.02, at + 0.35, land);
  const q = out === undefined ? 0 : progress(t, out, out + 0.3, leave);
  if (p <= 0 || q >= 1) return null;
  const s = 1 + (1 - p) * 1.6;
  return (
    <g transform={`translate(${x} ${y - (1 - p) * 40}) scale(${s.toFixed(3)})`} opacity={p * (1 - q)}>
      <path d={hexPath(r)} fill={fill} stroke={stroke} strokeWidth={stroke ? 3 : 0} />
    </g>
  );
};

/** A honeycomb of `cols` x `rows` cells; `kind(i)` decides each cell's look. */
export const HexField: React.FC<{
  t: number; at: number; out: number; cx: number; cy: number; r: number; cols: number; rows: number;
  kind: (i: number, col: number, row: number) => { fill: string; stroke?: string; at?: number };
}> = ({ t, at, out, cx, cy, r, cols, rows, kind }) => {
  const dx = Math.sqrt(3) * r;
  const dy = 1.5 * r;
  const w = dx * (cols + 0.5);
  const h = dy * (rows - 1) + 2 * r;
  const cells: React.ReactNode[] = [];
  for (let row = 0; row < rows; row++)
    for (let col = 0; col < cols; col++) {
      const i = row * cols + col;
      const k = kind(i, col, row);
      const x = cx - w / 2 + dx * (col + 0.5 + (row % 2 ? 0.5 : 0));
      const y = cy - h / 2 + r + dy * row;
      cells.push(<Hex key={i} t={t} at={k.at ?? at + noise(i + 3) * 0.6} out={out + noise(i + 7) * 0.15} x={x} y={y} r={r * 0.92} fill={k.fill} stroke={k.stroke} />);
    }
  return <svg width={1920} height={1080} style={{ position: 'absolute', left: 0, top: 0 }}>{cells}</svg>;
};

/** The 100-square grid: `lit` squares fill in the accent one by one from `litAt`. */
export const Squares: React.FC<{ t: number; at: number; out: number; lit: number; litAt: number; y: number }> = ({ t, at, out, lit, litAt, y }) => {
  const a = arrive(t, at, out);
  if (!a.shown) return null;
  const size = 46;
  const gap = 12;
  return (
    <div style={{ position: 'absolute', left: 960 - (size * 10 + gap * 9) / 2, top: y, display: 'grid', gridTemplateColumns: `repeat(10, ${size}px)`, gap, ...look(a) }}>
      {Array.from({ length: 100 }, (_, i) => {
        const on = i < lit ? progress(t, litAt + i * 0.12, litAt + i * 0.12 + 0.25, land) : 0;
        return <div key={i} style={{ width: size, height: size, borderRadius: 5, background: on > 0 ? C.accent : 'rgba(21,24,28,0.10)', transform: `scale(${1 + on * 0.06 * (1 - on)})`, opacity: i < lit ? 0.25 + on * 0.75 : 1 }} />;
      })}
    </div>
  );
};

/** A plain pill of words (people, sources). */
export const Pill: React.FC<{ t: number; at: number; out: number; children: React.ReactNode; dark?: boolean; size?: number }> = ({ t, at, out, children, dark, size = 38 }) => {
  const a = arrive(t, at, out);
  return (
    <div style={{ ...look(a), visibility: a.shown ? 'visible' : 'hidden', background: dark ? '#20262B' : C.card, color: dark ? '#E8EBEE' : C.ink, borderRadius: 999, padding: '16px 34px', boxShadow: FLOAT_SHADOW, fontFamily: SANS, fontWeight: 600, fontSize: size, letterSpacing: -0.5, whiteSpace: 'nowrap' }}>
      {children}
    </div>
  );
};

/** A centred label pill floating over footage, in the accent (one at a time). */
export const Tag: React.FC<{ t: number; at: number; out: number; x: number; y: number; children: React.ReactNode }> = ({ t, at, out, x, y, children }) => {
  const a = arrive(t, at, out);
  if (!a.shown) return null;
  return (
    <div style={{ position: 'absolute', left: x, top: y, transform: 'translateX(-50%)' }}>
      <div style={{ ...look(a), background: C.accent, color: '#fff', borderRadius: 14, padding: '14px 28px', boxShadow: '0 14px 40px rgba(124,26,75,0.30)', fontFamily: SANS, fontWeight: 600, fontSize: 32, letterSpacing: -0.3, whiteSpace: 'nowrap' }}>
        {children}
      </div>
    </div>
  );
};

/** The rank strip: one plant's rank jitters across 2,000 re-runs, leaving ghosts, then resolves into its range. */
export const RankStrip: React.FC<{ t: number; at: number; runFrom: number; runTo: number; resolve: number; out: number }> = ({ t, at, runFrom, runTo, resolve, out }) => {
  const a = arrive(t, at, out);
  if (!a.shown) return null;
  const L = 260;
  const W = 1400;
  const x = (r: number) => L + ((r - 1) / 28) * W;
  const y = 560;
  // Deterministic draws: mostly 1-5, centred on 2 (tongkat ali's real 90% interval is 1st to 5th, median 2nd).
  const draw = (i: number) => {
    const u = noise(i * 1.7 + 0.3);
    return u < 0.3 ? 1 : u < 0.62 ? 2 : u < 0.8 ? 3 : u < 0.92 ? 4 : 5;
  };
  const n = Math.floor(progress(t, runFrom, runTo) * 60);
  const k = progress(t, resolve, resolve + 0.6, settle);
  const live = draw(Math.floor((t - runFrom) * 9));
  return (
    <svg width={1920} height={1080} style={{ position: 'absolute', left: 0, top: 0, ...look(a) }}>
      <line x1={L} x2={L + W} y1={y} y2={y} stroke={C.tertiary} strokeWidth={3} />
      {[1, 5, 10, 15, 20, 25, 29].map((r) => (
        <g key={r}>
          <line x1={x(r)} x2={x(r)} y1={y - 12} y2={y + 12} stroke={C.tertiary} strokeWidth={2} />
          <text x={x(r)} y={y + 56} textAnchor="middle" fontFamily={SANS} fontSize={30} fill={C.tertiary}>{r === 1 ? '1st' : r === 29 ? '29th' : r}</text>
        </g>
      ))}
      {Array.from({ length: n }, (_, i) => (
        <circle key={i} cx={x(draw(i)) + (noise(i + 11) - 0.5) * 18} cy={y - 40 - (noise(i + 5) - 0.5) * 34} r={9} fill={C.accent} opacity={0.14 * (1 - k)} />
      ))}
      <rect x={x(1) - 14} y={y - 20} width={(x(5) - x(1) + 28) * k} height={40} rx={20} fill={C.accent} opacity={0.22 * k} />
      <circle cx={k > 0 ? x(2) : x(live)} cy={y} r={20} fill={C.accent} stroke="#fff" strokeWidth={5} />
      <text x={x(2)} y={y - 54} textAnchor="middle" fontFamily={SERIF} fontWeight={600} fontSize={44} fill={C.accent} opacity={k}>2nd</text>
      <text x={x(3)} y={y + 120} textAnchor="middle" fontFamily={SANS} fontWeight={600} fontSize={36} fill={C.ink} opacity={k}>could be anywhere from 1st to 5th</text>
    </svg>
  );
};

export const PAGES = ['Atlas', 'Plant', 'Field brief', 'Weights'];

/** The demo's map of pages, small at the top; the current page is ink, earlier ones ticked. */
export const Rail: React.FC<{ t: number; at: number; out: number; current: number }> = ({ t, at, out, current }) => {
  const a = arrive(t, at, out);
  if (!a.shown) return null;
  return (
    <div style={{ position: 'absolute', left: 0, right: 0, top: 34, display: 'flex', justifyContent: 'center', ...look(a) }}>
      <div style={{ display: 'flex', gap: 10, padding: 8, background: 'rgba(252,252,253,0.92)', borderRadius: 999, boxShadow: FLOAT_SHADOW }}>
        {PAGES.map((p, i) => (
          <div key={p} style={{ padding: '10px 22px', borderRadius: 999, fontFamily: SANS, fontWeight: 600, fontSize: 24, background: i === current ? C.ink : 'transparent', color: i === current ? '#fff' : i < current ? C.secondary : C.tertiary }}>
            {i < current ? '✓ ' : ''}
            {p}
          </div>
        ))}
      </div>
    </div>
  );
};

/** A plant card for the results: photo, name, the rank with its range, one plain reason. */
export const PlantCard: React.FC<{ t: number; at: number; out: number; x: number; photo: string; name: string; bin: string; rank: string; range: string; why: string; stampAt?: number }> = ({ t, at, out, x, photo, name, bin, rank, range, why, stampAt }) => {
  const a = arrive(t, at, out, 0.5);
  if (!a.shown) return null;
  const st = stampAt === undefined ? 0 : progress(t, stampAt, stampAt + 0.3, land);
  return (
    <div style={{ position: 'absolute', left: x - 160, top: 300, width: 320, background: C.card, borderRadius: 10, boxShadow: FLOAT_SHADOW, overflow: 'visible', ...look(a) }}>
      <div style={{ height: 300, borderRadius: '10px 10px 0 0', overflow: 'hidden' }}>
        <Img src={staticFile(`photos/${photo}.jpg`)} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
      </div>
      <div style={{ padding: '20px 22px 24px' }}>
        <div style={{ fontFamily: SERIF, fontWeight: 600, fontSize: 40, letterSpacing: -0.8, color: C.ink }}>{name}</div>
        <div style={{ fontFamily: SERIF, fontStyle: 'italic', fontSize: 22, color: C.tertiary, marginTop: 2 }}>{bin}</div>
        <div style={{ fontFamily: SANS, fontSize: 26, marginTop: 14, color: C.secondary }}>
          <b style={{ color: C.accent }}>{rank}</b> {range}
        </div>
        <div style={{ fontFamily: SANS, fontSize: 23, marginTop: 10, lineHeight: 1.35, color: C.secondary }}>{why}</div>
      </div>
      {st > 0 && (
        <div style={{ position: 'absolute', right: -18, top: 250, transform: `rotate(-8deg) scale(${(1 + (1 - st) * 1.4).toFixed(3)})`, opacity: st, border: `4px solid ${C.accent}`, color: C.accent, background: 'rgba(252,252,253,0.96)', borderRadius: 10, padding: '6px 14px', fontFamily: SANS, fontWeight: 700, fontSize: 22, letterSpacing: 0.5 }}>
          DENR listed
        </div>
      )}
    </div>
  );
};

export { leave, progress, land };
