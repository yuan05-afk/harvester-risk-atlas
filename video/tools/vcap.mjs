// Frame-exact 60 fps capture of the real app (Chrome headless shell, begin-frame control).
//
//   node tools/vcap.mjs <clip> [<clip> ...]          clips are defined in tools/takes.mjs
//
// Chrome draws nothing on its own: each frame is produced by HeadlessExperimental.beginFrame, which advances the page's
// clock by exactly 1/60 s and returns that frame. Animations, map fly-tos and scrolls are therefore recorded at a true
// 60 fps however slow the machine is. The cursor is a person's, not a tween: every move follows a curved, minimum-jerk
// path with a small overshoot, tremor and a dwell before each press, and its position is dispatched to the page every
// frame, so hovers, the pointer hand and clicks are the page's real responses. Frames go to capture60/<clip>/NNNNN.jpg.
import { chromium } from 'playwright-core';
import { mkdirSync, rmSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { TAKES } from './takes.mjs';

const BASE = process.env.BASE_URL ?? 'http://localhost:4173';
const DPR = 1.5;
const ROOT = new URL('../capture60/', import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, '$1');
const SHELL = process.env.HEADLESS_SHELL ?? 'C:/Users/Yuan/AppData/Local/ms-playwright/chromium_headless_shell-1248/chrome-headless-shell-win64/chrome-headless-shell.exe';
const FRAME = 1000 / 60;

const ctx = await chromium.launchPersistentContext(join(ROOT, '_profile'), {
  executablePath: SHELL,
  headless: true,
  viewport: null,
  args: ['--deterministic-mode', '--enable-begin-frame-control', '--run-all-compositor-stages-before-draw', '--disable-new-content-rendering-timeout', '--disable-threaded-animation', '--disable-threaded-scrolling', '--disable-checker-imaging', '--hide-scrollbars'],
});
const bcdp = await ctx.browser()?.newBrowserCDPSession?.() ?? (await ctx.newCDPSession(ctx.pages()[0]));
const pagePromise = ctx.waitForEvent('page');
await bcdp.send('Target.createTarget', { url: 'about:blank', enableBeginFrameControl: true, width: 1920, height: 1080 });
const pg = await pagePromise;
const cdp = await ctx.newCDPSession(pg);
await cdp.send('Emulation.setDeviceMetricsOverride', { width: 1920, height: 1080, deviceScaleFactor: DPR, mobile: false });
await cdp.send('HeadlessExperimental.enable').catch(() => {});

let ticks = 1000;
let last = null;
let virtual = false;
/** Puts the page's clock (timers, Date, performance.now, rAF) under our control; it advances only per frame. */
async function freezeClock() {
  if (virtual) return;
  await cdp.send('Emulation.setVirtualTimePolicy', { policy: 'pause' });
  virtual = true;
}
async function thawClock() {
  if (!virtual) return;
  await cdp.send('Emulation.setVirtualTimePolicy', { policy: 'advance' });
  virtual = false;
}
/** Produces one frame 1/60 s later; returns its JPEG (the previous one if nothing changed). */
async function frame(shot = true) {
  ticks += FRAME;
  if (virtual) {
    // 'advance' (not pauseIfNetworkFetchesPending): a long-lived request must never stall the clock. Pages are loaded
    // and quiet before the clock is frozen, so nothing the film needs is still in flight.
    const done = new Promise((r) => cdp.once('Emulation.virtualTimeBudgetExpired', r));
    await cdp.send('Emulation.setVirtualTimePolicy', { policy: 'advance', budget: FRAME, maxVirtualTimeTaskStarvationCount: 200 });
    await Promise.race([done, new Promise((r) => setTimeout(r, 400))]);
  }
  const r = await cdp.send('HeadlessExperimental.beginFrame', { frameTimeTicks: ticks, interval: FRAME, screenshot: shot ? { format: 'jpeg', quality: 90 } : undefined });
  if (r.screenshotData) last = Buffer.from(r.screenshotData, 'base64');
  return last;
}
/** Runs frames without recording until `ms` of page time pass (loading, settling). */
async function idle(ms) {
  for (let i = 0; i < ms / FRAME; i++) await frame(i % 6 === 0);
}

// Mouse input under frame control: an event is only processed when a frame is drawn, so it is sent without waiting,
// the frame is drawn, and then the acknowledgement is collected (awaiting first would deadlock the renderer).
const pending = [];
const mouse = (p) => pending.push(cdp.send('Input.dispatchMouseEvent', p).catch(() => {}));
const flush = async () => {
  await Promise.all(pending.splice(0));
};

// ------------------------------------------------------------------------------------------------- the hand
const noise = (s) => {
  const v = Math.sin(s * 12.9898) * 43758.5453;
  return v - Math.floor(v);
};
const minJerk = (u) => u * u * u * (10 - 15 * u + 6 * u * u);
/** A person's move from a to b: curved path, fast middle, small overshoot then settle, faint tremor. */
function path(a, b, frames, seed) {
  const dx = b.x - a.x;
  const dy = b.y - a.y;
  const d = Math.hypot(dx, dy) || 1;
  const bend = (noise(seed) - 0.5) * 0.28 * d; // sideways bow
  const over = Math.min(14, d * 0.035);
  const pts = [];
  for (let i = 1; i <= frames; i++) {
    const u = i / frames;
    const e = minJerk(Math.min(1, u * 1.08)); // reach slightly early ...
    const back = u > 0.92 ? Math.sin(((u - 0.92) / 0.08) * Math.PI) * over * 0.5 : 0; // ... overshoot, settle
    const arc = Math.sin(Math.PI * e) * bend;
    const tremor = 0.6 * Math.sin(i * 0.9 + seed) + 0.4 * Math.sin(i * 2.3 + seed * 3);
    pts.push({ x: a.x + dx * e - (dy / d) * arc + (dx / d) * back + tremor * 0.5, y: a.y + dy * e + (dx / d) * arc + (dy / d) * back + tremor * 0.5 });
  }
  pts[pts.length - 1] = { ...b };
  return pts;
}

const CURSOR_JS = `window.__hand = (x, y, down, kind) => {
  let c = document.getElementById('__hand');
  if (!c) { c = document.createElement('div'); c.id = '__hand'; Object.assign(c.style, { position: 'fixed', zIndex: 2147483647, pointerEvents: 'none', left: 0, top: 0, width: '32px', height: '32px', filter: 'drop-shadow(0 2px 3px rgba(0,0,0,.30))' }); document.documentElement.appendChild(c); }
  const arrow = '<svg width="32" height="32" viewBox="0 0 32 32"><path d="M6 3 L6 24.5 L11 19.8 L14.6 28 L18.4 26.4 L14.9 18.4 L22 18.4 Z" fill="#111" stroke="#fff" stroke-width="1.6" stroke-linejoin="round"/></svg>';
  const hand = '<svg width="32" height="32" viewBox="0 0 32 32"><path d="M12 15 V6.5 a2 2 0 0 1 4 0 V14 m0 -1.5 a2 2 0 0 1 4 0 V15 m0 -1 a2 2 0 0 1 4 0 V16 m0 0 a2 2 0 0 1 3.6 1.2 V21 c0 4.4 -3.2 8 -8 8 h-2.4 c-2.6 0 -4.2 -1.1 -5.6 -3 L7.3 21.4 a2 2 0 0 1 3.3 -2.3 L12 21 Z" fill="#fff" stroke="#111" stroke-width="1.6" stroke-linejoin="round"/></svg>';
  const want = kind === 'hand' ? 'hand' : 'arrow';
  if (c.dataset.kind !== want) { c.innerHTML = want === 'hand' ? hand : arrow; c.dataset.kind = want; }
  const ox = want === 'hand' ? -13 : -6, oy = want === 'hand' ? -5 : -3;
  c.style.transform = 'translate(' + (x + ox) + 'px,' + (y + oy) + 'px) scale(' + (down ? 0.86 : 1) + ')';
};
window.__kind = (x, y) => { const e = document.elementFromPoint(x, y); if (!e) return 'arrow'; const k = getComputedStyle(e).cursor; return k === 'pointer' ? 'hand' : 'arrow'; };`;

const H = {
  pg,
  mouse,
  base: BASE,
  idleFor: (ms) => idle(ms),
  freeze: () => freezeClock(),
  frameOnly: () => frame(false),
  cursorJs: CURSOR_JS,
  pos: { x: 1700, y: 1150 },
  out: null,
  n: 0,
  marks: [],
  async goto(path, settleMs = 2500) {
    // Load in real time (frames pumped so the page can render), let the network go quiet, then freeze the clock.
    await thawClock();
    const nav = pg.goto(BASE + path, { waitUntil: 'networkidle' });
    let done = false;
    nav.then(() => (done = true), () => (done = true));
    while (!done) {
      await frame(false);
      await new Promise((r) => setTimeout(r, 16));
    }
    await nav;
    for (let i = 0; i < 90; i++) {
      await frame(false);
      await new Promise((r) => setTimeout(r, 16));
    }
    await pg.evaluate(CURSOR_JS);
    await freezeClock();
    await idle(settleMs);
  },
  async rec(n = 1) {
    for (let i = 0; i < n; i++) {
      await pg.evaluate(([x, y, d]) => window.__hand && window.__hand(x, y, d, window.__kind(x, y)), [H.pos.x, H.pos.y, H.down ?? false]).catch(() => {});
      const jpg = await frame(true);
      await flush();
      writeFileSync(join(H.out, `${String(H.n++).padStart(5, '0')}.jpg`), jpg);
    }
  },
  /** Waits (records) for ms; the hand breathes a pixel so it never freezes. */
  async hold(ms) {
    const n = Math.round(ms / FRAME);
    const base = { ...H.pos };
    for (let i = 0; i < n; i++) {
      H.pos = { x: base.x + 0.5 * Math.sin(H.n * 0.07), y: base.y + 0.5 * Math.cos(H.n * 0.05) };
      await H.rec();
    }
    H.pos = base;
  },
  async to(target, ms) {
    const b = typeof target.x === 'number' ? target : await H.box(target);
    const d = Math.hypot(b.x - H.pos.x, b.y - H.pos.y);
    const frames = Math.max(14, Math.round((ms ?? 380 + d * 0.55) / FRAME));
    for (const p of path(H.pos, b, frames, H.n * 0.37 + 1)) {
      H.pos = p;
      mouse({ type: 'mouseMoved', x: p.x, y: p.y, button: H.down ? 'left' : 'none', buttons: H.down ? 1 : 0 });
      await H.rec();
    }
    return b;
  },
  async box(loc, fx = 0.5, fy = 0.5) {
    const r = await loc.boundingBox();
    if (!r) throw new Error('not visible: ' + loc);
    return { x: r.x + r.width * (fx + (noise(r.x) - 0.5) * 0.08), y: r.y + r.height * (fy + (noise(r.y) - 0.5) * 0.12) };
  },
  async click(target, ms) {
    await H.to(target, ms);
    await H.hold(160 + noise(H.n) * 120);
    H.marks.push({ f: H.n, click: String(target).slice(0, 60) });
    H.down = true;
    mouse({ type: 'mousePressed', x: H.pos.x, y: H.pos.y, button: 'left', buttons: 1, clickCount: 1 });
    await H.rec(4);
    mouse({ type: 'mouseReleased', x: H.pos.x, y: H.pos.y, button: 'left', buttons: 0, clickCount: 1 });
    H.down = false;
    await H.rec(2);
  },
  /** A wheel scroll by dy px, as two or three flicks with momentum, like a trackpad or mouse wheel. */
  async scroll(dy, ms = 1300) {
    const n = Math.round(ms / FRAME);
    let done = 0;
    for (let i = 1; i <= n; i++) {
      const u = i / n;
      const want = dy * (1 - Math.pow(1 - u, 3));
      const step = want - done;
      done = want;
      mouse({ type: 'mouseWheel', x: H.pos.x, y: H.pos.y, deltaX: 0, deltaY: step });
      await H.rec();
    }
  },
  mark(what) {
    H.marks.push({ f: H.n, mark: what });
  },
};

const report = {};
try {
  for (const name of process.argv.slice(2)) {
    if (!TAKES[name]) throw new Error(`no take "${name}"`);
    H.out = join(ROOT, name);
    rmSync(H.out, { recursive: true, force: true });
    mkdirSync(H.out, { recursive: true });
    H.n = 0;
    H.marks = [];
    await TAKES[name](H, { idle, frame });
    report[name] = { frames: H.n, seconds: +(H.n / 60).toFixed(2), marks: H.marks };
    console.log(name, JSON.stringify(report[name]));
  }
} catch (e) {
  console.error('FAILED', String(e).slice(0, 800));
  process.exitCode = 1;
} finally {
  writeFileSync(join(ROOT, `_report-${Date.now()}.json`), JSON.stringify(report, null, 1));
  await ctx.close();
}
