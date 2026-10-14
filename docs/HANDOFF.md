# HANDOFF: read this first (new Claude chat)

You are continuing **Harvester Risk Atlas v2** for EthnoHack 2026, Track 3 (hackathon Nov 2–8 2026; submission Nov 8). This file replaces the old chat. It is enough to continue: read the plan only if a step here is unclear (`C:\Users\Yuan\.claude\plans\harvester-risk-atlas-virtual-eagle.md`).

**Updated:** 2026-10-14, after Phase 4 (tests and parity, complete). Branch `v2-rebuild`. Run `git log --oneline -5` for the latest commit.

## 1. Rules (non-negotiable)
- **Approvals.** Commit at the end of each phase, which the user has approved. **Never push, deploy, make the repo public, or tag a release without asking.**
- **Verification.** Verify UI in a real browser at **1440×900 and 390×844** before claiming it works. Run `pytest` and `npm run build` before committing. Report pass, fail and not checked.
- **Data integrity.** Never invent IUCN or DENR categories or coordinates. Missing data stays missing. Plants are only ever shown as H3 cells, never as points.
- **Design quality is a first-class requirement.** The user rejects generic "AI-looking" UI. Obey the **Banned patterns** in `docs/DESIGN.md`: no coloured left-stripe boxes, no icon-in-pastel-square cards, no status pills, no stock icons for meaning, no rounded-pill everything, no Tableau blue/orange/green.
- **Audience.** Write for non-experts: plain words first, numbers second (behind disclosures).
- **Scope.** Don't widen it silently. Ask only when an answer changes product behaviour, architecture, data handling or scope.
- **Log the work.** After each change, add a line to `docs/ORIGINALITY.md` (v2 log until tag `v2.0-pre-hackathon`, then the hack-week log).

## 2. What exists
**Science (Phases 1–2, done).** The Python package `src/harvester_risk_atlas/` runs the pipeline `fetch → base → index → validate → export`.
- **Index:** HPI v2 "Harvest Priority Index", with components R (rarity), H (harvest harm) and E (habitat pressure) at equal weight, and C (climate) at weight 0.
- **Uncertainty:** 2,000 Monte Carlo draws assign tiers by P(top quartile): ≥ 0.8 High attention, ≥ 0.3 Watch.
- **Cohort:** 51 taxa; 29 scored, 22 gated (not native, or fewer than 5 cells).
- **Validation:** results are in `web/public/data/validation.json`.
- **Docs:** the full method is in `docs/METHODS.md`.

**Web (Phase 3, done; Phase 4 mostly done).** `web/` is Vite 8, React 19, TypeScript, MapLibre 6, motion, zod and Radix. Routes (lazy except Overview):

| Route | What it shows |
|---|---|
| `/` | Intro preloader on first visit, hero hotspot map with hover tooltip and click-through to Atlas, top-5 cards, "How we decide" figure plates, the 4-step trail, footnote caveats |
| `/atlas?sp=&cell=` | Full-bleed map; panels: Browse (grouped by tier), Plant, Area |
| `/plants` | Tier sections of plant cards, plus a CSV download |
| `/species/:slug` | Photo and stamp, reason tiles, disclosures, where-map, history, climate, sources |
| `/species/:slug/brief` | One A4 page; all 51 verified to fit |
| `/how-it-works` | 5 steps, weight explorer, robustness ledger, sources, what was built when |

`/rankings` and `/methods` redirect to `/plants` and `/how-it-works`.

**Key files**
- `web/src/lib/vocab.ts`: plain labels for tiers and components.
- `web/src/lib/explain.ts`: plain sentences.
- `web/src/lib/score.ts`: a TypeScript copy of the index maths.
- `web/src/components/Figures.tsx`: drawn plates, glyphs and verdict marks.
- `web/src/components/Stamp.tsx`
- `web/src/components/HexMap.tsx`: coarse res-4 cells below zoom 6.5, fine res-5 at or above, with feature-states.
- `web/src/styles/tokens.css`: the natural-dye palette.
- `web/src/styles/app.css`
- `docs/DESIGN.md`: the design system and the banned list.
- `scripts/check_palette.py`: the colour-vision check for any new colour.

## 3. Commands (Windows; Git Bash or PowerShell)
```
.venv/Scripts/python.exe -m pytest -q                          # 95 pass
.venv/Scripts/python.exe -m harvester_risk_atlas all --offline  # rebuild data → web/public/data
cd web && npm run dev            # http://localhost:5173 (also .claude/launch.json "atlas-web")
cd web && npm run build          # tsc + vite; main chunk 144.8 KB gz
cd web && npm test               # vitest: 61 pass (parity, text, tooltip)
cd web && npm run e2e            # Playwright + axe, 16 pass; builds and serves on :4173
```

**Browser QA.** Use the Playwright MCP tools (`browser_run_code_unsafe` for mouse and viewport control). Screenshots go to the repo root, in `.playwright-mcp/` (gitignored). The in-app browser pane is too small to judge 1440 px layouts.

Gotchas:
- `maplibre-gl.css` loads later than `app.css`, so override it with higher specificity.
- A full-page screenshot repeats the sticky header mid-page; that is an artifact, not a bug.
- To skip the intro, set `sessionStorage['hra-intro-seen']='1'`.

## 4. Phase status and what to do next
Work in order. Each phase ends with: verify, then update `ORIGINALITY.md` and **this file's status lines**, then commit.

### Phase 4 remainder: tests and parity (DONE, incl. weights in the URL: ?w=R,H,E,C)
1. **Golden parity test.** `export.py` writes `web/public/data/parity.json`: weights and ranks for 3 weight sets. Then a vitest `src/lib/score.test.ts` asserts that `lib/score.ts` reproduces the ranks exactly. Install `jsdom` if vitest asks for it.
   *Done when:* `npm test` is green and `pytest` is still green.
2. **Unit tests** for `vocab.level()`, `explain()` (no undefined or NaN text across all 51 species) and `MapTooltip` counts.
3. **Playwright e2e plus axe** (`web/e2e/`, `@playwright/test`, `@axe-core/playwright`):
   - pick a plant from the Atlas list and from a map area;
   - check that URLs round-trip;
   - check a bad slug shows NotFound;
   - check the brief fits one A4 page;
   - axe has 0 serious or critical issues on every route.

   Add an `npm run e2e` script.
4. **Optional, if time allows by Oct 28:** weights in the URL on How it works.

   Already cut: the Compare page and pre-built PDFs (browser print to PDF is enough).

### Phase 5: QA, docs and cutover (Oct 29 – Nov 1)
1. **CI** (`.github/workflows/ci.yml`): pytest, `npm ci`, typecheck, vitest, build, Playwright plus axe. Never fetch raw data in CI.
2. **Performance.** The Overview first load is 144.8 KB (main) + 31 KB (`api` chunk, mostly zod) = 176 KB gz, against a 150 KB target. Fix: switch `src/data/schema.ts` to `zod/mini`, or validate only on dev or error. Lighthouse targets: Performance ≥ 90, Accessibility ≥ 95, LCP < 2 s.
3. **Accessibility and responsive pass.** Keyboard-only through every route; focus order; `aria-live` on Atlas selection. Widths 360, 390, 768, 1024, 1280, 1440. Reduced motion.
4. **Old Streamlit code.** Delete `app/`, `suitability.py`, `archetypes.py` and the Streamlit tests (`test_cloud_import`, `test_intro_compat`, `test_ui_polish`, `test_landing`) and their dependencies. **Ask the user first:** the Streamlit Cloud app becomes a "moved to …" page, which the user switches over.
5. **README rewrite.** A judge quick start (live URL, 3-minute tour), Windows and POSIX reproduce steps, data licences, limitations, and the AI disclosure (Grok, Cursor, Claude Code).
6. **User actions:** make the repo public, then approve a GitHub Pages deploy. The Pages workflow builds with `VITE_BASE=/<repo>/` and needs a 404.html SPA fallback. Smoke-test the live URL.
7. **Tag `v2.0-pre-hackathon`** only with user approval. It marks the originality boundary.

### Phase 6: hack week (Nov 2–8)
- Do real new work inside the week and log it. Candidates: SDMs with spatial block cross-validation (`elapid`, species with ≥ 30 cells), province profiles, Filipino briefs (need native-speaker review), and cohort round 2.
- Devpost: Problem → Data → Method → Prototype → Results → Impact → Limitations, plus a clear pre-existing vs hack-week split.
- Slides: ≤ 10, and a video ≤ 10 min. Story: "v1 ranked a plant with zero records #1; here's how we found and fixed it" → demo deep links: Overview → Atlas area → top plant → brief → How sure.

## 5. Waiting on the user (ask; don't assume)
- **Curated data:** 18 cohort rows flagged `needs_review` in `data/curated/cohort.csv`, and 29 rows of `harvest_traits.csv`. Species pages show "Awaiting expert review" until cleared.
- **Lagundi** (*Vitex negundo*): WCVP says introduced, so it is gated. Should a `nativity_override` keep it gated?
- **Photos:** check the choices in `data/curated/photos.csv` (4 use CC BY-NC). Abutra and *Hydnocarpus* have no photo.
- **Accounts:** optional IUCN token and GBIF account (DOI downloads).
