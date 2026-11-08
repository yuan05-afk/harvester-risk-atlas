// Harvester Risk Atlas: the EthnoHack pitch, 2:19 at 60 fps. AIDA, one continuous take:
//   Attention  hook (night) -> tree cover lost a day, harvest unmeasured -> tongkat ali's five records
//   Interest   the five records become the app's own opening -> three questions -> 2,000 re-runs -> a range
//   Desire     the live app as one journey (atlas -> plant -> field brief -> weights), real clicks as cuts
//              -> what is new: names checked in World Flora Online, plants against Co's Digital Flora, where to look
//              next, two thirds of the land next to records barely searched -> five plants
//   Action     limits, the name, the question it answers
// Picture keys on the narration's measured words (timing.ts). Voice only, no music.
import React from 'react';
import { AbsoluteFill, Audio, staticFile, useCurrentFrame } from 'remotion';
import '@fontsource-variable/atkinson-hyperlegible-next';
import '@fontsource-variable/fraunces';
import '@fontsource-variable/fraunces/full-italic.css';
import { C, SANS, SERIF } from './lib/theme';
import { drift, glide, keys, progress, settle } from './lib/motion';
import { Haze } from './components/Haze';
import { Words } from './components/Words';
import { Screen } from './components/Screen';
import { DURATION, FPS, cue, line } from './timing';
import takes from './takes.json';
import { Counter, Hex, HexField, Pill, Plate, PlantCard, RankStrip, Rail, Tag, arrive, look } from './parts';

const FULL = { x: 0, y: 0, w: 1920 };

// ------------------------------------------------------------------------------------------------------------ cues
const T = {
  most: cue('Most'),
  almost: cue('almost') - 0.12,
  inPh: cue('In'),
  ha: cue('175'),
  but: cue('but'),
  so: cue('So'),
  where: cue('where'),
  take: cue('Take'),
  roots: cue('roots'),
  officially: cue('officially'),
  yet: cue('Yet'),
  reliable: cue('reliable'),
  this: cue('This'),
  grow: cue('grow,'),
  asks: cue('asks') - 0.3,
  rare: cue('rare'),
  harvesting: cue('harvesting'),
  home: cue('home'),
  measures: cue('measures', 2),
  reruns: cue('reruns'),
  range: cue('range,'),
  pick: cue('Pick'),
  broad: cue('Broad'),
  now: cue('Now'),
  checked: cue('checked'),
  against2: cue('against', 2),
  agrees: cue('agrees'),
  mindoro: cue('Mindoro,'),
  next1: cue('next.'),
  across: cue('Across'),
  two: cue('two'),
  turns: cue('turns'),
  five: cue('Five', 2),
  change: cue('Change'),
  medical: cue('medical'),
  harvest2: cue('harvest', 2),
  name: cue('Harvester', 3),
  which: cue('Which', 2),
  sure2: cue('sure.', 2),
  help: cue('Help', 2),
};

// Footage: the demo is one user's journey, recorded at 60 fps (tools/vcap.mjs, tools/takes.mjs). Each take starts on
// the frame after the previous take's click, so the click itself is the cut. takes.json holds lengths and click frames.
type Take = { frames: number; clicks: number[]; marks?: Record<string, number> };
const TK = takes as Record<string, Take>;
const len = (n: string) => TK[n].frames / FPS;
const clickAt = (n: string, i = 0) => TK[n].clicks[i] / FPS;
const mark = (n: string, m: string) => (TK[n].marks?.[m] ?? 0) / FPS;
const chain = (() => {
  const at: Record<string, number> = {};
  at.atlas = T.pick - 0.3;
  at.profile = at.atlas + clickAt('atlas', 1) + 0.1;
  at.brief = at.profile + clickAt('profile') + 0.1;
  at.weights = at.brief + len('brief') - 0.35; // the printed sheet drops away; How it works rises
  return at;
})();
const DEMO_END = T.now - 0.35;
// The cross-check take: its "Co's Digital Flora" row lands on "agrees".
const CHECK_AT = T.agrees - mark('check', 'cdfp');
const CHECK_END = Math.min(CHECK_AT + len('check'), T.next1 + 0.2);

// --------------------------------------------------------------------------------------------- 1. hook, at night
const Hook: React.FC<{ t: number }> = ({ t }) => {
  if (t > T.inPh + 0.5) return null;
  const photoDim = progress(t, T.almost, T.almost + 0.8, settle);
  const night = { color: '#F2F4F5' };
  return (
    <>
      <Words t={t} words={line('Up to ^4 ^billion people rely on herbal medicine.').map((w) => (w.blue ? { ...w, blue: false, c: C.highlight } : w))} x={960} y={540} size={84} exit={T.most - 0.35} {...night} />
      <Plate t={t} at={T.most - 0.1} out={T.almost - 0.35} src="cinnamomum-mercadoi" x={960} y={455} w={600} h={600} dim={photoDim} scaleIn={1.18} />
      <Words t={t} words={line('Most medicinal plants in trade are taken from the *wild.', T.most)} x={960} y={900} size={54} exit={T.almost - 0.35} {...night} />
      <Words t={t} words={line('And almost no one is counting what is *left.', T.almost).map((w) => (w.serif ? { ...w, c: C.accentSoft } : w))} x={960} y={540} size={92} exit={T.inPh - 0.6} {...night} />
    </>
  );
};

// ------------------------------------------------------------------------------------------- 2. the problem
const Problem: React.FC<{ t: number }> = ({ t }) => {
  if (t < T.inPh - 0.6 || t > T.take + 0.5) return null;
  return (
    <>
      <Words t={t} words={line('In the *Philippines', T.inPh)} x={960} y={250} size={64} exit={T.but - 0.4} />
      <Counter t={t} at={T.ha} out={T.but - 0.4} to={175} dur={1.0} y={360} size={230} suffix=" ha" color={C.habitat} label={<>of tree cover lost <b style={{ color: C.ink }}>every day</b></>} labelAt={cue('tree')} />
      {(() => {
        const a = arrive(t, T.but, T.so - 0.35, 0.5);
        if (!a.shown) return null;
        return (
          <div style={{ position: 'absolute', left: 960 - 520, top: 360, width: 1040, ...look(a) }}>
            <div style={{ background: C.card, borderRadius: 20, padding: '40px 52px', boxShadow: '0 30px 80px rgba(20,40,32,0.16)', fontFamily: SANS }}>
              {[
                ['Where it grows', 'GBIF records', C.habitat],
                ['How threatened', "DENR's list", C.habitat],
                ['How much is harvested', 'not measured', C.accent],
              ].map(([k, v, col], i) => {
                const r = arrive(t, T.but + 0.2 + i * 0.35);
                return (
                  <div key={k} style={{ display: 'flex', alignItems: 'center', gap: 22, padding: '22px 0', borderTop: i ? `1px solid ${C.hairline}` : undefined, ...look(r) }}>
                    <span style={{ width: 30, height: 30, borderRadius: 30, flex: 'none', border: i === 2 ? `3px dashed ${C.accent}` : 'none', background: i === 2 ? 'transparent' : C.habitat }} />
                    <span style={{ fontSize: 46, fontWeight: 600, color: C.ink, letterSpacing: -0.6 }}>{k}</span>
                    <span style={{ marginLeft: 'auto', fontSize: 34, fontWeight: 600, color: col as string }}>{v}</span>
                  </div>
                );
              })}
            </div>
          </div>
        );
      })()}
      <div style={{ position: 'absolute', left: 0, right: 0, top: 360, display: 'flex', justifyContent: 'center', gap: 28 }}>
        <Pill t={t} at={cue('ranger')} out={T.take - 0.6}>a ranger</Pill>
        <Pill t={t} at={cue('harvester')} out={T.take - 0.6}>a harvester</Pill>
      </div>
      <Words t={t} words={line('Where should they even *start?', T.where)} x={960} y={600} size={96} exit={T.take - 0.6} />
    </>
  );
};

// --------------------------------------------------------------------------------- 3. tongkat ali: five records
const HEX5 = [0, 1, 2, 3, 4].map((i) => ({ x: 1130 + i * 116, y: 720 }));
const Tongkat: React.FC<{ t: number }> = ({ t }) => {
  if (t < T.take - 0.5 || t > T.this + 0.6) return null;
  const out = T.this - 1.0;
  // The five hexagons are carried into the next beat: they rise to the centre and become the app's opening.
  const carry = progress(t, out - 0.1, T.this - 0.2, glide);
  const end = progress(t, T.this - 0.35, T.this + 0.1, settle);
  return (
    <>
      <Plate t={t} at={T.take - 0.2} out={out} src="eurycoma-longifolia" x={560} y={520} w={540} h={720} credit="Tongkat ali · Steven Bodzin, CC BY 4.0, iNaturalist" />
      <Words t={t} words={line('Tongkat *ali', T.take)} x={1060} y={250} size={112} align="left" maxWidth={800} exit={out} />
      <Words t={t} words={line('Roots dug up and sold.', T.roots)} x={1064} y={380} size={50} align="left" maxWidth={800} exit={out} weight={500} color={C.secondary} />
      {(() => {
        const a = arrive(t, T.officially, out);
        if (!a.shown) return null;
        return (
          <div style={{ position: 'absolute', left: 1064, top: 450, ...look(a), border: `4px solid ${C.accent}`, borderRadius: 12, padding: '10px 22px', color: C.accent, fontFamily: SANS, fontWeight: 700, fontSize: 36, transform: `${look(a).transform} rotate(-3deg)` }}>
            Officially Endangered
          </div>
        );
      })()}
      <Words t={t} words={line('Open databases hold only', T.yet + 0.4)} x={1064} y={600} size={36} align="left" maxWidth={820} exit={out} weight={500} color={C.secondary} />
      <svg width={1920} height={1080} style={{ position: 'absolute', left: 0, top: 0, opacity: 1 - end }}>
        {HEX5.map((h, i) => {
          const x = h.x + (960 - 232 + i * 116 - h.x) * carry;
          const y = h.y + (470 - h.y) * carry;
          return <Hex key={i} t={t} at={T.reliable - 0.45 + i * 0.16} x={x} y={y} r={50} fill={C.accent} />;
        })}
      </svg>
      <Words t={t} words={[{ w: 'reliable records.', at: T.reliable }]} x={1064} y={830} size={48} align="left" maxWidth={820} exit={out} />
    </>
  );
};

// ---------------------------------------------------- 4. the reveal: the app's own opening, then its promise
const Reveal: React.FC<{ t: number }> = ({ t }) => {
  const s = T.this - 0.3;
  if (t < s - 0.1 || t > T.asks + 0.6) return null;
  const leaveAt = T.asks;
  const g = s + len('intro') - 0.1;
  return (
    <>
      <Screen t={t} src="intro" at={s} from={0} dur={len('intro') - 0.05} cam={[[0, FULL]]}
        px={[[s, 960]]} py={[[s, 600], [s + 0.6, 540, settle], [g, 540], [g + 0.8, 470], [leaveAt, 470], [leaveAt + 0.5, -400]]}
        pw={[[s, 1200], [s + 0.6, 1500, settle], [g, 1500], [g + 0.8, 1260]]} />
      {t >= g && (
        <Screen t={t} src="overview" at={g} from={0.05} dur={leaveAt + 0.6 - g} cam={[[0, FULL]]}
          px={[[0, 960]]} py={[[g, 540], [g + 0.8, 470], [leaveAt, 470], [leaveAt + 0.5, -400]]} pw={[[g, 1500], [g + 0.8, 1260]]} />
      )}
      <Words t={t} words={line('where they *grow · how ^sure we are', T.grow - 0.2)} x={960} y={1000} size={54} exit={leaveAt - 0.2} />
    </>
  );
};

// ----------------------------------------------------------------------- 5. method: questions, rarity, re-runs
const Q = [
  { label: 'Rarity', q: 'How rare is it?', ink: C.rarity, at: () => T.rare },
  { label: 'Harvest harm', q: 'Does harvesting kill it?', ink: C.harvest, at: () => T.harvesting },
  { label: 'Habitat pressure', q: 'Is its home disappearing?', ink: C.habitat, at: () => T.home },
];
const Method: React.FC<{ t: number }> = ({ t }) => {
  if (t < T.asks - 0.4 || t > T.pick + 0.4) return null;
  const qOut = T.measures - 0.4;
  return (
    <>
      <Words t={t} words={line('Three *questions', cue('three'))} x={960} y={230} size={72} exit={qOut} />
      {Q.map((q, i) => {
        const a = arrive(t, q.at() - 0.1, qOut, 0.5);
        if (!a.shown) return null;
        return (
          <div key={q.label} style={{ position: 'absolute', left: 960 - 810 + i * 550, top: 380, width: 520, ...look(a) }}>
            <div style={{ background: C.card, borderRadius: 16, borderTop: `8px solid ${q.ink}`, padding: '40px 40px 48px', boxShadow: '0 30px 80px rgba(20,40,32,0.14)' }}>
              <div style={{ fontFamily: SANS, fontWeight: 700, fontSize: 34, color: q.ink }}>{q.label}</div>
              <div style={{ fontFamily: SERIF, fontWeight: 600, fontSize: 58, lineHeight: 1.08, letterSpacing: -1.2, color: C.ink, marginTop: 18 }}>{q.q}</div>
            </div>
          </div>
        );
      })}
      <Words t={t} words={line('Rarity counts only where botanists searched *well.', T.measures)} x={960} y={190} size={54} exit={T.reruns - 0.4} />
      <HexField t={t} at={T.measures} out={T.reruns - 0.4} cx={960} cy={560} r={44} cols={15} rows={6}
        kind={(i, col, row) => {
          const road = row === 2 || row === 3;
          const well = (col + row * 3) % 4 === 0 || (road && col % 2 === 0);
          return { fill: road ? C.tertiary : '#CFE0D3', stroke: t > cue('searched') && well ? C.ink : undefined };
        }} />
      <Words t={t} words={[{ w: '332', at: cue('searched') + 0.1, blue: true }, { w: 'well-searched areas of 1,267', at: cue('searched') + 0.3 }]} x={960} y={930} size={46} exit={T.reruns - 0.4} />
      <Counter t={t} at={T.reruns + 0.4} out={T.pick - 0.5} to={2000} dur={1.4} y={150} size={120} prefix="× " color={C.accent} />
      <RankStrip t={t} at={T.reruns} runFrom={T.reruns + 0.4} runTo={T.range - 0.6} resolve={T.range - 0.5} out={T.pick - 0.5} />
      <Words t={t} words={line('a ^range, not one *number.', T.range - 0.3)} x={960} y={860} size={72} exit={T.pick - 0.5} />
    </>
  );
};

// ------------------------------------------------------------------------------------- 6. the live app, one journey
type Cam = Array<[number, { x: number; y: number; w: number }, ((x: number) => number)?]>;
const ORDER = ['atlas', 'profile', 'brief', 'weights'] as const;
const Demo: React.FC<{ t: number }> = ({ t }) => {
  const start = chain.atlas;
  const end = DEMO_END;
  if (t < start - 0.6 || t > end + 0.8) return null;
  const until = (i: number) => (i < ORDER.length - 1 ? chain[ORDER[i + 1]] : end);
  const current = ORDER.findIndex((n, i) => t >= chain[n] && t < until(i));
  const py: Array<[number, number]> = [[start - 0.5, 1500], [start, 590], [end - 0.2, 590], [end + 0.35, -600]];
  const c = (n: string) => chain[n];
  const cams: Record<string, Cam> = {
    atlas: [[0, FULL], [c('atlas') + clickAt('atlas') + 1.0, FULL], [c('atlas') + clickAt('atlas') + 2.2, { x: 80, y: 120, w: 1260 }], [c('profile') - 1.9, { x: 80, y: 120, w: 1260 }], [c('profile') - 0.8, FULL]],
    profile: [[0, FULL], [cue('second') - 0.6, FULL], [cue('second') + 0.4, { x: 880, y: 110, w: 1040 }], [c('brief') - 1.4, { x: 880, y: 110, w: 1040 }], [c('brief') - 0.6, FULL]],
    brief: [[0, FULL], [c('brief') + 0.4, FULL], [c('brief') + 1.5, { x: 360, y: 40, w: 1200 }]],
    weights: [[0, FULL], [cue('slider,') - 0.2, FULL], [cue('slider,') + 0.8, { x: 140, y: 50, w: 1640 }]],
  };
  return (
    <>
      <Rail t={t} at={start + 0.4} out={end - 0.2} current={Math.max(0, current)} />
      {ORDER.map((n, i) => {
        const a = chain[n];
        const b = until(i);
        if (t < a - 0.05 || t > b + 0.45) return null;
        const drop: Array<[number, number]> = [[b - 0.05, 590], [b + 0.4, 1700]];
        const rise: Array<[number, number]> = [[a, 1700], [a + 0.45, 590]];
        const y: Array<[number, number]> = n === 'brief' ? [...py.filter(([k]) => k < b - 0.05), ...drop] : n === 'weights' ? [...rise, ...py.filter(([k]) => k > a + 0.45)] : py;
        return <Screen key={n} t={t} src={n} at={a} from={0} dur={Math.min(len(n), b + 0.45 - a)} cam={cams[n]} px={[[0, 960]]} py={y} pw={[[0, 1620]]} />;
      })}
      <Tag t={t} at={T.broad} out={c('profile') - 0.3} x={960} y={968}>Broad hexagons, never exact spots</Tag>
      <Tag t={t} at={cue('field') - 0.2} out={chain.weights - 0.4} x={960} y={968}>One A4 page for the field</Tag>
      <Tag t={t} at={cue('slider,')} out={end - 0.3} x={960} y={968}>Your weights, re-ranked live</Tag>
    </>
  );
};

// ------------------------------------------------------------------- 7. what is new: checked against experts
const NB = [0, 1, 2, 3, 4, 5].map((k) => {
  const a = (Math.PI / 180) * (60 * k);
  return { dx: Math.cos(a) * 1.732, dy: Math.sin(a) * 1.732 };
});
const New: React.FC<{ t: number }> = ({ t }) => {
  if (t < T.now - 0.4 || t > T.five + 0.4) return null;
  const wfoOut = T.against2 - 0.35;
  const cdfpOut = CHECK_AT - 0.3;
  const ringAt = CHECK_END - 0.1;
  const ringOut = T.five - 0.45;
  const s = CHECK_AT;
  return (
    <>
      <Words t={t} words={line('Now, what is *new?', T.now)} x={960} y={540} size={104} exit={cue('Every', 3) - 0.25} />
      <Counter t={t} at={T.checked} out={wfoOut} to={50} dur={1.0} y={300} size={220} suffix=" of 51" label="names matched in World Flora Online, all accepted names" labelAt={T.checked + 0.6} />
      <Words t={t} words={[{ w: 'The one left, Mentha × piperita, is flagged and not ranked.', at: T.checked + 1.2 }]} x={960} y={760} size={34} weight={500} color={C.tertiary} exit={wfoOut} />
      <Words t={t} words={line("Co's Digital Flora of the *Philippines", T.against2)} x={960} y={430} size={86} exit={cdfpOut} />
      <Words t={t} words={[{ w: 'the expert checklist built on the work of botanist Leonardo L. Co', at: T.against2 + 0.9 }]} x={960} y={560} size={40} weight={500} color={C.secondary} exit={cdfpOut} />
      <Words t={t} words={[{ w: 'Pelser, Barcelona & Nickrent (eds.), 2011 onwards · philippineplants.org', at: T.against2 + 1.4 }]} x={960} y={640} size={28} weight={500} color={C.tertiary} exit={cdfpOut} />
      {t >= s - 0.1 && t <= CHECK_END + 0.5 && (
        <Screen t={t} src="check" at={s} from={0} dur={CHECK_END + 0.45 - s}
          cam={[[0, FULL], [T.agrees - 0.7, FULL], [T.agrees + 0.3, { x: 100, y: 60, w: 1500 }], [T.mindoro - 1.4, { x: 100, y: 60, w: 1500 }], [T.mindoro - 0.4, { x: 100, y: 200, w: 1500 }]]}
          px={[[0, 960]]} py={[[s - 0.4, 1500], [s, 560], [CHECK_END - 0.2, 560], [CHECK_END + 0.3, -600]]} pw={[[0, 1600]]} />
      )}
      <Tag t={t} at={T.agrees + 0.3} out={T.mindoro - 0.6} x={960} y={985}>Co's Flora agrees: native, and Endangered</Tag>
      <Tag t={t} at={T.mindoro} out={CHECK_END - 0.2} x={960} y={985}>Mindoro · Homonhon · Bucas Grande: documented, no open records</Tag>
      {/* Two thirds of the land next to known records barely searched: one record and its six neighbours. */}
      {(() => {
        const a = arrive(t, ringAt, ringOut, 0.5);
        if (!a.shown) return null;
        const r = 62;
        const cx = 520;
        const cy = 540;
        return (
          <svg width={1920} height={1080} style={{ position: 'absolute', left: 0, top: 0, ...look(a) }}>
            <Hex t={t} at={ringAt} x={cx} y={cy} r={r * 0.94} fill={C.accent} />
            {NB.map((n, k) => (
              <Hex key={k} t={t} at={ringAt + 0.25 + k * 0.12} x={cx + n.dx * r} y={cy + n.dy * r} r={r * 0.94} fill={k === 1 || k === 4 ? '#7FA58A' : '#D6DAD8'} stroke={k === 1 || k === 4 ? undefined : C.tertiary} />
            ))}
            <text x={cx} y={cy + 3.2 * r} textAnchor="middle" fontFamily={SANS} fontSize={28} fill={C.secondary}>a known record and its neighbours</text>
          </svg>
        );
      })()}
      <div style={{ position: 'absolute', left: 820, width: 980, top: 0 }}>
        <Counter t={t} at={T.two} out={ringOut} from={0} to={66} dur={1.1} y={300} size={200} suffix="%" color={C.accent} />
      </div>
      <Words t={t} words={line('of the land next to known records has barely been searched', T.two + 0.3)} x={1310} y={600} size={42} maxWidth={940} exit={ringOut} weight={500} color={C.secondary} />
      <Words t={t} words={[{ w: '2,992 of 4,542 neighbouring areas · 29 ranked plants', at: cue('searched.', 2) }]} x={1310} y={700} size={28} maxWidth={940} exit={ringOut} weight={500} color={C.tertiary} />
      <Words t={t} words={line('A ranking becomes a *survey ^plan.', T.turns - 0.2)} x={960} y={900} size={64} exit={ringOut} />
    </>
  );
};

// ------------------------------------------------------------------------------------------ 8. what we found
const Results: React.FC<{ t: number }> = ({ t }) => {
  if (t < T.five - 0.3 || t > T.medical) return null;
  const out = T.medical - 0.8;
  return (
    <>
      <Words t={t} words={line('Five plants need ^attention ^now.', T.five)} x={960} y={190} size={72} exit={out} />
      <PlantCard t={t} at={cue('Kalingag,')} out={out} x={960 - 680} photo="cinnamomum-mercadoi" name="Kalingag" bin="Cinnamomum mercadoi" rank="2nd" range="(1st–3rd)" why="Found only in the Philippines." />
      <PlantCard t={t} at={cue('Toncat', 4)} out={out} x={960 - 340} photo="eurycoma-longifolia" name="Tongkat ali" bin="Eurycoma longifolia" rank="2nd" range="(1st–5th)" why="Roots dug up. Endangered." />
      <PlantCard t={t} at={cue('Bitaug,')} out={out} x={960} photo="calophyllum-blancoi" name="Bitaog" bin="Calophyllum blancoi" rank="3rd" range="(1st–4th)" why="Bark and sap taken." />
      <PlantCard t={t} at={cue('Tibig,')} out={out} x={960 + 340} photo="ficus-nota" name="Tibig" bin="Ficus nota" rank="4th" range="(3rd–5th)" why="A wild fig; bark gathered." />
      <PlantCard t={t} at={cue('Amuion.')} out={out} x={960 + 680} photo="goniothalamus-amuyon" name="Amuyon" bin="Goniothalamus amuyon" rank="5th" range="(2nd–9th)" why="Only 6 reliable records." />
      <Words t={t} words={line('Change the math, and the order barely *moves.', T.change)} x={960} y={985} size={44} exit={out} weight={500} color={C.secondary} />
    </>
  );
};

// ------------------------------------------------------------------------------------ 9. limits, then close
const Limits: React.FC<{ t: number }> = ({ t }) => {
  if (t < T.medical - 0.8 || t > T.name + 0.4) return null;
  const out = T.name - 0.5;
  return (
    <>
      <Words t={t} words={line('Not medical advice.', T.medical - 0.4)} x={960} y={420} size={78} exit={out} />
      <Words t={t} words={line('Harvest data still needs ^experts in the *field.', T.harvest2 - 0.2)} x={960} y={600} size={56} exit={out} weight={500} color={C.secondary} />
    </>
  );
};

const Close: React.FC<{ t: number }> = ({ t }) => {
  if (t < T.name - 0.5) return null;
  // A slow push through the close, so the last frame is still moving when the film ends.
  const push = 1 + 0.06 * progress(t, T.name, DURATION, (x) => x);
  return (
    <AbsoluteFill style={{ transform: `scale(${push.toFixed(5)})`, transformOrigin: '42% 52%' }}>
      <Plate t={t} at={T.name - 0.2} src="cinnamomum-mercadoi" x={1500} y={540} w={420} h={560} scaleIn={1.1} />
      <Words t={t} words={[{ w: 'Harvester', at: T.name }, { w: 'Risk', at: cue('risk', 2) }, { w: 'Atlas', at: cue('Atlas.', 4) }]} x={180} y={330} size={118} align="left" maxWidth={1100} />
      <Words t={t} words={line('Which plants first, where to look *next, and how sure.', T.which)} x={186} y={480} size={42} align="left" maxWidth={1080} weight={500} color={C.secondary} />
      <Words t={t} words={[{ w: 'harvester-risk-atlas.vercel.app', at: T.sure2 + 0.3 }]} x={186} y={630} size={48} align="left" maxWidth={1100} color={C.accent} />
      <Words t={t} words={line('Help us protect the plants that *heal us.', T.help - 0.1)} x={186} y={750} size={50} align="left" maxWidth={1100} />
      <Words t={t} words={[{ w: 'Yuan Andrei C. Mariano · Alicia Jhyle Vilale · EthnoHack 2026', at: T.help + 1.2 }]} x={186} y={890} size={28} align="left" maxWidth={1100} weight={500} color={C.tertiary} />
    </AbsoluteFill>
  );
};

export const Film: React.FC = () => {
  const t = useCurrentFrame() / FPS;
  const dark = keys(t, [[0, 1], [T.inPh - 1.0, 1], [T.inPh - 0.1, 0]]);
  const d = drift(t, 5);
  return (
    <AbsoluteFill style={{ background: C.haze1, fontFamily: SANS }}>
      <Haze t={t} dark={dark} />
      {/* One hand-held camera over everything: a slow float and breath, so no held frame is dead. */}
      <AbsoluteFill style={{ transform: `translate(${d.x.toFixed(2)}px, ${d.y.toFixed(2)}px) scale(${(1.012 + 0.006 * Math.sin(t * 0.42)).toFixed(5)})` }}>
        <Hook t={t} />
        <Problem t={t} />
        <Tongkat t={t} />
        <Reveal t={t} />
        <Method t={t} />
        <Demo t={t} />
        <New t={t} />
        <Results t={t} />
        <Limits t={t} />
        <Close t={t} />
      </AbsoluteFill>
      <Audio src={staticFile('audio/vo-master-rt.wav')} />
    </AbsoluteFill>
  );
};
