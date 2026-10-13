# Methods: Harvest Priority Index (HPI v2)

EthnoHack 2026, Track 3: Biodiversity & Sustainability.

HPI v2 is a transparent, reproducible screen that orders Philippine medicinal plants for conservation attention. It is **not** a Red List assessment, **not** a harvest permit, and **not** medical advice. No dataset measures harvest volumes, so the index makes no claim to measure harvest pressure. It combines evidence on **vulnerability to wild harvest** and **exposure of the places a species grows**, and it reports how certain each ranking is.

- Build: `python -m harvester_risk_atlas all` (network once), then `python -m harvester_risk_atlas index validate --offline`.
- Code: `src/harvester_risk_atlas/` (`components.py`, `index.py`, `uncertainty.py`, `validation.py`, `pipeline.py`).
- Outputs: `data/processed/v2/scores.csv`, `validation.json`.

---

## 1. Cohort

The cohort has 51 taxa in `data/curated/cohort.csv`:
- 35 carried over from v1.
- 16 native, wild-crafted medicinal plants added in v2 from Stuart's *Philippine Medicinal Plants* (StuartXchange).

Rows marked `needs_review = True` await confirmation by the team or a domain expert.

Names resolve against the GBIF backbone (`species/match`), and synonyms resolve to the accepted key. *Mentha × piperita* (v1's "yerba buena") has no Philippine records and is flagged: the herb sold as yerba buena in the Philippines is not peppermint.

## 2. Occurrence data

**Source.** GBIF occurrence API, country = PH, `occurrenceStatus = PRESENT`, georeferenced records only.
- Exact totals come from search facets, and every record is paged up to a cap of 5,000 per species. No species reached the cap.
- v1 used the first 60 API results per species. That sample was not random, and the cap made every count equal.

**Cleaning** (`clean.py`). Each dropped record gets exactly one reason: the first rule it fails, in this order.

| Rule | Drops |
|---|---|
| missing coordinates | no lat/lon |
| zero coordinates | lat or lon = 0, or lat = lon |
| severe GBIF issue | e.g. `COUNTRY_COORDINATE_MISMATCH`, `PRESUMED_SWAPPED_COORDINATE` |
| not wild basis | `LIVING_SPECIMEN` (botanic gardens), `FOSSIL_SPECIMEN` |
| cultivated | `establishmentMeans = MANAGED` |
| imprecise | coordinate uncertainty > 10 km, or both coordinates whole degrees |
| country centroid | within 5 km of the Philippines' geographic centre |
| off land | outside the Natural Earth land mask buffered by ~3 km |
| duplicate | same species, coordinates to 4 dp, and year |

Across 9,660 PH records, 4,789 remain. Most of the drops are duplicate specimens and literature citations of the same collection. Province-centroid and institution-coordinate tests are not run, because no reference layer for them is shipped.

**Spatial units** (`grid.py`)
- **H3 resolution 5 hexagons**: mean area about 250 km², edge about 9 km. These are the unit for occupancy, protected-area coverage, maps, and the generalised display of sensitive species.
- **AOO and EOO** follow IUCN guidelines (2 × 2 km cells; convex hull with geodesic area) and are reported in species profiles. They do **not** enter the score. Record-based AOO is far below true range for every species, and the archipelago makes every EOO huge, so neither separates species here.

## 3. Components

Every component is in [0, 1], where higher means more priority, and missing means "not measured" (NaN), never a guessed number. All scales are anchored to fixed reference points rather than the cohort's own minimum and maximum. Adding or removing a species therefore never changes another species' values (v1's min–max scaling did).

### R. Range restriction
Mean of two parts:

- **Local rarity, effort-corrected.** Raw record counts mix rarity with attention: a roadside weed collects more citizen-science records than a forest liana.
  - The *reporting rate* is the share of **well-surveyed** Philippine cells (≥ 100 GBIF vascular-plant records; 322 of 1,244 cells) where the species was recorded.
  - The effort layer is a target-group count of all Tracheophyta records per cell (`sources/effort.py`).
  - It is scored on a log scale: a 50% reporting rate gives 0, and 0.5% gives 1.
  - A species never recorded in a well-surveyed cell is *unmeasured* there, not "rare".
- **Global restriction.** The number of TDWG level-3 regions where WCVP lists the species as native. One region gives 1; 50 or more give 0, on a log scale.

### H. Harvest sensitivity (curated)
Mean of three sub-scores, from `data/curated/harvest_traits.csv`. Each row cites a Stuart species page, with access date.

| Sub-score | Values |
|---|---|
| Part harvested | roots, rhizomes, bark, whole plant 1.0 · stems 0.75 · seeds, fruit, exudate 0.5 · leaves, flowers 0.25. The score is half the first-listed part plus half the most destructive part listed. |
| Life form | tree 1.0 · palm 0.9 · liana 0.8 · shrub 0.6 · fern 0.5 · herb or herbaceous vine 0.3 |
| Sourcing | wild only 1.0 · wild and cultivated 0.5 |

The rationale follows Cunningham (2001) and Schippmann, Leaman & Cunningham (2002): harvesting roots, bark or whole plants, and harvesting slow-regenerating woody species, is least sustainable.
- Sourcing comes from Stuart's *Availability* line and any mention of cultivation. Almost every page says "wild-crafted", so sourcing is the weakest of the three.
- Values are drafted, and **must be verified** (column `verified_by`) before they are treated as final.
- A species without cited traits has H = NaN and is flagged *partial*.

### E. Habitat exposure
Mean of two parts:

- **Protected-area gap:** 1 − the mean share of each occupied cell's area inside WDPCA Philippines polygons (equal-area projection).
  - v1 counted *points* inside protected areas. Observers cluster in parks, which biases that measure toward overlap. Counting occupied cells removes most of the bias.
- **Forest-loss exposure:**
  - Tree-cover loss from 2001–2023, divided by the 2000 extent (30% canopy threshold; Hansen et al. 2013, via Global Forest Watch), in the provinces where the species was recorded. Each cell takes the modal province of its records.
  - Scaled 0 → 0 and 20% → 1, then multiplied by forest affinity: forest 1, mixed 0.5, open 0.
  - Clearing does not threaten open-habitat species and may favour them.

### C. Climate exposure (reported, weight 0)
- Measured on occupied cells: WorldClim 2.1 baseline vs CMIP6 2041–2060 under SSP2-4.5, using five GCMs (MIROC6, MPI-ESM1-2-HR, EC-Earth3-Veg, IPSL-CM6A-LR, UKESM1-0-LL).
- Projected warming is **about +1.5 °C for every species** (GCM range +1.0 to +2.3 °C), so it does not separate species within this cohort.
- The exceedance measure (the share of cells whose future temperature exceeds the species' warmest 5% of current Philippine cells) mostly reflects where records sit within a thermal range that is truncated at the national border.
- Weighting either would add noise, so C is shown per species with its GCM range, and its default weight is 0. The weight explorer lets readers add it.

## 4. Gates
A species is shown but **not scored** when:
- **not native:** WCVP does not list it as native to the Philippines (`introduced`, `not_listed`, or `not_found`). A cited override in `cohort.csv` can change this, for example where a team source disagrees with WCVP.
  - WCVP lists lagundi (*Vitex negundo*) as introduced to the Philippines. It is therefore not prioritised for wild-harvest conservation, even though it is a flagship DOH herb.
- **insufficient data:** fewer than 5 occupied cells after cleaning.

## 5. Aggregation, uncertainty and tiers

**Score:** a weighted arithmetic mean of R, H and E with **equal default weights** (⅓ each; C = 0). Equal weighting is the neutral choice when there is no consensus (OECD/JRC 2008). Missing components drop out and the remaining weights rescale; the species is flagged *partial*.

**Uncertainty** (`uncertainty.py`). 2,000 seeded Monte Carlo draws perturb weights and evidence together:
- Weights follow a Dirichlet distribution centred on the defaults, with concentration 10.
- The reporting rate is drawn from Beta(k + ½, N − k + ½), the Jeffreys posterior for k occupied of N well-surveyed cells. This is used instead of resampling cells, because resampling occupied cells with replacement shrinks the unique-cell count and biases range measures.
- Protected-area and forest-loss shares are bootstrapped over occupied cells.
- Curated traits and WCVP region counts are held fixed.

Outputs: median rank, a 90% rank interval (5th–95th percentile; rank 1 = highest), and P(top quartile).

**Priority tiers** replace v1's fixed 0.33 / 0.66 bands:

| Tier | Rule |
|---|---|
| High attention | P(top quartile) ≥ 0.8 |
| Watch | 0.3 ≤ P(top quartile) < 0.8 |
| Lower | P(top quartile) < 0.3 |
| Not scored | gated (section 4) |

Tiers are honest by construction: when the evidence cannot separate species, they share a tier.

**Main driver:** the weighted component furthest above the scored cohort's median. It is blank when no component is above the median.

## Weight sensitivity

The Methods page has a weight explorer. Readers set their own weights for R, H, E and C. The weights are clipped at zero and rescaled to sum to 1, and the cohort re-ranks live against the published equal-weight ranking.

This is sensitivity analysis, not a new official index. The explorer reweights the stored components and does not refit them. A golden-file test keeps the browser's arithmetic identical to the Python pipeline's.

## 6. Validation (`validation.json`)

No ground truth exists for harvest priority. These checks test robustness and plausibility, not accuracy.

| Check | Result (29 scored species) |
|---|---|
| Aggregation: weighted mean vs geometric mean | Spearman ρ = 0.97 |
| Aggregation: weighted mean vs mean component rank | ρ = 0.89 |
| Leave R out / H out / E out | ρ = 0.73 / 0.88 / 0.94. R moves the ranking most. |
| Well-surveyed threshold 50 or 200 instead of 100 | ρ ≥ 0.997 |
| Median 90% rank interval | 5 places |
| Nationally threatened species (DENR DAO 2026-20) | 4 in the scored cohort. Mean rank 9.3 vs 15 expected; one-sided permutation p = 0.076. *Eurycoma longifolia* (EN) and *Cinnamomum mercadoi* (OTS) are High attention; *Pterocarpus indicus* (VU) and *Helminthostachys zeylanica* (EN) rank lower. A directional check only. |
| HPI v1.1 vs v2, 14 shared species | ρ = 0.09: v2 is a different ranking, not a re-styling. |

## 7. Limitations
- **GBIF records are presence-only and effort-biased.** The reporting rate corrects for effort only to the extent the target-group layer captures it.
- **Harvest sensitivity is a literature rubric,** not field data on harvest volumes or trade. Its values await expert verification.
- **WCVP nativity calls decide the gate.** Some, such as lagundi, will surprise users; a cited override can change them.
- **Forest loss is summarised by province,** not at each occurrence.
- **Climate exposure at 10′ with national records cannot separate species** (section 3C).
- **The Red List is not linked** unless an IUCN API token is configured. Categories are never invented.

## 8. Sensitive data
High-attention species are shown only as H3 cells (about 250 km²), never as points. Following Chapman (2020), precise locations of species at risk from collection are not published. No layer of the app exposes raw coordinates.

## 9. Data sources and licences

| Source | Use | Licence / terms |
|---|---|---|
| GBIF occurrences (API, accessed Oct 2026) | records, counts, effort layer | per-dataset CC0 / CC BY / CC BY-NC; GBIF citation guidelines |
| WCVP (Govaerts et al. 2021) via GBIF checklist `f382f0ce-…` | nativity, native regions | CC BY 4.0 |
| WorldClim 2.1 (Fick & Hijmans 2017), baseline and CMIP6 2041–2060 | climate exposure | free for research and education |
| WDPCA Philippines (UNEP-WCMC, via HDX) | protected areas | Protected Planet terms, non-commercial |
| Hansen et al. 2013 / Global Forest Watch province statistics | forest loss | CC BY 4.0 |
| DENR DAO 2026-20 | validation only | public government document |
| Stuart GU Jr., *Philippine Medicinal Plants* (StuartXchange) | curated traits, cohort additions | cited per species; text not redistributed |
| Natural Earth land | land mask | public domain |
| IUCN Red List API v4 (optional) | Red List status | IUCN terms; never invented |

## References
- Chapman AD (2020). *Current Best Practices for Generalizing Sensitive Species Occurrence Data.* GBIF Secretariat.
- Cunningham AB (2001). *Applied Ethnobotany: People, Wild Plant Use and Conservation.* Earthscan.
- Fick SE, Hijmans RJ (2017). WorldClim 2. *Int J Climatol* 37: 4302–4315.
- Govaerts R et al. (2021). The World Checklist of Vascular Plants. *Sci Data* 8: 215.
- Hansen MC et al. (2013). High-resolution global maps of 21st-century forest cover change. *Science* 342: 850–853.
- IUCN Standards and Petitions Committee (2024). *Guidelines for Using the IUCN Red List Categories and Criteria*, v16.
- OECD/JRC (2008). *Handbook on Constructing Composite Indicators.*
- Schippmann U, Leaman DJ, Cunningham AB (2002). *Impact of Cultivation and Gathering of Medicinal Plants on Biodiversity.* FAO.
- Zizka A et al. (2019). CoordinateCleaner. *Methods Ecol Evol* 10: 744–751.

---

## Appendix: HPI v1.1 (archived) and why it was replaced

v1.1 (tag `v1.1-baseline`; data in `data/archive/v1.1/`) computed `HPI = 0.30·R + 0.25·C + 0.25·H + 0.20·P` with cohort min–max scaling. An audit on 14 Oct 2026 found:

1. **Rarity was a fetch artifact.** 33 of 35 species had exactly 60 records (the fetch cap), so R reduced to a hand-typed endemism label.
2. **The top-ranked species had no records.** *Mentha × piperita*, with zero records, ranked first (HPI 0.556) on imputed values.
3. **The "decline" cue measured recording method.** The recent-record share correlated with the citizen-science share at Spearman ρ = 0.76. Abutra's high harvest score came from its records being 1909–1996 herbarium specimens.
4. **Out-of-scope distances.** Records outside the Philippines were measured against Philippine protected areas (*Eurycoma longifolia*: 1,252 km).
5. **The bands did not discriminate.** 33 of 35 species were "Moderate".
6. **Rankings were fragile.** Abutra's 90% rank interval under plausible weights was 1–30.
7. **The RandomForest suitability sketch had leakage.** It scored 1.00 cross-validation accuracy for every species, including coconut, because presences carried one constant climate value and background points carried jittered values. It is removed.
8. **KMeans archetypes were run on these artifact-driven components without validation.** They are removed from the product.
