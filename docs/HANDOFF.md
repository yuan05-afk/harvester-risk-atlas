# Handoff — Harvester Risk Atlas

Updated: **3 November 2026**.

All project development to date took place on **2–3 November 2026 (Asia/Manila)**, as confirmed by the project owner. Read [`ORIGINALITY.md`](ORIGINALITY.md) for attribution and [`../STATUS.md`](../STATUS.md) for the current state. These documents do not maintain a reconstructed development history.

## Working rules

- Keep the development dates consistent with the owner's confirmation. Do not infer earlier work or a separate development period from timestamps, version names, archive folders or Git reference names.
- Record only work actually done and checks actually run. Do not copy old pass counts, performance scores, deployment claims or completed-review claims into a new status report.
- Never invent IUCN or DENR categories, coordinates or curated facts. Missing data stays missing. The public map shows H3 cells rather than precise plant locations.
- Follow [`DESIGN.md`](DESIGN.md) and write for non-experts.
- Keep changes within the user's request. Do not push, deploy, change repository visibility or publish releases without authorization. A push to the configured production branch may redeploy the site.
- Keep [`ORIGINALITY.md`](ORIGINALITY.md) focused on confirmed development dates and attribution. Do not recreate a retrospective milestone log.

## What is in the repository

The Python package in `src/harvester_risk_atlas/` implements `fetch → base → index → validate → export`. HPI v2 combines rarity, harvest sensitivity and habitat exposure with equal default weights. Climate is reported with weight zero. The pipeline includes gates and Monte Carlo rank uncertainty; see [`METHODS.md`](METHODS.md).

The React/TypeScript app is in `web/`. Data is served from `web/public/data/`.

| Route | Purpose |
|---|---|
| `/` | Overview, hotspot map and priority plants |
| `/atlas?sp=&cell=` | Map with plant and area panels |
| `/plants` | Plant list and CSV download |
| `/species/:slug` | Plant evidence, uncertainty and sources |
| `/species/:slug/brief` | Printable field brief |
| `/how-it-works` | Method, weight explorer, robustness checks, sources and attribution |

`/rankings` and `/methods` redirect to `/plants` and `/how-it-works`.

Key files include `web/src/lib/score.ts`, `web/src/lib/vocab.ts`, `web/src/lib/explain.ts`, `web/src/components/HexMap.tsx` and `web/src/styles/`. Deployment configuration is described in [`../DEPLOY.md`](../DEPLOY.md); check external settings before claiming they are current.

## Local commands

From the repository root:

```powershell
.venv/Scripts/python.exe -m pytest -q
.venv/Scripts/python.exe -m harvester_risk_atlas all --offline
```

From `web/`:

```powershell
npm run dev
npm test
npm run build
npm run e2e
```

These are commands to run, not recorded passing results. For UI changes, inspect desktop and phone layouts. A preview server already running on port 4173 can cause Playwright to reuse an older build.

## Outstanding review

- Check `needs_review` in `data/curated/cohort.csv` and verification fields in `data/curated/harvest_traits.csv`. Keep pending expert reviews visible.
- Any nativity override needs a cited source. Do not override a gate solely to obtain a preferred ranking.
- Review `data/curated/photos.csv`, including attribution, non-commercial licences and herbarium-scan labels.
- IUCN credentials and GBIF DOI downloads are optional; do not invent results when unavailable.
- Keep judging notes, the video script and submission checklist aligned with the current web app and confirmed development dates.
