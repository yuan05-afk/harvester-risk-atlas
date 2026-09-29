# Deploy

The atlas is a Streamlit app. It reads the committed catalog in `data/catalog.json` and does not call Wikidata or GBIF at runtime. No API key and no secret is required.

## Local

Python 3.12. From the repository root:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

`requirements.txt` pins Streamlit, Plotly, Folium, streamlit-folium, and reportlab. Reportlab is used only for the field-brief PDF. The HTML download does not need it.

Open the URL Streamlit prints. The workflow is Map, then Dossier, then Brief. Demo mode locks *Aquilaria malaccensis* and compares it with *Boswellia sacra*.

## Streamlit Community Cloud

1. Push the branch you want to serve.
2. In Streamlit Community Cloud, create an app from this repository.
3. Set the main file to `app.py`.
4. Leave secrets empty. The basemap is Esri World Light Gray Canvas, which does not use a key.

The first boot installs the pinned requirements and starts on `app.py`. Rebuild the catalog only when you intend to refresh the snapshot:

```bash
python scripts/build_catalog.py
```

That script needs network access. The running app does not.
