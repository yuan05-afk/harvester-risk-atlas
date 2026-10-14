// Pre-renders the Overview into dist/index.html after `vite build`, so the first
// paint shows the page instead of an empty shell. The untouched shell is kept as
// dist/shell.html; vercel.json serves it for every other path.
import { readFileSync, rmSync, writeFileSync } from "node:fs";
import { fileURLToPath, pathToFileURL } from "node:url";
import { build } from "vite";

const dist = new URL("../dist/", import.meta.url);
const ssrOut = new URL("../dist-ssr/", import.meta.url);

await build({
  logLevel: "warn",
  build: { ssr: "src/entry-server.tsx", outDir: "dist-ssr", emptyOutDir: true, copyPublicDir: false },
});
const { render } = await import(pathToFileURL(fileURLToPath(new URL("entry-server.js", ssrOut))).href);

const read = (p) => JSON.parse(readFileSync(new URL(`data/${p}`, dist), "utf-8"));
const html = render("/", { "species.json": read("species.json"), "manifest.json": read("manifest.json") });
if (!html.includes("hero")) throw new Error("prerender: the Overview did not render");

const shell = readFileSync(new URL("index.html", dist), "utf-8");
const marker = '<div id="root"></div>';
if (!shell.includes(marker)) throw new Error("prerender: no empty #root in index.html");
writeFileSync(new URL("shell.html", dist), shell);
writeFileSync(new URL("index.html", dist), shell.replace(marker, `<div id="root" data-prerendered>${html}</div>`));
rmSync(ssrOut, { recursive: true, force: true });
console.log(`prerender: index.html now carries the Overview (${(html.length / 1024).toFixed(0)} KB of markup)`);
