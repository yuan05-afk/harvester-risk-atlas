/**
 * Build-time renderer for the Overview (see scripts/prerender.mjs). The data is
 * handed in with prime(), so the page renders complete, not as a loading state.
 */
import { renderToString } from "react-dom/server";
import { StaticRouter } from "react-router-dom";
import { AppRoutes, BASENAME } from "./App";
import { prime } from "./data/api";

export function render(url: string, data: Record<string, unknown>): string {
  for (const [path, value] of Object.entries(data)) prime(path, value);
  return renderToString(
    <StaticRouter location={url} basename={BASENAME}>
      <AppRoutes />
    </StaticRouter>,
  );
}
