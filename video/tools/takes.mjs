// The demo as one user's journey, take by take. Each take is timed to its stretch of narration, and each starts with
// the hand where the previous take's click left it, so a click in one take becomes the page of the next.
//   overview  hover two hotspots, click "Explore the map"
//   atlas     click Tongkat Ali in the list (the map flies to its hexagons), point at the map, click "Full profile"
//   profile   point at the rank and its range, click "Field brief"
//   brief     read, scroll the page
//   weights   drag "Harvest harm" up (the list re-ranks), click "Plants" in the menu
//   plants    scroll through the tiers
//   checks    the robustness checks, scroll to "Typical uncertainty"
//   intro     the app's own opening animation (first visit)

const seen = async (H) => {
  await H.pg.goto(H.base + '/');
  await H.pg.evaluate(() => sessionStorage.setItem('hra-intro-seen', '1'));
};
const toHeading = async (H, text, off) => {
  await H.pg.evaluate(([t, off]) => {
    const h = [...document.querySelectorAll('h2')].find((e) => e.textContent.includes(t));
    window.scrollTo(0, h.getBoundingClientRect().top + scrollY - off);
  }, [text, off]);
};

export const TAKES = {
  async intro(H, { frame }) {
    await H.pg.goto(H.base + '/');
    await H.pg.evaluate(() => sessionStorage.removeItem('hra-intro-seen'));
    H.pos = { x: 2400, y: 1400 }; // off screen: no hand during the opening
    // Freeze the clock before the page starts, so the opening animation plays frame by frame from its first frame.
    await H.freeze();
    const nav = H.pg.goto(H.base + '/', { waitUntil: 'commit' });
    for (let i = 0; i < 40; i++) await H.frameOnly();
    await nav;
    await H.pg.evaluate(H.cursorJs);
    await H.rec(Math.round(7.4 * 60));
  },

  async overview(H) {
    await seen(H);
    await H.goto('/');
    H.pos = { x: 1980, y: 900 };
    const m = await H.pg.locator('canvas').first().boundingBox();
    const at = (fx, fy) => ({ x: m.x + m.width * fx, y: m.y + m.height * fy });
    await H.hold(300);
    await H.to(at(0.47, 0.31), 900);
    H.mark('hover 1');
    await H.hold(1100);
    await H.to(at(0.52, 0.43), 750);
    H.mark('hover 2');
    await H.hold(900);
    await H.click(H.pg.getByRole('link', { name: /Explore the map/i }).first(), 950);
  },

  async atlas(H) {
    await H.goto('/atlas');
    await H.hold(200);
    await H.click(H.pg.getByRole('button', { name: /Tongkat Ali/i }).first(), 1000);
    await H.hold(1500); // the map flies to tongkat ali's hexagons
    // One of tongkat ali's own hexagons after the fly-to (located on the recorded frame), so the tooltip names it.
    await H.to({ x: 679, y: 430 }, 1000);
    H.mark('over the map');
    await H.hold(2600);
    await H.click(H.pg.getByRole('link', { name: /Full profile/i }).first(), 1000);
  },

  async profile(H) {
    await H.goto('/species/eurycoma-longifolia');
    await H.hold(300);
    await H.to(await H.box(H.pg.getByText(/Ranked 2nd of 29/).first(), 0.15, 1.6), 1100);
    H.mark('at the rank');
    await H.hold(2700);
    await H.click(H.pg.getByRole('link', { name: /Field brief/i }).first(), 950);
  },

  async brief(H) {
    await H.goto('/species/eurycoma-longifolia/brief');
    await H.to({ x: H.pos.x - 220, y: H.pos.y + 160 }, 900);
    await H.hold(700);
    await H.scroll(520, 1600);
    await H.hold(1800);
  },

  async weights(H) {
    await H.goto('/how-it-works', 1500);
    await toHeading(H, 'What if you weighed', 96);
    await H.idleFor(800);
    await H.hold(200);
    const thumb = H.pg.getByRole('slider').nth(1);
    const b = await thumb.boundingBox();
    const t = { x: b.x + b.width / 2, y: b.y + b.height / 2 };
    await H.to(t, 1100);
    await H.hold(180);
    H.down = true;
    H.mouse({ type: 'mousePressed', x: t.x, y: t.y, button: 'left', buttons: 1, clickCount: 1 });
    H.mark('drag');
    // A hand drag: fast start, slowing as it nears where it wants to be, a little wobble in y.
    const n = Math.round(2.6 * 60);
    for (let i = 1; i <= n; i++) {
      const u = i / n;
      const e = 1 - Math.pow(1 - u, 2.4);
      H.pos = { x: t.x + 200 * e, y: t.y + 1.2 * Math.sin(i * 0.21) };
      H.mouse({ type: 'mouseMoved', x: H.pos.x, y: H.pos.y, button: 'left', buttons: 1 });
      await H.rec();
    }
    H.mouse({ type: 'mouseReleased', x: H.pos.x, y: H.pos.y, button: 'left', buttons: 0, clickCount: 1 });
    H.down = false;
    H.mark('release');
    await H.hold(1000);
    await H.click(H.pg.getByRole('navigation', { name: 'Main' }).first().getByRole('link', { name: 'Plants' }), 900);
  },

  async plants(H) {
    await H.goto('/plants');
    await H.to({ x: 960, y: 640 }, 900);
    await H.hold(300);
    await H.scroll(640, 1800);
    await H.hold(2000);
  },

  // The expert cross-check on tongkat ali's page: WFO name, Co's Digital Flora, then where to look next.
  async check(H) {
    await H.goto('/species/eurycoma-longifolia', 1500);
    await toHeading(H, 'Checked against expert sources', 70);
    await H.idleFor(800);
    H.pos = { x: 1400, y: 900 };
    await H.hold(300);
    await H.to(await H.box(H.pg.getByText(/accepted name in World Flora Online/).first(), 0.3, 0.5), 1000);
    await H.hold(1600);
    await H.to(await H.box(H.pg.getByText(/Native in Co's Digital Flora/).first(), 0.3, 0.5), 900);
    H.mark('cdfp');
    await H.hold(2600);
    await H.to(await H.box(H.pg.getByText(/Documented by Co's Digital Flora/).first(), 0.8, 0.5), 1000);
    H.mark('look next');
    await H.hold(3200);
    await H.to(await H.box(H.pg.getByText(/areas right next to its records/).first(), 0.5, 0.5), 900);
    await H.hold(2600);
  },

  async checks(H) {
    await H.goto('/how-it-works', 1500);
    await toHeading(H, 'How sure is the ranking', 80);
    await H.idleFor(800);
    H.pos = { x: 1500, y: 700 };
    await H.to({ x: 1320, y: 520 }, 1000);
    await H.hold(3800);
    await H.scroll(380, 1600);
    await H.hold(2600);
  },
};
