import { Search } from "lucide-react";
import { AnimatePresence, motion } from "motion/react";
import { Suspense, useEffect, useState, type ReactNode } from "react";
import { Link, NavLink, useLocation } from "react-router-dom";
import { useManifest } from "../data/api";
import { fmtDate } from "../lib/format";
import { NavGlyph } from "./Figures";
import { Mark } from "./Mark";
import { replayIntro } from "./Preloader";
import { SearchPalette } from "./SearchPaletteLazy";
import { Loading, PageErrorBoundary } from "./Status";

const NAV = [
  { to: "/", label: "Overview", glyph: "overview", end: true },
  { to: "/atlas", label: "Atlas", glyph: "atlas", end: false },
  { to: "/plants", label: "Plants", glyph: "plants", end: false },
  { to: "/how-it-works", label: "How it works", glyph: "how", end: false },
] as const;

export function Layout({ children, bleed = false }: { children: ReactNode; bleed?: boolean }) {
  const [searchOpen, setSearchOpen] = useState(false);
  const location = useLocation();

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const typing = (e.target as HTMLElement)?.closest("input, textarea, select, [contenteditable]");
      if ((e.key === "k" && (e.metaKey || e.ctrlKey)) || (e.key === "/" && !typing)) {
        e.preventDefault();
        setSearchOpen(true);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  useEffect(() => {
    if (!location.hash) {
      window.scrollTo(0, 0);
      return;
    }
    // Sections render once their data arrives, so wait briefly for the target.
    const id = location.hash.slice(1);
    let tries = 0;
    let timer = 0;
    const seek = () => {
      const el = document.getElementById(id);
      if (el) el.scrollIntoView();
      else if (tries++ < 40) timer = window.setTimeout(seek, 50);
    };
    seek();
    return () => window.clearTimeout(timer);
  }, [location.pathname, location.hash]);

  return (
    <div className={`app${bleed ? " app--bleed" : ""}`}>
      <a className="skip" href="#main">
        Skip to content
      </a>
      <header className="topbar">
        <Link to="/" className="brand" aria-label="Harvester Risk Atlas, overview">
          <Mark size={30} />
          <span className="brand__name">Harvester Risk Atlas</span>
        </Link>
        <nav className="topnav" aria-label="Main">
          {NAV.map((n) => (
            <NavLink key={n.to} to={n.to} end={n.end} className="topnav__link">
              {n.label}
            </NavLink>
          ))}
        </nav>
        <button type="button" className="search-trigger" onClick={() => setSearchOpen(true)} aria-label="Find a plant">
          <Search size={16} aria-hidden="true" />
          <span className="search-trigger__text">Find a plant</span>
          <kbd className="search-trigger__key">/</kbd>
        </button>
      </header>

      <AnimatePresence mode="wait" initial={false}>
        <motion.main
          key={location.pathname}
          id="main"
          tabIndex={-1}
          className="main"
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -6 }}
          transition={{ duration: 0.22, ease: "easeOut" }}
        >
          <PageErrorBoundary resetKey={location.pathname}>
            <Suspense fallback={<Loading />}>{children}</Suspense>
          </PageErrorBoundary>
        </motion.main>
      </AnimatePresence>

      {!bleed && <Footer />}

      <nav className="bottomtabs" aria-label="Main">
        {NAV.map((n) => (
          <NavLink key={n.to} to={n.to} end={n.end} className="bottomtabs__link">
            <NavGlyph name={n.glyph} />
            <span>{n.label}</span>
          </NavLink>
        ))}
      </nav>

      <SearchPalette open={searchOpen} onOpenChange={setSearchOpen} />
    </div>
  );
}

function Footer() {
  const manifest = useManifest();
  return (
    <footer className="footer">
      <div className="footer__inner">
        <div className="footer__brand">
          <Mark size={36} />
          <p>
            <b>Harvester Risk Atlas</b>
            <br />
            Which wild medicinal plants of the Philippines need attention first.
          </p>
        </div>
        <p className="footer__disclaimer">
          For research and education. Not medical advice, not a harvest permit, and not a Red List assessment.
        </p>
        <p className="footer__meta">
          {manifest.status === "ready" ? (
            <>
              {manifest.data.index} v{manifest.data.version}, updated {fmtDate(manifest.data.built_at)}.{" "}
            </>
          ) : null}
          Data from GBIF, the World Checklist of Vascular Plants, WDPCA, Global Forest Watch and WorldClim. Photos
          from iNaturalist observers, and museum herbarium scans where none exist, credited on each plant.
        </p>
        <p className="footer__links">
          <Link to="/how-it-works#sources">Sources and licences</Link>
          <Link to="/how-it-works#built">What was built when</Link>
          <button type="button" className="link-button" onClick={replayIntro}>
            Replay intro
          </button>
        </p>
      </div>
    </footer>
  );
}
