import { readFileSync } from "node:fs";
import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";

const species: { slug: string; name: string; vernacular: string; gate: string; tier: string }[] = JSON.parse(
  readFileSync("public/data/species.json", "utf-8"),
);
const cells: { features: { properties: { h3: string; species: string[] } }[] } = JSON.parse(
  readFileSync("public/data/geo/cells.geojson", "utf-8"),
);
const top = species.find((s) => s.tier === "High attention")!;
const area = cells.features.find((f) => f.properties.species.some((s) => species.find((x) => x.slug === s && !x.gate)))!.properties;

test.beforeEach(async ({ page }) => {
  await page.addInitScript(() => sessionStorage.setItem("hra-intro-seen", "1"));
});

async function settled(page: Page) {
  await expect(page.locator("h1").first()).toBeVisible();
  await page.waitForLoadState("networkidle");
}

test("Atlas: pick a plant from the list and the URL round-trips", async ({ page }) => {
  await page.goto("/atlas");
  await settled(page);
  await page.locator(".plant-list a, .plant-list button").filter({ hasText: top.vernacular || top.name }).first().click();
  await expect(page).toHaveURL(new RegExp(`sp=${top.slug}`));
  await expect(page.locator(".panel--plant h1")).toContainText(top.vernacular ? new RegExp(top.vernacular, "i") : top.name);
  await page.goBack();
  await expect(page).not.toHaveURL(/sp=/);
  await expect(page.getByRole("heading", { name: "Explore the atlas" })).toBeVisible();
  await page.goForward();
  await expect(page).toHaveURL(new RegExp(`sp=${top.slug}`));
  await page.reload();
  await expect(page.locator(".panel--plant h1")).toBeVisible();
});

test("Atlas: pick a plant from a map area", async ({ page }) => {
  await page.goto(`/atlas?cell=${area.h3}`);
  await settled(page);
  await expect(page.getByRole("heading", { name: "This area" })).toBeVisible();
  const first = page.locator(".panel .plant-list a, .panel .plant-list button").first();
  await expect(first).toBeVisible();
  await first.click();
  await expect(page).toHaveURL(/sp=/);
  await expect(page.locator(".panel--plant h1")).toBeVisible();
});

test("Atlas: clicking an area on the map opens its panel", async ({ page }) => {
  await page.goto("/atlas");
  await settled(page);
  const canvas = page.locator(".atlas__map canvas").first();
  await expect(canvas).toBeVisible();
  await page.waitForTimeout(1500);
  const box = (await canvas.boundingBox())!;
  let hit = false;
  for (let fy = 0.15; fy < 0.95 && !hit; fy += 0.07) {
    for (let fx = 0.2; fx < 0.8 && !hit; fx += 0.05) {
      await page.mouse.click(box.x + box.width * fx, box.y + box.height * fy);
      await page.waitForTimeout(150); // spaced out so two clicks never count as a double-click zoom
      hit = /[?&]cell=/.test(page.url());
    }
  }
  expect(hit, "a click on the map should select an area").toBe(true);
  await expect(page.getByRole("heading", { name: "This area" })).toBeVisible();
});

test("How it works: weights live in the URL", async ({ page }) => {
  await page.goto("/how-it-works?w=3,1,1,0");
  await expect(page.getByRole("button", { name: "Rarity first" })).toHaveAttribute("aria-pressed", "true");
  await page.getByRole("button", { name: "Harvest first" }).click();
  await expect(page).toHaveURL(/w=1(%2C|,)3(%2C|,)1(%2C|,)0/);
  await page.getByRole("button", { name: "Equal (published)" }).click();
  await expect(page).not.toHaveURL(/w=/);
  await page.goto("/how-it-works?w=garbage");
  await expect(page.getByRole("button", { name: "Equal (published)" })).toHaveAttribute("aria-pressed", "true");
});

test("a bad slug shows NotFound", async ({ page }) => {
  await page.goto("/species/not-a-plant");
  await expect(page.getByRole("heading", { name: /is not in the atlas/ })).toBeVisible();
  await page.goto("/species/not-a-plant/brief");
  await expect(page.getByRole("heading", { name: /is not in the atlas/ })).toBeVisible();
  await page.goto("/nowhere");
  await expect(page.getByRole("heading", { name: /is not in the atlas/ })).toBeVisible();
});

test("redirects keep old links working", async ({ page }) => {
  await page.goto("/rankings");
  await expect(page).toHaveURL(/\/plants$/);
  await page.goto("/methods");
  await expect(page).toHaveURL(/\/how-it-works$/);
});

test("field brief fits one A4 page", async ({ page }) => {
  for (const s of [top, species.find((x) => x.gate === "not_native")!]) {
    await page.goto(`/species/${s.slug}/brief`);
    await expect(page.locator("article.brief")).toBeVisible();
    await page.emulateMedia({ media: "print" });
    const pdf = await page.pdf({ preferCSSPageSize: true, printBackground: true });
    const pages = pdf.toString("latin1").match(/\/Type\s*\/Page[^s]/g)?.length ?? 0;
    expect(pages, `${s.slug} prints on ${pages} pages`).toBe(1);
    await page.emulateMedia({ media: "screen" });
  }
});

const routes = ["/", "/atlas", `/atlas?sp=${top.slug}`, `/atlas?cell=${area.h3}`, "/plants", `/species/${top.slug}`, `/species/${top.slug}/brief`, "/how-it-works", "/nowhere"];
for (const route of routes) {
  test(`axe: no serious or critical issues on ${route}`, async ({ page }) => {
    await page.goto(route);
    await settled(page);
    const { violations } = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"]).analyze();
    const bad = violations.filter((v) => v.impact === "serious" || v.impact === "critical");
    expect(bad.map((v) => `${v.id}: ${v.nodes.map((n) => n.target.join(" ")).slice(0, 3).join(" | ")}`)).toEqual([]);
  });
}

const widths = [360, 390, 768, 1024, 1280, 1440];
for (const w of widths) {
  test(`no horizontal scroll at ${w}px on any route`, async ({ page }) => {
    await page.setViewportSize({ width: w, height: 844 });
    for (const route of routes) {
      await page.goto(route);
      await settled(page);
      const over = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
      expect(over, `${route} overflows by ${over}px at ${w}px`).toBeLessThanOrEqual(0);
    }
  });
}

test("reduced motion skips the intro", async ({ page }) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.addInitScript(() => sessionStorage.removeItem("hra-intro-seen"));
  await page.goto("/");
  await expect(page.getByRole("heading", { level: 1 })).toContainText("Which wild medicinal plants");
  await expect(page.getByRole("button", { name: /skip/i })).toHaveCount(0);
});

test("keyboard: skip link is first, and the Atlas announces a selection", async ({ page }) => {
  await page.goto("/atlas");
  await settled(page);
  await page.keyboard.press("Tab");
  await expect(page.getByRole("link", { name: "Skip to content" })).toBeFocused();
  await page.goto(`/atlas?sp=${top.slug}`);
  await expect(page.locator('aside [role="status"]').first()).toContainText("Showing");
});
