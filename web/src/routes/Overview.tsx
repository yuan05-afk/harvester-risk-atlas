import { ArrowRight, Map as MapIcon, Search } from "lucide-react";
import { motion } from "motion/react";
import { useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ComponentFigure } from "../components/Figures";
import { HexMap } from "../components/HexMapLazy";
import type { HoverInfo } from "../components/HexMap";
import { MapTooltip } from "../components/MapTooltip";
import { PlantCard } from "../components/PlantCard";
import { SearchPalette } from "../components/SearchPaletteLazy";
import { WithData } from "../components/Status";
import { useSpeciesList } from "../data/api";
import type { SpeciesSummary } from "../data/schema";
import { useWidth } from "../lib/useWidth";
import { COMPONENT_META, SCORED_COMPONENTS } from "../lib/vocab";

const rise = {
  initial: { opacity: 0, y: 18 },
  whileInView: { opacity: 1, y: 0 },
  viewport: { once: true, margin: "-80px" },
  transition: { duration: 0.5, ease: [0.2, 0.7, 0.2, 1] as const },
};

export function Overview() {
  const list = useSpeciesList();
  return <WithData state={list}>{(species) => <OverviewView species={species} />}</WithData>;
}

function OverviewView({ species }: { species: SpeciesSummary[] }) {
  const navigate = useNavigate();
  const [searchOpen, setSearchOpen] = useState(false);
  const [hover, setHover] = useState<HoverInfo>(null);
  const [mapRef, mapW] = useWidth<HTMLDivElement>(600);
  const bySlug = useMemo(() => new Map(species.map((s) => [s.slug, s])), [species]);
  const scored = species.filter((s) => !s.gate);
  const top = scored.filter((s) => s.tier === "High attention").sort((a, b) => (a.rank ?? 0) - (b.rank ?? 0));
  const watch = scored.filter((s) => s.tier === "Watch").length;
  const example = top[0];

  return (
    <div className="overview">
      <section className="hero">
        <div className="hero__text">
          <motion.h1 className="display" {...rise}>
            Which wild medicinal plants need attention <em>first?</em>
          </motion.h1>
          <motion.p className="lede" {...rise} transition={{ ...rise.transition, delay: 0.08 }}>
            Many of the Philippines' healing plants are still gathered from the wild. This atlas shows which are most at
            risk, where they grow, and why, so that harvesters, rangers and researchers know where to look first.
          </motion.p>
          <motion.button
            type="button"
            className="hero-search"
            onClick={() => setSearchOpen(true)}
            {...rise}
            transition={{ ...rise.transition, delay: 0.16 }}
          >
            <Search size={20} aria-hidden="true" />
            <span>Search a plant, for example kalingag or lagundi</span>
            <kbd>/</kbd>
          </motion.button>
          <motion.div className="actions" {...rise} transition={{ ...rise.transition, delay: 0.22 }}>
            <Link to="/atlas" className="button button--primary">
              <MapIcon size={18} aria-hidden="true" /> Explore the map
            </Link>
            <Link to="/plants" className="button">
              See all {scored.length} plants
            </Link>
          </motion.div>
          <motion.dl className="hero__stats" {...rise} transition={{ ...rise.transition, delay: 0.3 }}>
            <div>
              <dt>Need attention now</dt>
              <dd className="num" style={{ color: "var(--tier-high)" }}>
                {top.length}
              </dd>
            </div>
            <div>
              <dt>Keep watch</dt>
              <dd className="num" style={{ color: "var(--tier-watch)" }}>
                {watch}
              </dd>
            </div>
            <div>
              <dt>Plants ranked</dt>
              <dd className="num">{scored.length}</dd>
            </div>
          </motion.dl>
        </div>

        <motion.figure
          className="hero__map"
          ref={mapRef}
          initial={{ opacity: 0, scale: 0.98 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.6, ease: "easeOut" }}
        >
          <HexMap
            mode="hotspots"
            interactive={false}
            onHover={setHover}
            onCellClick={(c) => c && c.n_cohort > 0 && navigate(`/atlas?cell=${c.h3}`)}
            padding={24}
            label="Map of the Philippines. Each hexagon is an area of about 1,770 square kilometres, darker where more priority plants were recorded. The atlas page lists the same areas."
          />
          <MapTooltip info={hover} bySlug={bySlug} mode="hotspots" width={mapW} height={640} />
          <figcaption className="map-legend">
            <span className="map-legend__title">Plants needing attention or watching, per area</span>
            <span className="ramp" aria-hidden="true">
              <i style={{ background: "var(--hot-1)" }} />
              <i style={{ background: "var(--hot-2)" }} />
              <i style={{ background: "var(--hot-3)" }} />
              <i style={{ background: "var(--hot-4)" }} />
            </span>
            <span className="ramp__ends">
              <span>1</span>
              <span>4 or more</span>
            </span>
            <span className="map-legend__hint">Point at an area to see its plants. Tap or click to open it.</span>
          </figcaption>
        </motion.figure>
      </section>

      <section className="band">
        <motion.header className="band__head" {...rise}>
          <h2>Plants that need attention now</h2>
          <p>
            On every check we ran, these {top.length} come out near the top. Open one to see why, and where it grows.
          </p>
        </motion.header>
        <div className="card-grid card-grid--feature">
          {top.map((s, i) => (
            <motion.div key={s.slug} {...rise} transition={{ ...rise.transition, delay: i * 0.06 }}>
              <PlantCard s={s} nScored={scored.length} size="large" />
            </motion.div>
          ))}
        </div>
        <Link to="/plants" className="more-link">
          See all {scored.length} ranked plants <ArrowRight size={16} aria-hidden="true" />
        </Link>
      </section>

      <section className="band">
        <motion.header className="band__head" {...rise}>
          <h2>How we decide</h2>
          <p>Each plant is judged on three things. A plant that does badly on all three rises to the top.</p>
        </motion.header>
        <ol className="plates">
          {SCORED_COMPONENTS.map((k, i) => {
            const meta = COMPONENT_META[k];
            return (
              <motion.li
                key={k}
                className="plate"
                style={{ ["--accent" as string]: meta.color }}
                {...rise}
                transition={{ ...rise.transition, delay: i * 0.08 }}
              >
                <ComponentFigure k={k} color={meta.color} />
                <p className="plate__no">
                  Fig. {i + 1} <span aria-hidden="true">·</span> {meta.short}
                </p>
                <h3 className="plate__title">{meta.label}</h3>
                <p className="plate__text">{meta.question}</p>
              </motion.li>
            );
          })}
        </ol>
        <p className="band__note">
          Climate change is shown on every plant's page but does not change the order: the warming expected by 2050 is
          about the same, +1.5 °C, everywhere these plants grow. <Link to="/how-it-works">How it works</Link>
        </p>
      </section>

      <section className="band">
        <motion.header className="band__head" {...rise}>
          <h2>From the map to the field</h2>
          <p>Four steps, whether you are planning a survey or deciding what to gather.</p>
        </motion.header>
        <ol className="journey">
          {[
            {
              title: "Find a plant",
              text: "Search by its Filipino or scientific name.",
              action: (
                <button type="button" className="link-button" onClick={() => setSearchOpen(true)}>
                  Search now
                </button>
              ),
            },
            {
              title: "See where it grows",
              text: "The atlas shows the areas it was recorded in, and which are protected.",
              action: <Link to="/atlas">Open the atlas</Link>,
            },
            {
              title: "Understand why",
              text: "Each plant's page explains its rank in plain words, with every source.",
              action: example ? <Link to={`/species/${example.slug}`}>See {example.vernacular || example.name}</Link> : null,
            },
            {
              title: "Take a field brief",
              text: "A one-page summary to print or share with your team.",
              action: example ? <Link to={`/species/${example.slug}/brief`}>Example brief</Link> : null,
            },
          ].map((step, i) => (
            <motion.li key={step.title} className="journey__step" {...rise} transition={{ ...rise.transition, delay: i * 0.07 }}>
              <span className="journey__num num" aria-hidden="true">
                {i + 1}
              </span>
              <h3>{step.title}</h3>
              <p>{step.text}</p>
              {step.action}
            </motion.li>
          ))}
        </ol>
      </section>

      <section className="band">
        <motion.header className="band__head" {...rise}>
          <h2>Read this first</h2>
        </motion.header>
        <ul className="caveats">
          {[
            {
              title: "A guide to priorities, not a verdict",
              text: "No dataset records how much of any plant is harvested. The atlas ranks plants on what can be measured, and shows how sure each rank is.",
            },
            {
              title: "Not a Red List",
              text: "Whether a species is threatened with extinction is decided by the IUCN and DENR. Their categories are shown where they exist and never invented.",
            },
            {
              title: "No exact locations",
              text: "Places are shown as areas of about 250 km² or more, so rare plants are not easier to find and take.",
            },
            {
              title: "Not medical advice",
              text: "Traditional uses are cultural context only.",
            },
          ].map((c, i) => (
            <motion.li key={c.title} {...rise} transition={{ ...rise.transition, delay: i * 0.05 }}>
              <span className="caveats__mark" aria-hidden="true">
                {["*", "†", "‡", "§"][i]}
              </span>
              <div>
                <h3>{c.title}</h3>
                <p>{c.text}</p>
              </div>
            </motion.li>
          ))}
        </ul>
      </section>

      <SearchPalette open={searchOpen} onOpenChange={setSearchOpen} />
    </div>
  );
}
