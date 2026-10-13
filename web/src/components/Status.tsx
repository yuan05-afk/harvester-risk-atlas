import { Component, type ErrorInfo, type ReactNode } from "react";
import type { DataError, Loadable } from "../data/api";

export function Loading({ label = "Loading" }: { label?: string }) {
  return (
    <div className="status" role="status" aria-live="polite">
      <span className="status__pulse" aria-hidden="true" />
      {label}…
    </div>
  );
}

export function ErrorView({ error }: { error: DataError }) {
  const what =
    error.kind === "schema"
      ? "This page and its data are from different versions of the atlas. Reload to fetch the latest copy."
      : error.kind === "missing"
        ? "That file is not part of this build."
        : "The data could not be loaded.";
  return (
    <div className="status status--error" role="alert">
      <p className="status__title">{what}</p>
      <p className="status__detail">{error.message}</p>
      <button type="button" className="button" onClick={() => window.location.reload()}>
        Reload
      </button>
    </div>
  );
}

/** Render children once the data is ready; otherwise a loading or error state. */
export function WithData<T>({ state, children }: { state: Loadable<T>; children: (data: T) => ReactNode }) {
  if (state.status === "loading") return <Loading />;
  if (state.status === "error") return <ErrorView error={state.error} />;
  return <>{children(state.data)}</>;
}

/**
 * Catches a page that fails to render, so one broken view shows a way back
 * instead of a blank screen. Reset by changing `resetKey` (the route).
 */
export class PageErrorBoundary extends Component<{ resetKey: string; children: ReactNode }, { error: Error | null }> {
  state = { error: null as Error | null };

  static getDerivedStateFromError(error: Error) {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("Page failed to render", error, info.componentStack);
  }

  componentDidUpdate(prev: { resetKey: string }) {
    if (prev.resetKey !== this.props.resetKey && this.state.error) this.setState({ error: null });
  }

  render() {
    if (!this.state.error) return this.props.children;
    return (
      <div className="status status--error" role="alert">
        <p className="status__title">Something on this page went wrong.</p>
        <p className="status__detail">Reloading usually fixes it. If it does not, start again from the overview.</p>
        <p className="status__actions">
          <button type="button" className="button button--primary" onClick={() => window.location.reload()}>
            Reload
          </button>
          <a className="button" href={import.meta.env.BASE_URL}>
            Go to the overview
          </a>
        </p>
      </div>
    );
  }
}
