# QA notes

Checked 29 Sep 2026 against a local Streamlit run (`streamlit run app.py`) and `python -m unittest tests.test_atlas`.

## Before

The repository was a placeholder README. There was no app, no chart, no map, and no demo path. These notes record what that gap looked like and what the first usable build got wrong before it was corrected.

## After

Track 3 workflow is Map → Dossier → Brief. Demo mode keeps *Aquilaria malaccensis* selected and compares it with *Boswellia sacra*. The atlas reads `data/catalog.json` and does not need a network connection to run.

## Issues found and fixed

| Issue | What was wrong | Fix |
| --- | --- | --- |
| No interface | Placeholder only | Map, dossier, and brief, with hairline cards and a forest accent |
| Workflow control clipped | A segmented control in the sidebar cut “Brief” off | Full-width Map, Dossier, and Brief buttons |
| Retrieval date truncated | Wikidata times were sliced to `+2023-01-0` | Stored as real dates, e.g. `2023-01-02`. That date is when the statement was retrieved, not an assessment year |
| Partial score looked finished | *Aquilaria crassna* has 21 georeferenced records | Listing is shown. Record concentration and HPI stay unscored. The brief does not quote a country share for an unscored species |
| Missing IUCN category | *Panax quinquefolius* and *Boswellia papyrifera* have no P141 statement in this snapshot | Shown as “Not recorded”. HPI is not scored. Copy says this is not an IUCN assessment |
| Metric row collided with the cohort | Three metrics in the narrow map column wrapped into each other | The map card uses one score line. The full metric row stays on the dossier, where there is width |
| Chart labels crowded the plot | Plotly’s left margin was 8px, and “Record concentration” collided with neighboring labels | Shorter axis labels (“Concentration”), automatic margins, HPI axis held at 0–112 so the total label sits inside the plot |
| Empty search still drew a cohort | A nonsense query left a chart frame up | “No species match” and “No cohort to draw”. The selected species stays selected and is marked hidden |
| Name column repeated the Latin name | Species with no single GBIF name showed the scientific name twice | Lists use one recorded English name when GBIF has one (*Agarwood*), and “—” when it has none (*Aquilaria crassna*). The dossier still says when no name is preferred |
| Stale catalog in a long-running server | The first load stayed cached after the snapshot was corrected | The file is reread when its modification time changes |
| Compare legend casing | “frankincense” rendered as stored | Display labels capitalize a fully lowercase vernacular |
| Compare chart title on the legend | “Component comparison” sat on the species legend, and a later pass still left the green swatch on that word | The heading is outside the figure. Every Plotly legend is horizontal, on paper coordinates, at y=−0.28 under the axes. Compare categories are on the Y axis so “Listing” and “Concentration” stay whole |
| Right compare card showed markup | An indented multiline HTML string was read as a Markdown code fence | Both cards use the same dedented HTML, and no line is indented |
| Long binomials broke mid-word | A narrow card could split a name into pieces such as “ARCANGELISI” / “A FLAVA” | Genus and epithet stay whole words, in italics, with no uppercase transform |

## Smoke

- Map: Esri Light Gray Canvas, cluster counts in a neutral ink circle, legend under the map (Lower, Moderate, Higher, Severe, Not scored). Marker color is the HPI band only.
- Dossier, demo species: HPI 70, Higher, IUCN CR from The IUCN Red List of Threatened Species 2022.2, taxon 32056. Waterfall is listing 50, concentration 20, total 70. Decade bars are GBIF record counts. 26 records dated before 1950 are called out in the caption, not dropped silently.
- Dossier, partial: *Aquilaria crassna* is CR and “Not scored”.
- Brief: agarwood (70, Higher) beside frankincense (49, Moderate). Component bars stay forest and stone. Risk color stays on the HPI figures.
- Empty search `zzzz-not-a-species`: empty copy, no fake cohort.
- Unit tests cover sourced IUCN fields, the “do not fill a missing category” rule, chart colors, the Esri basemap, and an AppTest pass over Map, Dossier, Brief, demo mode, and the empty filter.

## Not claimed

HPI is an in-app sum. It is not an IUCN category, a population trend, or a harvest volume. Country share is a pattern in georeferenced GBIF records. No IUCN category was typed in by hand.
