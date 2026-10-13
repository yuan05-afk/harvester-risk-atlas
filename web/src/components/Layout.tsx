import { BookOpen, ListOrdered, Map as MapIcon, Search, Sprout } from "lucide-react";
import { useEffect, useState, type ReactNode } from "react";
import { Link, NavLink, useLocation } from "react-router-dom";
import { useManifest } from "../data/api";
import { fmtDate } from "../lib/format";
import { Mark } from "./Mark";
import { SearchPalette } from "./SearchPalette";

const NAV = [
  { to: "/", label: "Overview", icon: Sprout, end: true },
  { to: "/atlas", label: "Atlas", icon: MapIcon, end: false },
  { to: "/rankings", label: "Rankings", icon: ListOrdered, end: false },
  { to: "/methods", label: "Methods", icon: BookOpen, end: false },
];

export function Layout({ children, bleed = false }: { children: ReactNode; bleed?: boolean }) {
  const [searchOpen, setSearchOpen] = useState(false);
  const location = useLocation();

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const typing = (e.target as HTMLElement)?.closest("input, textarea, [contenteditable]");
      if ((e.key === "k" && (e.metaKey || e.ctrlKey)) || (e.key === "/" && !typing)) {
        e.preventDefault();
        setSearchOpen(true);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  useEffect(() => {
    if (!location.hash) window.scrollTo(0, 0);
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
        <button type="button" className="search-trigger" onClick={() => setSearchOpen(true)}>
          <Search size={16} aria-hidden="true" />
          <span className="search-trigger__text">Find a plant</span>
          <kbd className="search-trigger__key">/</kbd>
        </button>
      </header>

      <main id="main" tabIndex={-1} className="main">
        {children}
      </main>

      {!bleed && <Footer />}

      <nav className="bottomtabs" aria-label="Main">
        {NAV.map((n) => (
          <NavLink key={n.to} to={n.to} end={n.end} className="bottomtabs__link">
            <n.icon size={20} aria-hidden="true" />
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
        <p className="footer__disclaimer">
          Research and education only. Not medical advice, not a harvest permit, not a Red List assessment.
        </p>
        <p className="footer__meta">
          {manifest.status === "ready" ? (
            <>
              {manifest.data.index} v{manifest.data.version}, built {fmtDate(manifest.data.built_at)}.{" "}
            </>
          ) : null}
          Data from GBIF, WCVP, WDPCA, Global Forest Watch and WorldClim.{" "}
          <Link to="/methods#data">Sources and licences</Link>.{" "}
          <Link to="/methods#originality">What was built when</Link>.
        </p>
      </div>
    </footer>
  );
}
