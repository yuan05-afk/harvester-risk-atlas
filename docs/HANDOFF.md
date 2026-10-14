# HANDOFF: read this first (new Claude chat)

You are continuing **Harvester Risk Atlas v2** for EthnoHack 2026, Track 3 (hackathon Nov 2–8 2026; submission Nov 8). This file replaces the old chat. It is enough to continue: read the plan only if a step here is unclear (`C:\Users\Yuan\.claude\plans\harvester-risk-atlas-virtual-eagle.md`).

**Updated:** 2026-10-14, after Phase 5. Phases 0–5 are done and on `main`, which is tagged `v2.0-pre-hackathon` at `9be0eb7` (the originality boundary). Live at https://harvester-risk-atlas.vercel.app. **Next: Phase 6 (hack week, Nov 2–8).** Run `git log --oneline -5` for the latest commit.

## 1. Rules (non-negotiable)
- **Approvals.** Commit at the end of each phase, which the user has approved. **Never push, deploy, make the repo public, or tag a release without asking.**
- **Protected `main`.** Every push to `main` redeploys production (Vercel, project `harvester-risk-atlas`, team `yuans-projects-e4a11f96`, root `web`). Work on a branch, open a PR, and merge only when the `python` and `web` CI checks pass and the user has said to merge that PR.
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

**Web (Phases 3–5, done).** `web/` is Vite 8, React 19, TypeScript, MapLibre 6, motion and Radix; zod validates data in dev and tests only. The Overview is pre-rendered at build time (`scripts/prerender.mjs`, `src/entry-server.tsx`) and hydrated; every other path is served `shell.html` (`vercel.json` rewrite). Routes (lazy except Overview):

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
.venv/Scripts/python.exe -m pytest -q                          # 65 pass (v1 Streamlit tests removed)
.venv/Scripts/python.exe -m harvester_risk_atlas all --offline  # rebuild data → web/public/data
cd web && npm run dev            # http://localhost:5173 (also .claude/launch.json "atlas-web")
cd web && npm run build          # tsc + vite + pre-render; Overview first load ~132 KB gz
cd web && npm test               # vitest: 66 pass (parity, URL weights, schemas, text, tooltip)
cd web && npm run e2e            # Playwright + axe, 26 pass; builds and serves on :4173
```

**Browser QA.** Use the Playwright MCP tools (`browser_run_code_unsafe` for mouse and viewport control). Screenshots go to the repo root, in `.playwright-mcp/` (gitignored). The in-app browser pane is too small to judge 1440 px layouts.

Gotchas:
- `maplibre-gl.css` loads later than `app.css`, so override it with higher specificity.
- A full-page screenshot repeats the sticky header mid-page; that is an artifact, not a bug.
- To skip the intro, set `sessionStorage['hra-intro-seen']='1'`.

## 4. Phase status and what to do next
Work in order. Each phase ends with: verify, then update `ORIGINALITY.md` and **this file's status lines**, then commit.

### Done (Phases 0–5, before the tag)
- **Phase 4:** golden parity test (`parity.json` vs `lib/score.ts`, 3 weight sets), unit tests for vocab/explain/tooltip, Playwright + axe e2e (26 tests: URL round-trips, NotFound, one-page brief, 0 serious/critical axe issues on 9 routes, no horizontal scroll at 360–1440, reduced motion, hydration), weights in the URL on How it works (`?w=R,H,E,C`).
- **Phase 5:** CI (`.github/workflows/ci.yml`, jobs `python` and `web`), zod out of the production bundle, CLS 0, `aria-live` on Atlas selection, README and DEPLOY rewrites, Vercel deploy from `main`, branch protection, Streamlit v1 code removed (the old streamlit.app address shows a "moved" page via `app/streamlit_app.py` + `app/requirements.txt`), tag `v2.0-pre-hackathon`.
- **Lighthouse (Overview, live):** mobile with applied throttling 85 (LCP 2.4 s); Lighthouse's default simulated mobile ~65 (it counts font downloads); desktop 98; accessibility 100. The intro is CSS-animated, fades in over the pre-rendered page, and is skipped if the app starts later than 1.5 s.
- **Cut on purpose:** the Compare page, pre-built PDFs (browser print is enough), GitHub Pages (Vercel replaced it).

### Phase 6: hack week (Nov 2–8)
- **Everything after `v2.0-pre-hackathon` is hack-week work:** log each change in the hack-week section of `docs/ORIGINALITY.md`.
- Do real new work inside the week and log it. Candidates: SDMs with spatial block cross-validation (`elapid`, species with ≥ 30 cells), province profiles, Filipino briefs (need native-speaker review), and cohort round 2.
- Devpost: Problem → Data → Method → Prototype → Results → Impact → Limitations, plus a clear pre-existing vs hack-week split.
- **Stale v1 docs to rewrite:** `docs/JUDGING.md`, `docs/SUBMISSION_CHECKLIST.md` and `docs/VIDEO_SCRIPT.md` still describe the v1 Streamlit tour and URL.
- Slides: ≤ 10, and a video ≤ 10 min. Story: "v1 ranked a plant with zero records #1; here's how we found and fixed it" → demo deep links: Overview → Atlas area → top plant → brief → How sure.

## 5. Waiting on the user (ask; don't assume)
- **Curated data:** 18 cohort rows flagged `needs_review` in `data/curated/cohort.csv`, and 29 rows of `harvest_traits.csv`. Species pages show "Awaiting expert review" until cleared.
- **Lagundi** (*Vitex negundo*): WCVP says introduced, so it is gated. Should a `nativity_override` keep it gated?
- **Photos:** check the choices in `data/curated/photos.csv` (4 use CC BY-NC). Abutra and *Hydnocarpus* have no photo.
- **Accounts:** optional IUCN token and GBIF account (DOI downloads).
- **Repo visibility:** the repo is already public (checked 2026-10-14).
- **Leftover branches** (safe to delete, ask first): remote `finalize-docs`, `v2-rebuild` and the old `cursor/*` branches; local `finalize-v2` and `v2-rebuild`.
