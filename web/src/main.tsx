import "@fontsource-variable/atkinson-hyperlegible-next/wght.css";
import "@fontsource-variable/atkinson-hyperlegible-next/wght-italic.css";
import "@fontsource-variable/fraunces/opsz.css";
import "@fontsource-variable/fraunces/opsz-italic.css";
import { StrictMode } from "react";
import { createRoot, hydrateRoot } from "react-dom/client";
import { App } from "./App";
import { load } from "./data/api";
import "./styles/tokens.css";
import "./styles/app.css";

const root = document.getElementById("root")!;

/**
 * index.html carries a pre-rendered Overview. Fetch the data that page shows,
 * then hydrate it: the nodes already on screen are kept, not replaced.
 * Every other path is served the empty shell (shell.html) and renders as usual.
 */
async function start() {
  const home = root.dataset.prerendered !== undefined && location.pathname === import.meta.env.BASE_URL;
  const app = (
    <StrictMode>
      <App />
    </StrictMode>
  );
  if (home) {
    const data = await Promise.allSettled([load("species.json", "speciesList"), load("manifest.json", "manifest")]);
    // Hydrate, keeping the painted nodes; if the data failed, render afresh to show the error state.
    if (data.every((d) => d.status === "fulfilled")) {
      hydrateRoot(root, app, {
        onRecoverableError: (error) => console.warn("Pre-rendered Overview did not match; re-rendered.", error),
      });
      return;
    }
  }
  createRoot(root).render(app);
}

void start();
