// Harvester Risk Atlas: the EthnoHack pitch, version 4 (2:48, 60 fps, narrated by ElevenLabs Brian on eleven_v4).
//   Attention  four billion people, plants taken from the wild -> the Philippines: 175 hectares a day, harvest unmeasured
//              -> tongkat ali's five records, dropped on the real map
//   Interest   the map becomes the app -> three questions -> where botanists searched well (real cells) -> 2,000 runs as
//              a histogram of tongkat ali's real ranks -> a range
//   Desire     the app as one journey: atlas -> plant -> field brief -> weights -> Seasons (new) -> expert cross-check
//              (new) -> where to look next -> two thirds barely searched -> five plants
//   Action     limits, the name, the link
// One flat cool-grey ground, ink type rising out of masks, white sheets with hairlines, one drawn ink mark at a time.
// Every picture cue keys on a measured word of the narration (timing.ts). Voice only, no music.
import React from 'react';
import { AbsoluteFill, Audio, Img, staticFile, useCurrentFrame } from 'remotion';
import '@fontsource-variable/atkinson-hyperlegible-next';
import '@fontsource-variable/fraunces';
import { C, SANS, SERIF } from './lib/theme';
import { glide, keys, land, progress, settle } from './lib/motion';
import { Screen } from './components/Screen';
import { DURATION, FPS, cue, line } from './timing';
import takes from './takes.json';
import { Count, PAPER, PH, PH_H, PH_W, Photo, RULE, Ring, Rise, Say, SHEET, Sheet, Under, io } from './kit';

const FULL = { x: 0, y: 0, w: 1920 };
const plain = (s: string, at: number) => s.split(' ').map((w, i) => ({ w, at: at + i * 0.06 }));

// ------------------------------------------------------------------------------------------------------------ cues
const T = {
  four: cue('4'),
  most: cue('Most'),
  almost: cue('almost'),
  ph: cue('Philippines,') - 0.3,
  ha: cue('175'),
  tree: cue('tree'),
  but: cue('but'),
  so: cue('So'),
  take: cue('Take'),
  roots: cue('roots'),
  officially: cue('officially'),
  yet: cue('yet'),
  five: cue('five'),
  built: cue('So', 2),
  asks: cue('asks') - 0.3,
  rare: cue('rare'),
  harvesting: cue('harvesting'),
  home: cue('home'),
  rarity: cue('Rarity'),
  then: cue('Then'),
  runs: cue('2'),
  different: cue('different'),
  range: cue('range,'),
  pick: cue('Pick'),
  broad: cue('broad'),
  second: cue('second'),
  field: cue('field'),
  slider: cue('slider'),
  year: cue('year'),
  slide: cue('slide'),
  flower: cue('flower'),
  pile: cue('pile'),
  weighed: cue('weighed'),
  name: cue('name'),
  digital: cue('digital'),
  leonardo: cue('Leonardo'),
  forT: cue('Tonkat', 3) - 0.3,
  agrees: cue('agrees,'),
  but2: cue('But', 2),
  mindoro: cue('Mindoro,'),
  nothing: cue('nothing.'),
  look: cue('look'),
  across: cue('Across'),
  two: cue('two'),
  barely: cue('barely'),
  fivePlants: cue('Five', 2),
  change: cue('Change'),
  medical: cue('medical'),
  experts: cue('experts'),
  name2: cue('Harvester', 3),
  which: cue('Which', 2),
  help: cue('Help', 2),
};

// ----------------------------------------------------------------------------------------------------- footage
type Box = { x: number; y: number; w: number; h: number };
type Take = { frames: number; clicks: number[]; marks?: Record<string, number>; boxes?: Record<string, Box> };
const TK = takes as unknown as Record<string, Take>;
const len = (n: string) => TK[n].frames / FPS;
const clickAt = (n: string, i = 0) => TK[n].clicks[i] / FPS;
const mark = (n: string, m: string) => (TK[n].marks?.[m] ?? 0) / FPS;
const box = (n: string, m: string): Box => TK[n].boxes?.[m] ?? { x: 860, y: 500, w: 200, h: 60 };

// The journey: each take starts on the frame after the previous take's click, so the real click is the cut.
const at: Record<string, number> = {};
at.atlas = T.pick - 0.4;
at.profile = at.atlas + clickAt('atlas', 1) + 0.1;
at.brief = at.profile + clickAt('profile') + 0.1;
// Weights starts so its drag lands on "slider"; the brief holds on its page until then.
at.weights = T.slider - mark('weights', 'drag') + 0.1;
at.seasons = at.weights + clickAt('weights') + 0.1;
const DEMO_END = T.name - 0.4;
// The cross-check take: its "Co's Digital Flora" row arrives on "agrees".
at.check = T.agrees - mark('check', 'cdfp');
const CHECK_END = T.but2 + 0.2;

// --------------------------------------------------------------------------- the plane the app footage sits on
const PLANE_W = 1600;
const planeScale = PLANE_W / 1920;
const PLANE_Y = 540;
/** A footage box (viewport px) to film px on the standard plane, with an optional camera rect. */
const onPlane = (b: Box, cam = FULL) => {
  const s = PLANE_W / cam.w;
  const left = 960 - PLANE_W / 2;
  const top = PLANE_Y - (PLANE_W * 9) / 16 / 2;
  return { x: left + (b.x - cam.x) * s, y: top + (b.y - cam.y) * s, w: b.w * s, h: b.h * s };
};

/** A plain caption on a white slip under the footage: what to look at, in a few words. */
const Caption: React.FC<{ t: number; at: number; out: number; children: React.ReactNode }> = ({ t, at: a, out, children }) => {
  const k = io(t, a, out, 0.45);
  if (!k.shown) return null;
  return (
    <div style={{ position: 'absolute', left: 0, right: 0, top: 1000, display: 'flex', justifyContent: 'center' }}>
      <div style={{ overflow: 'hidden', paddingBottom: 4 }}>
        <div style={{ transform: `translateY(${((1 - k.p) * 110 - k.q * 110).toFixed(2)}%)`, fontFamily: SANS, fontWeight: 600, fontSize: 36, letterSpacing: -0.4, color: C.ink }}>
          {children}
        </div>
      </div>
    </div>
  );
};

// --------------------------------------------------------------------------------------------------- 1. hook
const Hook: React.FC<{ t: number }> = ({ t }) => {
  if (t > T.ph + 0.6) return null;
  const out1 = T.most - 0.35;
  const out2 = T.ph - 0.4;
  return (
    <>
      <Say t={t} words={plain('Up to', 0.66)} x={960} y={330} size={48} weight={600} color={C.secondary} out={out1} />
      <Count t={t} at={T.four - 0.1} out={out1} from={0} to={4} dur={0.6} x={960} y={360} size={260} suffix=" billion" />
      <Say t={t} words={line('people rely on herbal medicine.', cue('people'))} x={960} y={740} size={64} out={out1} />
      <Photo t={t} at={T.most - 0.1} out={out2} src="cinnamomum-mercadoi" x={180} y={190} w={560} h={700} credit="Kalingag, a wild medicinal tree · Nielbert Raner, CC BY 4.0, iNaturalist" />
      <Say t={t} words={line('Most medicinal plants in trade are still taken from the ^wild.', T.most)} x={860} y={420} size={66} align="left" width={900} out={T.almost - 0.4} />
      <Say t={t} words={line('Almost no one is counting what is left.', T.almost)} x={860} y={540} size={80} align="left" width={900} out={out2} />
      <Under t={t} at={cue('left.') + 0.1} out={out2} x={1404} y={652} w={210} />
    </>
  );
};

// --------------------------------------------------------------- 2. the problem, on the Philippines' own outline
const MAP = { x: 1180, y: 70, s: 0.92 };
const Problem: React.FC<{ t: number }> = ({ t }) => {
  if (t < T.ph - 0.2 || t > T.take + 0.6) return null;
  const out = T.take - 0.4;
  const ledgerOut = T.so - 0.4;
  const rows: Array<[string, string, boolean]> = [
    ['Where plants grow', 'GBIF records', true],
    ['How threatened they are', "DENR's list", true],
    ['How much is harvested', 'not measured', false],
  ];
  return (
    <>
      <Say t={t} words={line('In the Philippines', T.ph)} x={160} y={200} size={60} align="left" width={1000} out={out} />
      <Count t={t} at={T.ha} out={T.but - 0.35} from={0} to={175} dur={1.0} x={160} y={300} size={230} align="left" />
      <Say t={t} words={line('hectares of tree cover lost, every day', cue('hectares'))} x={160} y={600} size={52} align="left" width={1000} weight={500} color={C.secondary} out={T.but - 0.35} />
      <Sheet t={t} at={T.but} out={ledgerOut} x={160} y={300} w={940} pad={0}>
        {rows.map(([k, v, ok], i) => {
          const r = io(t, T.but + 0.15 + i * 0.3);
          return (
            <div key={k} style={{ display: 'flex', alignItems: 'baseline', padding: '30px 40px', borderTop: i ? `1px solid ${RULE}` : undefined, opacity: r.p }}>
              <span style={{ fontSize: 42, fontWeight: 600, color: C.ink, letterSpacing: -0.6 }}>{k}</span>
              <span style={{ marginLeft: 'auto', fontSize: 32, fontWeight: 700, color: ok ? C.secondary : C.accent }}>{v}</span>
            </div>
          );
        })}
      </Sheet>
      <Under t={t} at={cue('harvest.') + 0.1} out={ledgerOut} x={872} y={555} w={196} />
      <Say t={t} words={line('So where should a ranger, or a harvester, even start?', T.so)} x={160} y={460} size={72} align="left" width={980} out={out} />
    </>
  );
};

// ------------------------------------------------- the map that carries the opening: problem -> tongkat ali -> app
const OpeningMap: React.FC<{ t: number }> = ({ t }) => {
  if (t < T.ph - 0.2 || t > T.built + 1.4) return null;
  const a = io(t, T.ph, undefined, 0.8);
  // The map slides to centre for the five records, then shrinks into the app's own map as the app rises.
  const x = keys(t, [[0, MAP.x], [T.yet - 0.2, MAP.x], [T.yet + 0.6, 1080, glide], [T.built - 0.1, 1080], [T.built + 0.9, 1250, glide]]);
  const y = keys(t, [[0, MAP.y], [T.built - 0.1, MAP.y], [T.built + 0.9, 250, glide]]);
  const s = keys(t, [[0, MAP.s], [T.built - 0.1, MAP.s], [T.built + 0.9, 0.5, glide]]);
  const fade = progress(t, T.built + 0.5, T.built + 1.2, settle);
  return (
    <div style={{ opacity: a.p * (1 - fade), transform: `translateY(${((1 - a.p) * 30).toFixed(1)}px)` }}>
      <PH t={t} x={x} y={y} scale={s} tongkat={t > T.five - 0.4 ? 1 : 0} tongkatAt={T.five - 0.2} />
    </div>
  );
};

// ------------------------------------------------------------------------------- 3. tongkat ali, five records
const Tongkat: React.FC<{ t: number }> = ({ t }) => {
  if (t < T.take - 0.4 || t > T.built + 0.6) return null;
  const out = T.built - 0.35;
  const stamp = progress(t, T.officially, T.officially + 0.35, land);
  return (
    <>
      <Photo t={t} at={T.take - 0.1} out={T.yet - 0.4} src="eurycoma-longifolia" x={160} y={150} w={520} h={680} credit="Tongkat ali · Steven Bodzin, CC BY 4.0, iNaturalist" />
      <Say t={t} words={line('Tongkat ali', T.take)} x={760} y={250} size={110} align="left" width={900} out={T.yet - 0.4} accent={C.ink} />
      <Say t={t} words={[{ w: 'Eurycoma longifolia', at: T.take + 0.5 }]} x={766} y={340} size={36} align="left" width={900} weight={500} color={C.tertiary} out={T.yet - 0.4} />
      <Say t={t} words={line('Roots dug up and sold.', T.roots)} x={766} y={450} size={52} align="left" width={900} weight={500} color={C.secondary} out={T.yet - 0.4} />
      {stamp > 0 && t < T.yet + 0.2 && (
        <div style={{ position: 'absolute', left: 766, top: 540, opacity: stamp * (1 - progress(t, T.yet - 0.4, T.yet - 0.1)), transform: `rotate(-3deg) scale(${(1 + (1 - stamp) * 0.6).toFixed(3)})`, transformOrigin: 'left center', border: `4px solid ${C.accent}`, borderRadius: 4, padding: '10px 22px', color: C.accent, fontFamily: SANS, fontWeight: 700, fontSize: 38, letterSpacing: 0.4 }}>
          ENDANGERED · DENR list
        </div>
      )}
      <Say t={t} words={line('Open databases hold just', T.yet)} x={160} y={330} size={52} align="left" width={800} weight={500} color={C.secondary} out={out} />
      <Count t={t} at={T.five} out={out} from={0} to={5} dur={0.5} x={160} y={380} size={300} align="left" color={C.accent} />
      <Say t={t} words={line('reliable records of it.', cue('reliable'))} x={160} y={740} size={60} align="left" width={800} out={out} />
    </>
  );
};

// ------------------------------------------------------------------------ 4. the app rises out of the map
const Reveal: React.FC<{ t: number }> = ({ t }) => {
  const s = T.built - 0.1;
  const leaveAt = T.asks;
  if (t < s - 0.1 || t > leaveAt + 0.6) return null;
  return (
    <>
      <Screen t={t} src="overview" at={s} from={0} dur={leaveAt + 0.6 - s} cam={[[0, FULL]]} radius={6}
        px={[[s, 1250], [s + 1.0, 960, glide]]} py={[[s, 470], [s + 1.0, 470, glide], [leaveAt, 470], [leaveAt + 0.5, -420]]}
        pw={[[s, 420], [s + 1.0, 1440, glide]]} opacity={progress(t, s, s + 0.4)} />
      <Say t={t} words={line('Which plants need help first · where they grow · how sure we are', cue('help') - 0.3)} x={960} y={950} size={44} weight={600} out={leaveAt - 0.2} />
    </>
  );
};

// ----------------------------------------------------------------- 5. method: three questions, searched, 2,000 runs
const Q = [
  { label: 'Rarity', q: 'How rare is it?', ink: C.rarity, at: () => T.rare },
  { label: 'Harvest harm', q: 'Does harvesting kill it?', ink: C.harvest, at: () => T.harvesting },
  { label: 'Habitat pressure', q: 'Is its home disappearing?', ink: C.habitat, at: () => T.home },
];
// Tongkat ali's rank in each of the 2,000 runs (uncertainty.rank_summary, the published seed): 1st to 7th.
const RUNS = [900, 336, 385, 227, 134, 11, 3];
const Method: React.FC<{ t: number }> = ({ t }) => {
  if (t < T.asks - 0.4 || t > T.pick + 0.5) return null;
  const qOut = T.rarity - 0.4;
  const effOut = T.then - 0.35;
  const histOut = T.pick - 0.45;
  const fill = progress(t, T.runs, T.range - 0.4, (x) => 1 - Math.pow(1 - x, 2));
  const runNo = Math.max(1, Math.round(2000 * fill));
  const k = progress(t, T.range - 0.2, T.range + 0.5, settle);
  const max = Math.max(...RUNS);
  const bx = (i: number) => 520 + i * 140;
  const base = 820;
  return (
    <>
      <Say t={t} words={line('Three questions', cue('three'))} x={160} y={190} size={60} align="left" width={1200} out={qOut} />
      <Sheet t={t} at={T.rare - 0.15} out={qOut} x={160} y={270} w={1600} pad={0}>
        {Q.map((q, i) => {
          const r = io(t, q.at() - 0.1);
          return (
            <div key={q.label} style={{ display: 'flex', alignItems: 'center', gap: 28, padding: '34px 44px', borderTop: i ? `1px solid ${RULE}` : undefined, opacity: r.p, transform: `translateY(${((1 - r.p) * 16).toFixed(1)}px)` }}>
              <span style={{ width: 22, height: 22, background: q.ink, borderRadius: 2, flex: 'none' }} />
              <span style={{ width: 360, fontSize: 36, fontWeight: 700, color: q.ink }}>{q.label}</span>
              <span style={{ fontFamily: SERIF, fontWeight: 600, fontSize: 62, letterSpacing: -1.2, color: C.ink }}>{q.q}</span>
            </div>
          );
        })}
      </Sheet>
      {/* Where botanists searched well: the app's own cells, ink where 100+ plant records were made. */}
      {t > T.rarity - 0.2 && t < effOut + 0.5 && (
        <div style={{ opacity: io(t, T.rarity, effOut).p * (1 - io(t, T.rarity, effOut).q) }}>
          <PH t={t} x={1150} y={60} scale={0.94} effort={progress(t, T.rarity, cue('searched.') + 0.3, settle)} />
        </div>
      )}
      <Say t={t} words={line('Rarity is measured only where botanists actually ^searched.', T.rarity)} x={160} y={400} size={66} align="left" width={900} out={effOut} />
      <Rise t={t} at={cue('searched.')} out={effOut} style={{ left: 160, top: 620, width: 900 }}>
        <div style={{ display: 'flex', gap: 30, fontSize: 32, fontWeight: 600, color: C.secondary, alignItems: 'center' }}>
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: 12 }}><i style={{ width: 22, height: 22, background: C.ink, display: 'inline-block' }} />searched well</span>
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: 12 }}><i style={{ width: 22, height: 22, background: '#C9CFD6', display: 'inline-block' }} />barely searched</span>
        </div>
        <div style={{ fontSize: 28, color: C.tertiary, marginTop: 14 }}>332 of 1,267 areas have 100 or more plant records</div>
      </Rise>
      {/* 2,000 runs: each run adds tongkat ali's rank to its bin; the bins become the range. */}
      <Say t={t} words={line('The whole ranking, run 2,000 times', T.then)} x={160} y={150} size={58} align="left" width={1600} out={histOut} />
      <Say t={t} words={line('different weights, different data each time', T.different)} x={160} y={225} size={38} align="left" width={1600} weight={500} color={C.secondary} out={histOut} />
      {t > T.runs - 0.3 && t < histOut + 0.5 && (
        <svg width={1920} height={1080} style={{ position: 'absolute', left: 0, top: 0, opacity: 1 - progress(t, histOut, histOut + 0.3) }}>
          <text x={160} y={380} fontFamily={SANS} fontWeight={600} fontSize={30} fill={C.secondary}>Run</text>
          <text x={160} y={460} fontFamily={SERIF} fontWeight={600} fontSize={84} fill={C.ink} style={{ fontVariantNumeric: 'tabular-nums' }}>{runNo.toLocaleString('en-US')}</text>
          <text x={160} y={510} fontFamily={SANS} fontWeight={500} fontSize={26} fill={C.tertiary}>tongkat ali's rank in each run</text>
          <line x1={480} x2={1500} y1={base} y2={base} stroke={C.ink} strokeWidth={2} />
          {RUNS.map((n, i) => {
            const h = (n / max) * 420 * fill;
            const inRange = i < 5;
            return (
              <g key={i}>
                <rect x={bx(i)} y={base - h} width={100} height={h} fill={k > 0 && !inRange ? '#C9CFD6' : i === 1 ? C.accent : C.ink} opacity={k > 0 && !inRange ? 0.8 : 1} />
                <text x={bx(i) + 50} y={base + 44} textAnchor="middle" fontFamily={SANS} fontWeight={600} fontSize={30} fill={C.secondary}>{['1st', '2nd', '3rd', '4th', '5th', '6th', '7th'][i]}</text>
                {fill > 0.98 && <text x={bx(i) + 50} y={base - h - 14} textAnchor="middle" fontFamily={SANS} fontWeight={600} fontSize={26} fill={C.tertiary}>{n}</text>}
              </g>
            );
          })}
          {k > 0 && (
            <g opacity={k}>
              <path d={`M${bx(0)},${base + 80} v14 H${bx(4) + 100 * k + (bx(0) - bx(0)) * (1 - k)} v-14`} fill="none" stroke={C.accent} strokeWidth={4} />
              <text x={(bx(0) + bx(4) + 100) / 2} y={base + 140} textAnchor="middle" fontFamily={SANS} fontWeight={700} fontSize={34} fill={C.accent}>Ranked 2nd, could be anywhere from 1st to 5th</text>
            </g>
          )}
        </svg>
      )}
      <Say t={t} words={line('A range, not a single number.', T.range - 0.3)} x={160} y={600} size={44} align="left" width={300} out={histOut} />
    </>
  );
};

// ------------------------------------------------------------------- 6. the app as one journey, real clicks as cuts
type Cam = Array<[number, { x: number; y: number; w: number }, ((x: number) => number)?]>;
const ORDER = ['atlas', 'profile', 'brief', 'weights', 'seasons'] as const;
const Demo: React.FC<{ t: number }> = ({ t }) => {
  const start = at.atlas;
  const end = DEMO_END;
  if (t < start - 0.6 || t > end + 0.8) return null;
  const until = (i: number) => (i < ORDER.length - 1 ? at[ORDER[i + 1]] : end);
  const zoomRank = { x: 860, y: 120, w: 1060 };
  const cams: Record<string, Cam> = {
    atlas: [[0, FULL]],
    profile: [[0, FULL], [T.second - 0.7, FULL], [T.second + 0.3, zoomRank], [at.brief - 1.2, zoomRank], [at.brief - 0.4, FULL]],
    brief: [[0, FULL], [at.brief + 0.4, FULL], [at.brief + 1.5, { x: 360, y: 40, w: 1200 }]],
    weights: [[0, FULL]],
    seasons: [[0, FULL]],
  };
  const rank = onPlane(box('profile', 'rank'), zoomRank);
  const sb = at.seasons;
  const playing = sb + mark('seasons', 'playing');
  const cal = sb + mark('seasons', 'calendar');
  return (
    <>
      {ORDER.map((n, i) => {
        const a = at[n];
        const b = until(i);
        if (t < a - 0.05 || t > b + 0.5) return null;
        const py: Array<[number, number]> = n === 'atlas' ? [[a - 0.45, 1500], [a, PLANE_Y]] : n === 'seasons' ? [[0, PLANE_Y], [end - 0.2, PLANE_Y], [end + 0.35, -620]] : [[0, PLANE_Y]];
        return <Screen key={n} t={t} src={n} at={a} from={0} dur={Math.min(len(n), b + 0.5 - a)} cam={cams[n]} px={[[0, 960]]} py={py} pw={[[0, PLANE_W]]} radius={6} />;
      })}
      <Caption t={t} at={T.broad} out={at.profile - 0.3}>Broad hexagons, never exact spots</Caption>
      <Ring t={t} at={T.second + 0.35} out={at.brief - 0.5} {...rank} />
      <Caption t={t} at={T.second} out={at.brief - 0.3}>Ranked 2nd of 29, anywhere from 1st to 5th</Caption>
      <Caption t={t} at={T.field - 0.2} out={at.weights - 0.3}>One page for the field</Caption>
      <Caption t={t} at={T.slider} out={at.seasons - 0.3}>Your weights, re-ranked live</Caption>
      <Caption t={t} at={Math.max(at.seasons + 0.4, T.year)} out={T.flower - 0.4}>New: a year in the field</Caption>
      <Ring t={t} at={playing - 0.9} out={playing + 0.4} {...onPlane(box('seasons', 'play'))} />
      <Caption t={t} at={T.flower - 0.2} out={cal - 0.3}>Where it was recorded, month by month</Caption>
      <Caption t={t} at={Math.max(cal + 0.2, T.pile - 0.2)} out={end - 0.3}>Every month weighed against survey effort</Caption>
    </>
  );
};

// ----------------------------------------------------------- 7. checked against expert sources, where to look next
const NB = [0, 1, 2, 3, 4, 5].map((j) => {
  const a = (Math.PI / 180) * (60 * j + 30);
  return { dx: Math.cos(a) * 1.732, dy: Math.sin(a) * 1.732 };
});
const hex = (x: number, y: number, r: number) =>
  Array.from({ length: 6 }, (_, i) => {
    const a = (Math.PI / 180) * (60 * i);
    return `${(x + r * Math.cos(a)).toFixed(1)},${(y + r * Math.sin(a)).toFixed(1)}`;
  }).join(' ');
const Check: React.FC<{ t: number }> = ({ t }) => {
  if (t < T.name - 0.5 || t > T.fivePlants + 0.5) return null;
  const wfoOut = cue('every', 5) - 0.3;
  const cdfpOut = at.check - 0.3;
  const s = at.check;
  const mapOut = T.across - 0.35;
  const ringOut = T.fivePlants - 0.4;
  return (
    <>
      <Count t={t} at={T.name} out={wfoOut} from={0} to={50} dur={0.9} x={960} y={250} size={230} suffix=" of 51" />
      <Say t={t} words={line('names matched in World Flora Online', cue('world'))} x={960} y={600} size={52} out={wfoOut} />
      <Say t={t} words={[{ w: 'all accepted names · the one left, Mentha × piperita, is not ranked', at: cue('online') + 0.3 }]} x={960} y={680} size={30} weight={500} color={C.tertiary} out={wfoOut} />
      <Say t={t} words={line("Co's Digital Flora of the Philippines", T.digital - 0.5)} x={960} y={420} size={84} out={cdfpOut} />
      <Say t={t} words={line('the expert checklist built on the work of botanist Leonardo L. Co', T.leonardo - 0.6)} x={960} y={540} size={40} weight={500} color={C.secondary} out={cdfpOut} />
      <Say t={t} words={[{ w: 'Pelser, Barcelona & Nickrent (eds.) · philippineplants.org', at: T.leonardo + 0.2 }]} x={960} y={610} size={28} weight={500} color={C.tertiary} out={cdfpOut} />
      {t >= s - 0.1 && t <= CHECK_END + 0.5 && (
        <Screen t={t} src="check" at={s} from={0} dur={CHECK_END + 0.5 - s} cam={[[0, FULL]]} radius={6}
          px={[[0, 960]]} py={[[s - 0.45, 1500], [s, PLANE_Y], [CHECK_END - 0.2, PLANE_Y], [CHECK_END + 0.35, -620]]} pw={[[0, PLANE_W]]} />
      )}
      <Ring t={t} at={T.agrees} out={CHECK_END - 0.3} {...onPlane(box('check', 'cdfp'))} />
      <Caption t={t} at={T.agrees} out={CHECK_END - 0.3}>{"Co's Flora agrees: native, and Endangered"}</Caption>
      {/* Where to look next: the islands Co's Flora documents it on, with no open records, on the real map. */}
      {t > T.but2 - 0.2 && t < mapOut + 0.5 && (
        <div style={{ opacity: io(t, T.but2, mapOut, 0.6).p * (1 - io(t, T.but2, mapOut).q) }}>
          <PH t={t} x={1100} y={40} scale={1.0} tongkat={1} tongkatAt={T.but2 - 1} look={progress(t, T.mindoro - 0.2, cue('Grande,') + 0.3)} />
        </div>
      )}
      <Rise t={t} at={T.but2} out={mapOut} style={{ left: 160, top: 300, width: 820 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16, fontSize: 34, fontWeight: 600, color: C.secondary }}>
          <i style={{ width: 24, height: 24, background: C.accent, display: 'inline-block' }} /> tongkat ali's five open records
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16, fontSize: 34, fontWeight: 600, color: C.secondary, marginTop: 18 }}>
          <i style={{ width: 22, height: 22, border: `3px dashed ${C.ink}`, borderRadius: 22, display: 'inline-block' }} /> documented in Co's Flora, no open records
        </div>
      </Rise>
      <Say t={t} words={line('Where to look next', T.look - 0.2)} x={160} y={560} size={96} align="left" width={900} out={mapOut} />
      {(() => {
        const a = io(t, T.across, ringOut, 0.5);
        if (!a.shown) return null;
        const r = 66;
        const cx = 500;
        const cy = 560;
        return (
          <svg width={1920} height={1080} style={{ position: 'absolute', left: 0, top: 0, opacity: a.p * (1 - a.q) }}>
            <polygon points={hex(cx, cy, r * 0.95)} fill={C.accent} />
            {NB.map((n, j) => {
              const p = progress(t, T.across + 0.2 + j * 0.12, T.across + 0.5 + j * 0.12, land);
              const searched = j === 1 || j === 4;
              return <polygon key={j} points={hex(cx + n.dx * r, cy + n.dy * r, r * 0.95)} fill={searched ? C.ink : '#C9CFD6'} opacity={p} />;
            })}
            <text x={cx} y={cy + 3.3 * r} textAnchor="middle" fontFamily={SANS} fontSize={28} fontWeight={500} fill={C.secondary}>a known record and the six areas around it</text>
          </svg>
        );
      })()}
      <Count t={t} at={T.two} out={ringOut} from={0} to={66} dur={1.0} x={900} y={250} size={230} suffix="%" color={C.accent} align="left" />
      <Say t={t} words={line('of the land next to known records has barely been searched', T.two + 0.3)} x={906} y={590} size={46} align="left" width={900} weight={500} color={C.secondary} out={ringOut} />
      <Say t={t} words={[{ w: '2,992 of 4,542 neighbouring areas · all 29 ranked plants', at: T.barely }]} x={906} y={720} size={28} align="left" width={900} weight={500} color={C.tertiary} out={ringOut} />
    </>
  );
};

// ---------------------------------------------------------------------------------------------- 8. five plants
const FIVE = [
  { photo: 'cinnamomum-mercadoi', name: 'Kalingag', bin: 'Cinnamomum mercadoi', rank: 2, lo: 1, hi: 3, cue: () => cue('Kalingag,') },
  { photo: 'eurycoma-longifolia', name: 'Tongkat ali', bin: 'Eurycoma longifolia', rank: 2, lo: 1, hi: 5, cue: () => cue('Tonkat', 4) },
  { photo: 'calophyllum-blancoi', name: 'Bitaog', bin: 'Calophyllum blancoi', rank: 3, lo: 1, hi: 4, cue: () => cue('Bitaug,') },
  { photo: 'ficus-nota', name: 'Tibig', bin: 'Ficus nota', rank: 4, lo: 3, hi: 5, cue: () => cue('Tibig,') },
  { photo: 'goniothalamus-amuyon', name: 'Amuyon', bin: 'Goniothalamus amuyon', rank: 5, lo: 2, hi: 9, cue: () => cue('Amuyon.') },
];
const Results: React.FC<{ t: number }> = ({ t }) => {
  if (t < T.fivePlants - 0.3 || t > T.medical) return null;
  const out = T.medical - 0.7;
  const sx = (r: number) => 1180 + ((r - 1) / 9) * 560;
  return (
    <>
      <Say t={t} words={line('Five plants need ^attention now', T.fivePlants)} x={160} y={130} size={64} align="left" width={1600} out={out} />
      <Sheet t={t} at={T.fivePlants + 0.3} out={out} x={160} y={200} w={1600} pad={0}>
        <div style={{ display: 'flex', padding: '18px 36px', fontSize: 24, fontWeight: 600, color: C.tertiary, borderBottom: `1px solid ${RULE}` }}>
          <span style={{ width: 860 }}>Plant</span>
          <span>Rank across 2,000 runs (1st to 10th)</span>
        </div>
        {FIVE.map((p, i) => {
          const r = io(t, p.cue() - 0.1);
          const bar = progress(t, p.cue(), p.cue() + 0.6, settle);
          return (
            <div key={p.name} style={{ position: 'relative', display: 'flex', alignItems: 'center', height: 128, padding: '0 36px', borderTop: i ? `1px solid ${RULE}` : undefined, opacity: 0.25 + 0.75 * r.p }}>
              <div style={{ width: 96, height: 96, borderRadius: 3, overflow: 'hidden', flex: 'none' }}>
                <Img src={staticFile(`photos/${p.photo}.jpg`)} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
              </div>
              <div style={{ marginLeft: 28 }}>
                <div style={{ fontFamily: SERIF, fontWeight: 600, fontSize: 46, letterSpacing: -0.8, color: C.ink }}>{p.name}</div>
                <div style={{ fontFamily: SERIF, fontStyle: 'italic', fontSize: 24, color: C.tertiary }}>{p.bin}</div>
              </div>
              <svg width={1920} height={128} style={{ position: 'absolute', left: -160, top: 0 }}>
                <line x1={sx(1)} x2={sx(10)} y1={64} y2={64} stroke={RULE} strokeWidth={2} />
                <line x1={sx(p.rank) - (sx(p.rank) - sx(p.lo)) * bar} x2={sx(p.rank) + (sx(p.hi) - sx(p.rank)) * bar} y1={64} y2={64} stroke={C.accent} strokeWidth={10} strokeLinecap="round" opacity={0.45} />
                <circle cx={sx(p.rank)} cy={64} r={12 * r.p} fill={C.accent} />
                <text x={sx(10) + 40} y={74} fontFamily={SANS} fontWeight={600} fontSize={28} fill={C.secondary} opacity={bar}>
                  {['', '1st', '2nd', '3rd', '4th', '5th'][p.rank]} ({p.lo === 1 ? '1st' : p.lo === 2 ? '2nd' : '3rd'} to {['', '1st', '2nd', '3rd', '4th', '5th', '6th', '7th', '8th', '9th'][p.hi]})
                </text>
              </svg>
            </div>
          );
        })}
      </Sheet>
      <Say t={t} words={line('Change the math, and the order barely moves.', T.change)} x={160} y={1000} size={40} align="left" width={1600} weight={500} color={C.secondary} out={out} />
      <Say t={t} words={[{ w: 'Photos: iNaturalist observers, CC BY', at: T.fivePlants + 0.6 }]} x={1760} y={1000} size={20} align="left" width={400} weight={500} color={C.tertiary} out={out} />
    </>
  );
};

// ------------------------------------------------------------------------------------- 9. limits, then the close
const Limits: React.FC<{ t: number }> = ({ t }) => {
  if (t < T.medical - 0.8 || t > T.name2 + 0.4) return null;
  const out = T.name2 - 0.45;
  return (
    <>
      <Say t={t} words={line('Not medical advice.', T.medical - 0.4)} x={960} y={430} size={84} out={out} />
      <Say t={t} words={line('Harvest data still needs experts in the field.', T.experts - 0.6)} x={960} y={580} size={54} weight={500} color={C.secondary} out={out} />
    </>
  );
};

const Close: React.FC<{ t: number }> = ({ t }) => {
  if (t < T.name2 - 0.5) return null;
  return (
    <>
      <Photo t={t} at={T.name2 - 0.2} src="eurycoma-longifolia" x={1300} y={170} w={460} h={620} />
      <Say t={t} words={[{ w: 'Harvester', at: T.name2 }, { w: 'Risk', at: cue('Risk', 2) }, { w: 'Atlas', at: cue('Atlas.', 3) }]} x={160} y={300} size={112} align="left" width={1100} />
      <Say t={t} words={line('Which plants first, where to look next, and how sure we are.', T.which)} x={164} y={430} size={42} align="left" width={1060} weight={500} color={C.secondary} />
      <Say t={t} words={[{ w: 'harvester-risk-atlas.vercel.app', at: cue('sure', 2) + 0.4 }]} x={164} y={560} size={52} align="left" width={1100} color={C.accent} />
      <Say t={t} words={line('Help us protect the plants that heal us.', T.help - 0.1)} x={164} y={690} size={52} align="left" width={1100} />
      <Say t={t} words={[{ w: 'Yuan Andrei C. Mariano · Alicia Jhyle Vilale · EthnoHack 2026', at: T.help + 1.2 }]} x={164} y={840} size={28} align="left" width={1100} weight={500} color={C.tertiary} />
    </>
  );
};

export const Film: React.FC = () => {
  const t = useCurrentFrame() / FPS;
  return (
    <AbsoluteFill style={{ background: PAPER, fontFamily: SANS }}>
      <Hook t={t} />
      <OpeningMap t={t} />
      <Problem t={t} />
      <Tongkat t={t} />
      <Reveal t={t} />
      <Method t={t} />
      <Demo t={t} />
      <Check t={t} />
      <Results t={t} />
      <Limits t={t} />
      <Close t={t} />
      <Audio src={staticFile('audio/vo-master-rt.wav')} />
    </AbsoluteFill>
  );
};

export { DURATION, PH_H, PH_W, SHEET, glide };
