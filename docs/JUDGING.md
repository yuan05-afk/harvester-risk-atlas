# Judging — Harvester Risk Atlas

EthnoHACK 2026, Track 3: Biodiversity & Sustainability.

**Development:** All project development to date took place on **2–3 November 2026 (Asia/Manila)**, as confirmed by the project owner. Attribution and AI assistance are disclosed in [`ORIGINALITY.md`](ORIGINALITY.md).

**Demo address:** https://harvester-risk-atlas.vercel.app

## Problem and approach

The atlas helps identify which wild medicinal plants of the Philippines need conservation attention, where they occur, why they rank as they do, and how uncertain that ranking is. It is for research and education, not medical advice, a harvest permit or a Red List assessment.

The **Harvest Priority Index (HPI v2)** combines three equally weighted components:

| Component | Evidence |
|---|---|
| Rarity | Effort-corrected occupied cells and native range |
| Harvest sensitivity | Cited traits: harvested parts, life form and sourcing |
| Habitat exposure | Protected-area gap and province-level forest loss |

Climate exposure is reported with default weight zero. Plants that are not native or have insufficient occupied cells are listed without a score. The bundled cohort has 51 taxa: 29 scored and 22 gated. Monte Carlo draws produce rank intervals and priority tiers. Checks test robustness rather than predictive accuracy. Full details: [`METHODS.md`](METHODS.md).

## Demonstration path

1. **Overview:** show the question, hotspot map and priority plants.
2. **Atlas:** select a plant or area. Locations appear as H3 cells rather than precise points.
3. **Plant profile:** explain the main reasons, evidence gaps, uncertainty and sources.
4. **Field brief:** open the printable A4 sheet.
5. **How it works:** try the weight explorer, then show robustness checks and limitations.

## Attribution and limitations

External data, photos, fonts and libraries retain their own licences and credits. See [`ORIGINALITY.md`](ORIGINALITY.md), [`METHODS.md`](METHODS.md) and the plant-level source records.

AI assistants helped draft and edit code and documentation. The project owner is responsible for reviewing the submission. Curated traits awaiting expert verification remain marked as such. IUCN and DENR categories must never be invented.

Video script: [`VIDEO_SCRIPT.md`](VIDEO_SCRIPT.md). Submission checklist: [`SUBMISSION_CHECKLIST.md`](SUBMISSION_CHECKLIST.md).
