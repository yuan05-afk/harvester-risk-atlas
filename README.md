# Harvester Risk Atlas

EthnoHACK 2026 Track 3. A Streamlit atlas for a fixed catalog of wild-harvested plants.

The workflow is **Map → Dossier → Brief**. Demo mode keeps *Aquilaria malaccensis* selected and compares it with *Boswellia sacra*.

## Run

```bash
pip install -r requirements.txt
streamlit run app.py
```

Pinned versions and a Cloud sketch are in [DEPLOY.md](DEPLOY.md). The brief page downloads the same note as HTML and as a PDF.

The app reads `data/catalog.json`. It does not need a network connection at runtime. Refresh the snapshot with:

```bash
python scripts/build_catalog.py
```

## What the score is

The Harvester Pressure Index (HPI) is computed in this app. It is not an IUCN index, a population trend, or a harvest volume.

HPI is the sum of two 0–50 components, and only when both exist:

| Component | Input | Scale |
| --- | --- | --- |
| Listing | IUCN category cited on the catalog record | CR 50, EN 40, VU 30, NT 18, LC 8 |
| Record concentration | Share of georeferenced GBIF records in the most-recorded country | share × 50, and only with at least 30 records |

Missing inputs stay unscored. They are not shown as zero.

Risk colors are used for the HPI band only: Lower, Moderate, Higher, Severe.

## What is not invented

IUCN categories are copied only from Wikidata P141 statements that cite a named IUCN Red List version. The reference retrieval date is not an assessment year. If that statement is absent, the catalog says the category is not recorded. That is not an IUCN assessment.

Occurrence counts, decade bars, country shares, coordinates, and English names come from GBIF. A single display name is used only when GBIF marks one name preferred, or when one English name is recorded more often than the others.

## Tests

```bash
python -m unittest tests.test_atlas -v
```
