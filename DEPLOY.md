# Deploy

## Web app (Vercel)

The atlas is a static site in `web/`. Its public source repository is https://github.com/yuan05-afk/harvester-risk-atlas.

| Setting | Value |
|---|---|
| Project | `harvester-risk-atlas` (Vercel team "Yuan's projects") |
| Root directory | `web` |
| Framework / build / output | Vite / `npm run build` / `dist` |
| Production branch | `main`: every merge redeploys https://harvester-risk-atlas.vercel.app |
| Previews | every other branch and pull request gets a preview URL |

`web/vercel.json` sets the single-page-app fallback (unknown paths without a file extension serve `shell.html`)
and cache headers. The build pre-renders the Overview into `index.html`; see `web/scripts/prerender.mjs`.

CI runs the `python` and `web` checks on pushes and pull requests. Work on a branch and review the checks before merging. Verify the current GitHub branch-protection settings before relying on enforced checks.

For a production deployment from the repository root, use `vercel --prod --yes` after verifying the linked project. `.vercelignore` excludes Python inputs, local environments and test artifacts from CLI uploads; the web app uses the exported files in `web/public/`.

## Streamlit landing page

`app/streamlit_app.py` displays a one-screen landing page linking to the web atlas.
`app/requirements.txt` sits next to it so Streamlit Community Cloud installs only Streamlit for this page.
