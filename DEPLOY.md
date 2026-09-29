# Deploy

Streamlit Community Cloud serves this app from **`app/streamlit_app.py`** on `main`.

https://harvester-risk-atlas.streamlit.app/

## Streamlit Cloud

1. Keep the GitHub repository **private**. Community Cloud can deploy a private repo when the GitHub account that owns the app is connected.
2. App settings:
   - Repository: `yuan05-afk/harvester-risk-atlas`
   - Branch: `main`
   - Main file path: `app/streamlit_app.py`
   - Python: 3.11 or newer
3. Dependencies come from `requirements.txt` at the repo root. That file includes `reportlab`, which the field-brief PDF download uses.
4. Optional secret, not required for the shipped demo: `IUCN_API_TOKEN`. Without it the badge stays **Not recorded**. Categories are never filled in.
5. A push to `main` is what Cloud rebuilds. If the live app stays on an older commit, reboot it from the app dashboard.

There is no root `app.py`. Do not point Cloud at one.

## Local

```bash
pip install -r requirements.txt
pip install -e .
streamlit run app/streamlit_app.py
```

`scripts/run_app.sh` starts the same file.
