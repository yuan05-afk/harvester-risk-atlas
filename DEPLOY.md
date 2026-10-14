# Deploy

## Web app (Vercel)

The atlas is a static site in `web/`, deployed by Vercel from this GitHub repository.

| Setting | Value |
|---|---|
| Project | `harvester-risk-atlas` (Vercel team "Yuan's projects") |
| Root directory | `web` |
| Framework / build / output | Vite / `npm run build` / `dist` |
| Production branch | `main`: every merge redeploys https://harvester-risk-atlas.vercel.app |
| Previews | every other branch and pull request gets a preview URL |

`web/vercel.json` sets the single-page-app fallback (unknown paths without a file extension serve `shell.html`)
and cache headers. The build pre-renders the Overview into `index.html`; see `web/scripts/prerender.mjs`.

`main` is protected: the CI checks `python` and `web` must pass, and force-push and deletion are blocked.
Work on a branch and merge by pull request.

## Old Streamlit app

https://harvester-risk-atlas.streamlit.app/ was the v1 prototype. Its entry point, `app/streamlit_app.py`,
is now a one-screen "moved" page that links to the new atlas. `app/requirements.txt` sits next to it, so
Streamlit Community Cloud installs only Streamlit for it. The v1 code is in git history (tag `v1.1-baseline` and earlier).
