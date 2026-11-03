# Devpost submission: Harvester Risk Atlas

Copy each block into the matching Devpost field. Text in `[square brackets]` must be filled in or removed before submitting.

Deadline: **8 November 2026, 10:00 Athens time (EET, UTC+2)**: 16:00 in Manila (UTC+8) and 08:00 UTC. The Devpost form shows 17:00 GMT+8, but the organisers' final reminder gives 10:00 Athens time, so treat **16:00 Manila** as the deadline.

---

## Step 1 · Project overview

### Project name (max 60 characters)

```
Harvester Risk Atlas
```

### Elevator pitch (max 200 characters)

```
Which wild medicinal plants of the Philippines need conservation attention first, where, why, and how sure we are: an open, reproducible ranking with uncertainty.
```

(162 characters.)

### Thumbnail (3:2, JPG/PNG/GIF, max 5 MB)

`submission/gallery/01-overview.png` (1500 × 1000).

---

## Step 2 · Project details

### About the project (Markdown, LaTeX supported)

Paste everything between the two rules below.

---

**Track 3: Biodiversity & Sustainability.** Live app: https://harvester-risk-atlas.vercel.app · Code: https://github.com/yuan05-afk/harvester-risk-atlas · Slides: [PDF](https://github.com/yuan05-afk/harvester-risk-atlas/blob/main/submission/Harvester-Risk-Atlas-slides.pdf)

> For research and education. Not medical advice, not a harvest permit, and not a Red List assessment.

## Inspiration

Up to **4 billion people** rely on herbal medicine as their main source of healthcare ([Kew, State of the World's Plants and Fungi 2020](https://www.nhm.ac.uk/discover/news/2020/september/two-in-five-plants-are-threatened-with-extinction.html)). About **30,000** plant species have documented medicinal uses. An estimated **60–90%** of those in international trade are collected from the wild, only **7%** have been assessed for the IUCN Red List, and **1 in 5** of those assessed is threatened. The trade tripled in value between 1999 and 2015, to over US$3 billion ([IUCN and TRAFFIC, *Wild at Home*, 2018](https://iucn.org/news/species/201806/wild-home-threats-and-opportunities-trade-wild-plants)).

The Philippines lost **1.47 million hectares of tree cover** between 2001 and 2023. That is about 175 ha a day, roughly 245 football pitches, and 7.9% of its tree cover in 2000 (Hansen et al. 2013, via Global Forest Watch; tree-cover loss includes plantation harvest). The government's threatened-plant list (DENR DAO 2026-20) names **1,186 plants** by our count, 248 of them critically endangered.

Many of the Philippines' medicinal plants are still gathered from the wild. Stuart's *Philippine Medicinal Plants* describes most of the plants in our cohort as "wild-crafted", and for many of them the part used is the root, the bark or the whole plant. Taking those parts can kill the plant, and slow-growing trees and lianas recover slowly (Cunningham 2001; Schippmann, Leaman & Cunningham 2002).

No dataset records how much of each plant is harvested. Only 4 of the 29 native plants we could score appear on the national threatened-plant list (DENR DAO 2026-20). Tongkat ali, whose roots are dug up and sold, is officially Endangered, yet open databases hold only 5 reliable records of it in the whole country. Rangers, LGU staff, harvester groups and students have limited time in the field. We wanted to give them a clear, honest answer to one question: **which plants should we look at first, where, and how far can we trust that order?**

[Optional: add one or two sentences on your own motivation.]

## What it does

Harvester Risk Atlas ranks **29 native medicinal plants** (from a cohort of 51) with a **Harvest Priority Index (HPI v2)** and shows the result as an interactive atlas:

- **Overview**: a hotspot map of the Philippines and the five plants that need attention now.
- **Atlas**: pick a plant to see where it grows, or click an area to see which plants grow there. Plants appear only as H3 hexagons of about 250 km², never as points, so plants at risk from collection stay hard to find.
- **Plant profiles**: the three reasons for each rank in plain words, the evidence behind them, how far the rank could move, sources, and credited photos.
- **Field briefs**: a one-page A4 sheet per plant to print and take into the field.
- **How it works**: the method, a **weight explorer** that re-ranks the plants live (the weights are kept in the URL, so a view can be shared), and the robustness checks.

Every rank is given with its range, for example: *"Ranked 2nd of 29. It could be anywhere from 1st to 5th."*

## How we built it

**Data.** We used GBIF occurrence records for the Philippines, Kew's World Checklist of Vascular Plants (WCVP) for native status and range, WDPCA Philippines for protected areas, Hansen/Global Forest Watch for tree-cover loss by province, WorldClim 2.1 with CMIP6 projections for climate, and Stuart's *Philippine Medicinal Plants* for harvest traits. DENR DAO 2026-20 is used for validation only. Of 9,660 Philippine GBIF records, 4,789 remain after a nine-rule cleaning pass. Each dropped record is assigned exactly one reason.

**Index.** Each plant gets three components, each in $[0, 1]$ on fixed anchors rather than cohort min–max, so adding a plant never changes another plant's values:

- **Rarity (R)**: the *reporting rate*, the share of well-surveyed hexagons (≥ 100 vascular-plant records; 332 of 1,267) where the plant was recorded, on a log scale. This corrects for where botanists have looked. It is averaged with how few world regions WCVP lists the plant as native to.
- **Harvest harm (H)**: which part is harvested, the life form, and whether it is only wild-sourced, from a rubric following Cunningham (2001).
- **Habitat pressure (E)**: the share of occupied hexagons outside protected areas, and provincial forest loss from 2001 to 2023, scaled by forest dependence.

$$\text{HPI} = \tfrac{1}{3}R + \tfrac{1}{3}H + \tfrac{1}{3}E \quad (\text{climate } C \text{ is shown with weight } 0)$$

Climate is shown but carries no weight: projected warming is about +1.5 °C for every plant, so it cannot separate them. Plants are **gated** (listed but not scored) when WCVP does not list them as native, or when they have fewer than 5 occupied hexagons.

**Uncertainty.** 2,000 seeded Monte Carlo draws perturb weights and evidence together. The weights follow a Dirichlet distribution centred on the defaults. The reporting rate is drawn from the Jeffreys posterior $\text{Beta}(k+\tfrac12,\, N-k+\tfrac12)$. Protected-area and forest-loss shares are bootstrapped over occupied cells. Each plant gets a median rank, a 90% rank interval and $P(\text{top quartile})$, which sets its tier: **Needs attention now** ($\ge 0.8$), **Keep watch** ($0.3$–$0.8$) or **Lower concern**.

**Software.** A Python pipeline (`fetch → base → index → validate → export`) using pandas, GeoPandas, H3 and rasterio writes static JSON. A React + TypeScript + MapLibre web app reads it. A golden-file test keeps the browser's weight explorer arithmetically identical to the Python index. Tests cover the Python pipeline (pytest), web unit tests (Vitest), and browser and accessibility tests (Playwright + axe), all run in GitHub Actions. A committed raw-data snapshot lets anyone rebuild every number offline with `python -m harvester_risk_atlas all --offline`.

## Results

| Tier | Plants |
|---|---|
| Needs attention now | 5: tongkat ali (*Eurycoma longifolia*), kalingag (*Cinnamomum mercadoi*), bitaog (*Calophyllum blancoi*), tibig (*Ficus nota*), amuyon (*Goniothalamus amuyon*) |
| Keep watch | 4: dita (*Alstonia scholaris*), banag (*Smilax bracteata*), bayag-usa (*Voacanga globosa*), bunga (*Areca catechu*) |
| Lower concern | 20 |
| Not ranked | 22 (not native per WCVP, or too few records) |

No ground truth exists for harvest priority, so we tested **robustness, not accuracy**:

| Check (29 scored plants) | Result |
|---|---|
| Arithmetic vs geometric mean | Spearman ρ = 0.97 |
| Arithmetic mean vs mean component rank | ρ = 0.89 |
| Well-surveyed threshold 50 or 200 instead of 100 | ρ ≥ 0.997 |
| Leave R / H / E out | ρ = 0.73 / 0.88 / 0.94 (rarity moves the ranking most) |
| Median width of the 90% rank interval | 5 places |
| DENR-threatened plants (n = 4) | mean rank 9.3 vs 15 expected; one-sided permutation p = 0.076 |

The DENR check is directional only. Two listed plants (tongkat ali, Endangered; kalingag, Other Threatened Species) rank in the top five even though the list is not an input, and two rank lower.

One data-quality note: tongkat ali rests on only 5 reliable records in 5 hexagons, exactly at the gate. Its high rarity partly reflects how little it has been recorded, which is why its rank is given as a range (1st to 5th) and why field surveys are the next step.

## Challenges we ran into

- **Survey effort.** A roadside weed collects more records than a forest liana, so raw record counts measure attention as much as rarity. We built a target-group survey-effort layer and scored rarity only in well-surveyed cells.
- **Bootstrapping range.** Resampling occupied cells with replacement shrinks the unique-cell count and biases range measures, so we draw the reporting rate from a Beta posterior instead.
- **Nativity surprises.** WCVP lists lagundi (*Vitex negundo*), a flagship Department of Health herb, as introduced to the Philippines. We kept the gate and explain it, rather than overriding data to obtain a preferred ranking.
- **Climate that does not discriminate.** Projected warming is nearly uniform across plants. We report it but give it zero weight, and the weight explorer lets readers add it.

## Accomplishments that we're proud of

- Every rank is shown with its uncertainty, in words a ranger or harvester can use.
- Sensitive locations are generalised by design (Chapman 2020); no layer exposes raw coordinates.
- The pipeline is fully reproducible offline, and the browser arithmetic is tested against the Python index.

## What we learned

A transparent screen with honest uncertainty is more useful than a single confident number. Saying "we cannot separate these plants" is a valid result, and the tiers are designed to say it.

## Responsible research

- **Health claims:** none. The atlas is about conservation priority, not therapeutic value, and every page carries the disclaimer.
- **Traditional knowledge:** uses and local names come only from a published, cited compendium (Stuart), with a link per plant and no redistribution of its text. No community, interview or personal data were collected.
- **Sensitive data:** plants appear only as ~250 km² hexagons.
- **Licences:** each source is credited with its licence in the app and the repository. The data licences are CC0, CC BY 4.0, CC BY-NC and Protected Planet non-commercial terms. Photos are credited individually.
- **AI use:** AI assistants (including Claude Code) helped write the code and documentation and drafted the harvest-trait rows from cited Stuart pages. **None of the 29 trait rows is expert-verified yet**, and each plant page says "being checked". The project owner is responsible for the submission.
- **Limitations:** GBIF records are presence-only and effort-biased. Harvest harm is a literature rubric, not field data. Forest loss is measured per province. IUCN categories are linked only when an API token is configured, and they are never invented.

## Assumptions

- Cleaned GBIF records show where a plant occurs, and a plant's absence from a well-searched hexagon reflects real scarcity.
- Taking roots, bark or the whole plant, and harvesting slow-growing woody plants, harms a population more than taking leaves or fruit (Cunningham 2001; Schippmann et al. 2002).
- Provincial forest loss approximates pressure in the hexagons where the plant was recorded.
- WCVP's nativity calls are correct unless a cited source overrides them.
- Equal weights are a neutral default when there is no consensus (OECD/JRC 2008).

## What's next for Harvester Risk Atlas

1. **Expert verification** of the harvest traits and cohort with Filipino ethnobotanists and harvester communities.
2. **Species distribution models** with spatial block cross-validation, to estimate range beyond the recorded hexagons.
3. **Trade and market data**, to replace the harvest-harm proxy, and Red List linking.
4. **Other countries**: the global sources (GBIF, WCVP, WDPA, Hansen) carry over; a new cohort and local layers are needed.

## Team

- **Yuan Andrei C. Mariano** (Devpost [@yuan05-afk](https://devpost.com/yuan05-afk)): project lead; data pipeline, Harvest Priority Index, web atlas and documentation.
- **Alicia Jhyle Vilale** (Devpost [@asvilale](https://devpost.com/asvilale)): quality assurance and checking, the presentation, and directing and editing the pitch video.

## Development and attribution

Created and developed on 2–3 November 2026 (Asia/Manila), during EthnoHack 2026. Third-party datasets, libraries, fonts and photos are listed with their licences in [`docs/ORIGINALITY.md`](https://github.com/yuan05-afk/harvester-risk-atlas/blob/main/docs/ORIGINALITY.md). The full method is in [`docs/METHODS.md`](https://github.com/yuan05-afk/harvester-risk-atlas/blob/main/docs/METHODS.md).

---

### Built with (max 25 tags)

```
python, pandas, numpy, geopandas, shapely, h3, rasterio, pyarrow, pytest, typescript, react, vite, maplibre-gl, d3, zod, vitest, playwright, axe-core, github-actions, vercel, gbif, wcvp, worldclim, global-forest-watch, protected-planet
```

(25 tags.)

### "Try it out" links

```
https://harvester-risk-atlas.vercel.app
https://github.com/yuan05-afk/harvester-risk-atlas
https://github.com/yuan05-afk/harvester-risk-atlas/blob/main/docs/METHODS.md
https://github.com/yuan05-afk/harvester-risk-atlas/blob/main/submission/Harvester-Risk-Atlas-slides.pdf
```

### Image gallery (3:2, max 5 MB each, up to 15)

Upload in this order from `submission/gallery/`, with these captions:

| File | Caption |
|---|---|
| `01-overview.png` | Overview: the hotspot map and the plants that need attention now |
| `02-atlas-tongkat-ali.png` | Atlas: tongkat ali shown only as ~250 km² hexagons, never as points |
| `03-plant-profile.png` | Plant profile: three reasons in plain words and the rank with its range |
| `04-where-it-grows.png` | Where it grows: occupied areas, protected share, forest loss and provinces |
| `05-field-brief.png` | Field brief: one printable A4 page per plant |
| `06-weight-explorer.png` | Weight explorer: change the weights and the ranking updates live |
| `07-robustness-checks.png` | How sure is the ranking: the robustness checks |
| `08-plants-list.png` | All plants by tier, with CSV download |
| `09-phone-profile.png` | Phone layout of a plant profile |

`09-phone-profile.png` is portrait, so Devpost will crop it into the 3:2 frame. Leave it out if the crop looks poor.

### Video demo link

```
[YouTube or Vimeo URL: record from docs/VIDEO_SCRIPT.md, max 10 minutes]
```

---

## Step 3 · Additional info (judges only)

### Upload a file (max 35 MB)

Upload `submission/Harvester-Risk-Atlas-slides.pdf` (10 slides, about 2.4 MB). This form accepts a single file, so upload the PDF only. The same PDF is linked from the project story and the "Try it out" links.

Rebuild the slides and screenshots after any app change:

```bash
cd web && npm ci && npx playwright install chromium
node ../submission/build.mjs
```

---

## Step 4 · Before you press Submit

- [ ] Correct challenge track selected: **Track 3: Biodiversity & Sustainability**.
- [x] Team of 2 on Devpost: Yuan Andrei C. Mariano and Alicia Jhyle Vilale.
- [ ] Alicia Jhyle Vilale confirms they registered for EthnoHack by 31 October, 23:00.
- [x] Roles filled in for both members in the Team section above.
- [ ] Video uploaded (≤ 10 min, public or unlisted) and its link pasted.
- [ ] Slides PDF uploaded.
- [ ] Optional motivation sentence written or removed.
- [ ] Every link opens in a private browser window.
