# Judging — Harvester Risk Atlas

EthnoHack 2026, Track 3: Biodiversity & Sustainability.

**Development:** All project development to date took place on **2–3 November 2026 (Asia/Manila)**, as confirmed by the project owner. Attribution and AI assistance are disclosed in [`ORIGINALITY.md`](ORIGINALITY.md).

**Demo:** https://harvester-risk-atlas.vercel.app · **Slides:** `submission/Harvester-Risk-Atlas-slides.pdf` · **Method:** [`METHODS.md`](METHODS.md)

The atlas ranks which wild medicinal plants of the Philippines need conservation attention first, where they occur, why, and how uncertain each rank is. It is for research and education, not medical advice, a harvest permit or a Red List assessment.

## Where to find evidence for each criterion

| Criterion | What to look at |
|---|---|
| **Scientific relevance** | Wild harvest of medicinal roots, bark and whole plants is a recognised conservation problem (Cunningham 2001; Schippmann et al. 2002), and no dataset measures it in the Philippines. The index combines rarity, harvest sensitivity and habitat exposure. `METHODS.md` §3 |
| **Innovation** | Effort-corrected rarity from a target-group survey layer; a Jeffreys-posterior Monte Carlo that propagates evidence and weight uncertainty into rank intervals and tiers; a live weight explorer tested for parity with the Python index; a printable field brief per plant |
| **Technical implementation** | `src/harvester_risk_atlas/` pipeline (`fetch → base → index → validate → export`); static React/TypeScript app in `web/`; pytest, Vitest, Playwright + axe in CI (`.github/workflows/ci.yml`); offline rebuild from a committed snapshot |
| **Data science quality** | One recorded reason per dropped record (`METHODS.md` §2); fixed-anchor scales; gates instead of guessed values; 2,000-draw uncertainty; robustness checks in `web/public/data/validation.json` (`METHODS.md` §6) |
| **Feasibility** | Free static hosting; open global sources (GBIF, WCVP, WDPA, Hansen) mean another country needs a new cohort and local layers rather than a new method |
| **Impact** | A shortlist of plants and areas for DENR, protected-area boards, LGUs, harvester groups and researchers; the field brief for use offline |
| **Presentation** | Slides (10), video ([`VIDEO_SCRIPT.md`](VIDEO_SCRIPT.md)), Devpost page ([`../submission/devpost.md`](../submission/devpost.md)) |

## Index in one paragraph

**HPI v2** is the equally weighted mean of rarity (R), harvest sensitivity (H) and habitat exposure (E). Climate exposure (C) is reported with default weight zero, because projected warming hardly differs between plants. Plants that are not native per WCVP, or that occupy fewer than 5 hexagons, are listed without a score. The bundled cohort has 51 taxa: 29 scored and 22 gated. The 29 scored plants fall into 5 *Needs attention now*, 4 *Keep watch* and 20 *Lower concern*. The checks test robustness, not predictive accuracy.

## Demonstration path

1. **Overview:** the question, the hotspot map and the priority plants.
2. **Atlas:** select a plant or an area. Locations appear as H3 cells, never as precise points.
3. **Plant profile:** the main reasons, evidence gaps, uncertainty and sources.
4. **Field brief:** the printable A4 sheet.
5. **How it works:** the weight explorer, then the robustness checks and limitations.

## Attribution and limitations

External data, photos, fonts and libraries keep their own licences and credits. See [`ORIGINALITY.md`](ORIGINALITY.md), [`METHODS.md`](METHODS.md) and the plant-level source records.

AI assistants, including Claude Code, helped draft and edit code and documentation, and drafted the harvest-trait rows from cited sources. The project owner is responsible for reviewing the submission. Curated traits awaiting expert verification remain marked as such. IUCN and DENR categories are never invented.

Submission checklist and rules audit: [`SUBMISSION_CHECKLIST.md`](SUBMISSION_CHECKLIST.md).
