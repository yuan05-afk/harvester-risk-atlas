# Status — Harvester Risk Atlas

Last updated: **3 November 2026**.

All project development to date took place on **2–3 November 2026 (Asia/Manila)**, as confirmed by the project owner. See [`docs/ORIGINALITY.md`](docs/ORIGINALITY.md) for the development dates and attribution record.

## Current repository contents

- Python pipeline in `src/harvester_risk_atlas/`: fetch, clean, build components, score, quantify uncertainty, validate and export.
- Web app in `web/`: Overview, Atlas, plant list, plant profiles, printable field briefs and How it works.
- Published data in `web/public/data/`; source and curated inputs in `data/`.
- HPI v2 uses equal weights for rarity, harvest sensitivity and habitat exposure. Climate exposure is reported with default weight zero.
- The committed outputs contain 51 taxa, with 29 scored and 22 gated. These describe the bundled data, not completion of expert review.
- Test suites and CI configuration are present. Their presence does not establish that the current checkout has passed them.

## Review still needed

- Review curated cohort and harvest-trait rows marked as awaiting verification.
- Review plant photograph choices, credits and licence restrictions.
- Check the current app and submission materials before release.
- Run the relevant checks after changes and record their actual results.

## Documentation maintenance

Keep this file as a current-state summary. Do not add reconstructed milestone histories, unverified completion claims or invented AI-tool dates. Update the handoff and attribution documents when confirmed facts change.

## Verification for this checkout

Checked on **3 November 2026**:

- Inventoried all 426 tracked files and searched the 354 readable text and compressed-source files for earlier project-development claims. The remaining earlier dates are source retrieval and citation metadata.
- Checked the generated production bundle, hidden project configuration, and six connected AI plan and memory documents. No earlier project-development claims remain in that active text.
- Regenerated validation and the web data export. The export timestamp is the actual regeneration time; project development is separately recorded as November 2–3.
- Verified that scientific scores, source records, archived datasets, geographic layers and parity values are unchanged, allowing for Windows line endings.
- Python: **73 passed**. Web unit tests: **66 passed**. Browser tests: **33 passed**. Production build: **passed**.
- Inspected the corrected development text and export date at 1440 × 900 and 390 × 844, with no horizontal overflow.
- Removed stale generated local QA reports, screenshots, snapshots and logs.

Source-data dates remain provenance rather than app-development dates. The publication branch starts from a corrected initial commit authored on November 3, 2026. Older local archive branches are kept separately and are excluded from publication. Verify current publication and deployment state directly on GitHub and Vercel.
