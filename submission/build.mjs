// Builds the EthnoHack submission media: Devpost gallery screenshots of the live atlas
// and the slide deck PDF. Uses the Playwright already installed in web/.
//
//   cd web && npm ci && npx playwright install chromium
//   node ../submission/build.mjs            # screenshots + PDF
//   node ../submission/build.mjs --pdf-only # rebuild the PDF from slides/deck.html only
//
// BASE_URL defaults to the production atlas; set it to http://localhost:4173 to use a local preview.
import { createRequire } from "node:module";
import { mkdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const require = createRequire(join(here, "..", "web", "package.json"));
const { chromium } = require("@playwright/test");

const BASE = process.env.BASE_URL ?? "https://harvester-risk-atlas.vercel.app";
const pdfOnly = process.argv.includes("--pdf-only");

// 3:2 is Devpost's recommended gallery ratio.
const shots = [
  { name: "01-overview", path: "/" },
  { name: "02-atlas-tongkat-ali", path: "/atlas?sp=eurycoma-longifolia" },
  { name: "03-plant-profile", path: "/species/eurycoma-longifolia" },
  { name: "04-where-it-grows", path: "/species/eurycoma-longifolia", scrollTo: "where it grows" },
  { name: "05-field-brief", path: "/species/eurycoma-longifolia/brief" },
  { name: "06-weight-explorer", path: "/how-it-works", scrollTo: "weighed things differently" },
  { name: "07-robustness-checks", path: "/how-it-works", scrollTo: "how sure is the ranking" },
  { name: "08-plants-list", path: "/plants" },
  { name: "11-seasons", path: "/seasons?m=4" },
];

const browser = await chromium.launch();

if (!pdfOnly) {
  const out = join(here, "gallery");
  mkdirSync(out, { recursive: true });
  // Reduced motion skips the intro and the draw-in animations, so every frame is final.
  const ctx = await browser.newContext({ viewport: { width: 1500, height: 1000 }, reducedMotion: "reduce" });
  const page = await ctx.newPage();
  for (const s of shots) {
    await page.goto(BASE + s.path, { waitUntil: "networkidle" });
    await page.waitForTimeout(1500); // map tiles and photos settle
    if (s.scrollTo) {
      const scrolled = await page.evaluate((word) => {
        const heads = [...document.querySelectorAll("h2, h3")];
        const h = heads.find((el) => el.textContent?.toLowerCase().includes(word));
        if (!h) return false;
        window.scrollTo(0, h.getBoundingClientRect().top + window.scrollY - 96); // clear the sticky header
        return true;
      }, s.scrollTo);
      if (!scrolled) console.warn(`  ${s.name}: heading not found, kept the top of the page`);
      await page.waitForTimeout(800);
    }
    await page.screenshot({ path: join(out, `${s.name}.png`) });
    console.log(`gallery/${s.name}.png`);
  }
  // One phone view for the "works on a phone in the field" claim.
  const phone = await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2, reducedMotion: "reduce" });
  const p2 = await phone.newPage();
  await p2.goto(BASE + "/species/eurycoma-longifolia", { waitUntil: "networkidle" });
  await p2.waitForTimeout(1500);
  await p2.screenshot({ path: join(out, "09-phone-profile.png") });
  console.log("gallery/09-phone-profile.png");
  await ctx.close();
  await phone.close();
}

// Slides: 16:9 pages, one <section> per slide.
const deck = await browser.newPage();
await deck.goto(pathToFileURL(join(here, "slides", "deck.html")).href, { waitUntil: "networkidle" });
await deck.evaluate(() => document.fonts.ready);
await deck.pdf({
  path: join(here, "Harvester-Risk-Atlas-slides.pdf"),
  width: "1280px",
  height: "720px",
  printBackground: true,
  margin: { top: "0", right: "0", bottom: "0", left: "0" },
});
console.log("Harvester-Risk-Atlas-slides.pdf");

// README pipeline diagram: a static image, so GitHub's diagram controls never cover it.
const diagram = await browser.newPage({ viewport: { width: 1700, height: 400 }, deviceScaleFactor: 2 });
await diagram.goto(pathToFileURL(join(here, "slides", "pipeline.html")).href, { waitUntil: "networkidle" });
await diagram.evaluate(() => document.fonts.ready);
mkdirSync(join(here, "..", "docs", "images"), { recursive: true });
await diagram.locator("#diagram").screenshot({ path: join(here, "..", "docs", "images", "pipeline.png"), omitBackground: true });
console.log("docs/images/pipeline.png");

await browser.close();
