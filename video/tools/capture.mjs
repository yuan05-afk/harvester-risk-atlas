// Records real footage of https://harvester-risk-atlas.vercel.app at 2x pixel density (3840x2160) for the pitch film.
//
//   node tools/capture.mjs <clip> [<clip> ...]      (clips: intro overview atlas profile brief weights plants checks)
//
// Headless Chrome screencasts each frame to capture/<clip>/<n>_<ms>.jpg; tools/concat-lists.mjs + tools/encode.sh turn
// them into constant-rate clips. A drawn cursor (headless frames have none) glides to each target and rings on clicks.
// Read-only: the site has no accounts or writes; the only "clicks" are navigation, a plant row and a slider.
import { chromium } from 'playwright-core';
import { mkdirSync, rmSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';

const BASE = process.env.BASE_URL ?? 'https://harvester-risk-atlas.vercel.app';
const ROOT = new URL('../capture/', import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, '$1');
const wanted = process.argv.slice(2);

const CURSOR = `(() => { if (window.top !== window) return;
  const mk = () => { if (document.getElementById('__cur') || !document.body) return; const d = document.createElement('div'); d.id = '__cur';
    d.innerHTML = '<svg width="28" height="28" viewBox="0 0 26 26"><path d="M4 2 L4 20 L8.6 15.8 L11.8 23 L15 21.6 L11.8 14.6 L18 14.6 Z" fill="#15181c" stroke="#fff" stroke-width="1.5" stroke-linejoin="round"/></svg>';
    Object.assign(d.style, { position: 'fixed', left: '0', top: '0', zIndex: '2147483647', pointerEvents: 'none', transform: 'translate(' + (window.__curX ?? 1500) + 'px,' + (window.__curY ?? 1180) + 'px)', filter: 'drop-shadow(0 2px 3px rgba(0,0,0,.28))' });
    document.body.appendChild(d); };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', mk); else mk();
  const watch = () => document.documentElement && new MutationObserver(mk).observe(document.documentElement, { childList: true, subtree: true });
  if (document.documentElement) watch(); else document.addEventListener('readystatechange', watch, { once: true });
  window.__curTo = (x, y, ms) => { mk(); const d = document.getElementById('__cur'); d.style.transition = 'transform ' + ms + 'ms cubic-bezier(.3,.7,.2,1)'; d.style.transform = 'translate(' + (x - 4) + 'px,' + (y - 2) + 'px)'; };
  window.__curRing = (x, y) => { const r = document.createElement('div'); Object.assign(r.style, { position: 'fixed', left: (x - 18) + 'px', top: (y - 18) + 'px', width: '36px', height: '36px', borderRadius: '18px', border: '2.5px solid #7c1a4b', zIndex: '2147483646', pointerEvents: 'none' }); document.body.appendChild(r);
    r.animate([{ transform: 'scale(.4)', opacity: 0.9 }, { transform: 'scale(1.3)', opacity: 0 }], { duration: 520, easing: 'cubic-bezier(.2,.7,.3,1)' }).onfinish = () => r.remove(); };
  window.__scroll = (to, ms) => new Promise((res) => { const y0 = scrollY, t0 = performance.now(); const e = (x) => x < .5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2;
    const step = (now) => { const p = Math.min(1, (now - t0) / ms); scrollTo(0, y0 + (to - y0) * e(p)); p < 1 ? requestAnimationFrame(step) : res(); }; requestAnimationFrame(step); });
})();`;

const browser = await chromium.launch({ channel: 'chrome', headless: true, args: ['--force-device-scale-factor=2'] });
const ctx = await browser.newContext({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 2, timezoneId: 'Asia/Manila', locale: 'en-PH' });
await ctx.addInitScript(CURSOR);
const pg = await ctx.newPage();
const cdp = await ctx.newCDPSession(pg);
const w = (ms) => pg.waitForTimeout(ms);
const R = { clip: '', i: 0, t0: null, wall: 0, marks: [] };
cdp.on('Page.screencastFrame', (fr) => {
  cdp.send('Page.screencastFrameAck', { sessionId: fr.sessionId }).catch(() => {});
  if (!R.clip) return;
  const ts = fr.metadata.timestamp * 1000;
  if (R.t0 === null) R.t0 = ts;
  writeFileSync(join(ROOT, R.clip, `${String(R.i++).padStart(5, '0')}_${Math.round(ts - R.t0)}.jpg`), Buffer.from(fr.data, 'base64'));
});

const H = {
  async goto(path, settle = 3500, skipIntro = true) {
    await pg.goto(BASE + '/');
    await pg.evaluate((s) => (s ? sessionStorage.setItem('hra-intro-seen', '1') : sessionStorage.removeItem('hra-intro-seen')), skipIntro);
    await pg.goto(BASE + path, { waitUntil: 'networkidle' });
    await w(settle);
  },
  async move(loc, ms = 800, dx = 0.5) {
    const b = await loc.boundingBox();
    if (!b) throw new Error('target not visible: ' + loc);
    const x = b.x + b.width * dx;
    const y = b.y + b.height / 2;
    await pg.evaluate(([x, y, ms]) => window.__curTo(x, y, ms), [x, y, ms]);
    await pg.mouse.move(x, y, { steps: 12 });
    await w(ms + 150);
    return { x, y };
  },
  async point(x, y, ms = 800) {
    await pg.evaluate(([x, y, ms]) => window.__curTo(x, y, ms), [x, y, ms]);
    await pg.mouse.move(x, y, { steps: 14 });
    await w(ms + 150);
  },
  async click(loc, ms = 800) {
    const { x, y } = await H.move(loc, ms);
    await pg.evaluate(([x, y]) => window.__curRing(x, y), [x, y]);
    H.mark('click ' + String(loc).slice(0, 60));
    await pg.mouse.click(x, y);
    await w(300);
  },
  async scrollTo(loc, off = 110, ms = 1400) {
    const y = await loc.evaluate((e, off) => e.getBoundingClientRect().top + scrollY - off, off);
    await pg.evaluate(([y, ms]) => window.__scroll(y, ms), [y, ms]);
    await w(250);
  },
  async scrollBy(dy, ms = 1400) {
    await pg.evaluate(([dy, ms]) => window.__scroll(scrollY + dy, ms), [dy, ms]);
    await w(250);
  },
  async start(name) {
    rmSync(join(ROOT, name), { recursive: true, force: true });
    mkdirSync(join(ROOT, name), { recursive: true });
    Object.assign(R, { clip: name, i: 0, t0: null, marks: [], wall: Date.now() });
    await cdp.send('Page.startScreencast', { format: 'jpeg', quality: 92, everyNthFrame: 1 });
    await w(400);
  },
  async stop() {
    await w(300);
    const n = R.i;
    // Static holds send no frames; record the wall end so the last frame is held until the true end of the take.
    writeFileSync(join(ROOT, R.clip, '_end.txt'), String(Date.now() - R.wall));
    R.clip = '';
    await cdp.send('Page.stopScreencast').catch(() => {});
    return n;
  },
  mark(what) {
    if (R.clip) R.marks.push({ t: Date.now() - R.wall, mark: what });
  },
};

const heading = (text) => pg.locator('h2', { hasText: text }).first();

const CLIPS = {
  // The app's own opening: the outline draws, hexes bloom north to south, the sheet clips away.
  async intro() {
    await pg.goto(BASE + '/');
    await pg.evaluate(() => sessionStorage.removeItem('hra-intro-seen'));
    await H.start('intro');
    await pg.goto(BASE + '/');
    await w(6500);
    return { frames: await H.stop() };
  },
  // Overview: point at three hotspots so the map's own tooltip answers.
  async overview() {
    await H.goto('/');
    await H.start('overview');
    await w(800);
    const m = await pg.locator('canvas').first().boundingBox();
    for (const [fx, fy] of [[0.47, 0.30], [0.50, 0.42], [0.62, 0.62], [0.72, 0.80]]) {
      const [x, y] = [m.x + m.width * fx, m.y + m.height * fy];
      await H.point(x, y, 900);
      H.mark(`hover ${x},${y}`);
      await w(1400);
    }
    return { frames: await H.stop(), marks: R.marks };
  },
  // Atlas: pick tongkat ali from the list; the map shows only its hexagons.
  async atlas() {
    await H.goto('/atlas');
    await H.start('atlas');
    await w(1200);
    const row = pg.getByRole('button', { name: /Tongkat Ali/i }).first();
    await row.scrollIntoViewIfNeeded();
    await H.click(row, 1000);
    await w(4500);
    await H.point(1000, 600, 1400);
    await w(3000);
    await H.point(760, 420, 1400);
    await w(2600);
    return { frames: await H.stop(), marks: R.marks };
  },
  // Profile: the rank and its range, then why it ranks here, then where it grows.
  async profile() {
    await H.goto('/species/eurycoma-longifolia');
    await H.start('profile');
    await w(9500);
    await H.scrollTo(heading('Why it ranks here'), 120, 1800);
    await w(3600);
    return { frames: await H.stop(), marks: R.marks };
  },
  // From the profile, one click to the printable brief.
  async brief() {
    await H.goto('/species/eurycoma-longifolia');
    await H.start('brief');
    await w(900);
    await H.click(pg.getByRole('link', { name: /Field brief/i }).first(), 1000);
    await w(3500);
    await H.scrollBy(520, 2200);
    await w(4000);
    return { frames: await H.stop(), marks: R.marks };
  },
  // Weight explorer: drag "Harvest harm" up and watch the top 8 re-rank.
  async weights() {
    await H.goto('/how-it-works');
    await H.scrollTo(heading('What if you weighed'), 100, 10);
    await w(1500);
    await H.start('weights');
    await w(1000);
    const thumb = pg.getByRole('slider').nth(1);
    const b = await thumb.boundingBox();
    const x0 = b.x + b.width / 2;
    const y0 = b.y + b.height / 2;
    await H.point(x0, y0, 900);
    await pg.mouse.down();
    H.mark('drag start');
    for (let k = 1; k <= 40; k++) {
      const x = x0 + (k / 40) * 190;
      await pg.evaluate(([x, y]) => window.__curTo(x, y, 40), [x, y0]);
      await pg.mouse.move(x, y0);
      await w(45);
    }
    await pg.mouse.up();
    H.mark('drag end');
    await w(3800);
    return { frames: await H.stop(), marks: R.marks };
  },
  // All plants by tier, and the CSV download.
  async plants() {
    await H.goto('/plants');
    await H.start('plants');
    await w(2200);
    await H.scrollBy(620, 2400);
    await w(1500);
    await H.point(960, 640, 1000);
    await w(2000);
    return { frames: await H.stop(), marks: R.marks };
  },
  // How sure is the ranking: the four checks.
  async checks() {
    await H.goto('/how-it-works');
    await H.scrollTo(heading('How sure is the ranking'), 90, 10);
    await w(1500);
    await H.start('checks');
    await w(5500);
    await H.scrollBy(380, 2600);
    await w(6000);
    return { frames: await H.stop(), marks: R.marks };
  },
};

const report = {};
try {
  for (const name of wanted) {
    if (!CLIPS[name]) throw new Error(`no clip "${name}"`);
    report[name] = await CLIPS[name]();
    console.log(name, JSON.stringify(report[name]));
  }
} catch (e) {
  console.error('FAILED', String(e).slice(0, 600));
  await pg.screenshot({ path: join(ROOT, '_failure.png') }).catch(() => {});
  process.exitCode = 1;
} finally {
  R.clip = '';
  writeFileSync(join(ROOT, '_report.json'), JSON.stringify(report, null, 1));
  await browser.close();
}
