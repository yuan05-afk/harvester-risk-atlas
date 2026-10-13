import { Link } from "react-router-dom";
import { HexMap } from "../components/HexMapLazy";
import { Mark } from "../components/Mark";
import { SpecimenLabel } from "../components/SpecimenLabel";
import { WithData } from "../components/Status";
import { useSpeciesList, useValidation } from "../data/api";
import { COMPONENT_META, SCORED_COMPONENTS } from "../lib/vocab";

export function Overview() {
  const list = useSpeciesList();
  const validation = useValidation();
  return (
    <WithData state={list}>
      {(species) => {
        const scored = species.filter((s) => !s.gate);
        const top = scored.filter((s) => s.tier === "High attention").sort((a, b) => (a.rank ?? 0) - (b.rank ?? 0));
        const watch = scored.filter((s) => s.tier === "Watch").length;
        const notScored = species.length - scored.length;
        return (
          <>
            <section className="hero">
              <div className="hero__text">
                <Mark size={56} draw className="hero__mark" />
                <h1 className="display">Which wild medicinal plants need attention first?</h1>
                <p className="lede">
                  The atlas ranks {scored.length} native medicinal plants of the Philippines by how much harm wild
                  harvesting can do to them and how exposed the places they grow are. Every rank comes with how sure we
                  are of it.
                </p>
                <div className="actions">
                  <Link to="/atlas" className="button button--primary">
                    Open the atlas
                  </Link>
                  <Link to="/rankings" className="button">
                    See the full ranking
                  </Link>
                </div>
                <p className="hero__counts">
                  <b className="num">{top.length}</b> need high attention, <b className="num">{watch}</b> are on watch,
                  and <b className="num">{notScored}</b> more are listed but not ranked because they were introduced or
                  have too few records.
                </p>
              </div>
              <figure className="hero__map sheet">
                <HexMap mode="hotspots" interactive={false} showPA={false} label="Map of the Philippines: grid cells shaded by how many high-attention or watch species were recorded there" />
                <figcaption className="hero__legend">
                  <span>Plants on high attention or watch recorded in each area of about 1,770 km²</span>
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
                </figcaption>
              </figure>
            </section>

            <section className="band">
              <div className="band__head">
                <h2>Highest priority on current evidence</h2>
                <p>
                  These {top.length} rank in the top quarter in at least 80% of the 2,000 simulations that vary the
                  weights and resample the evidence.
                </p>
              </div>
              <div className="label-grid">
                {top.map((s) => (
                  <SpecimenLabel key={s.slug} s={s} nScored={scored.length} compact />
                ))}
              </div>
            </section>

            <section className="band">
              <div className="band__head">
                <h2>How a plant is scored</h2>
                <p>Three parts, each from 0 to 1, weighted equally. A missing part is left out, never guessed.</p>
              </div>
              <ol className="parts sheet">
                {SCORED_COMPONENTS.map((k) => (
                  <li key={k} className="parts__item">
                    <span className="parts__swatch" style={{ background: COMPONENT_META[k].color }} aria-hidden="true" />
                    <h3>{COMPONENT_META[k].label}</h3>
                    <p>{COMPONENT_META[k].question}</p>
                  </li>
                ))}
              </ol>
              <p className="band__note">
                Climate change is reported for every plant but not weighted: projected warming is about +1.5 °C for all
                of them, so it does not tell them apart. <Link to="/methods#components">How each part is measured</Link>
              </p>
            </section>

            <section className="band band--split">
              <div>
                <h2>What the atlas cannot tell you</h2>
                <ul className="limits">
                  <li>How much of any plant is actually harvested. No dataset records that; the score uses what can be measured.</li>
                  <li>Whether a species is threatened with extinction. That is the Red List's job, and no category here is invented.</li>
                  <li>Where exactly a plant grows. Locations are shown as grid cells so that plants at risk from collection are not easier to find.</li>
                  <li>Anything medical. Uses are cultural context only.</li>
                </ul>
              </div>
              <WithData state={validation}>
                {(v) => (
                  <div className="sheet checks">
                    <h3>How robust is the ranking?</h3>
                    <dl>
                      <div>
                        <dt>Typical uncertainty</dt>
                        <dd>
                          A species' rank is known to within about <b className="num">{v.interval_width_median}</b> places.
                        </dd>
                      </div>
                      <div>
                        <dt>Change of method</dt>
                        <dd>
                          Ranks barely move under a different way of combining the parts (agreement{" "}
                          <b className="num">{v.aggregation.geometric_mean?.toFixed(2)}</b>).
                        </dd>
                      </div>
                      <div>
                        <dt>National list</dt>
                        <dd>
                          Species on the DENR threatened list rank higher than chance would place them, a weak signal
                          from {v.dao.n_listed} species.
                        </dd>
                      </div>
                    </dl>
                    <Link to="/methods#validation">All checks</Link>
                  </div>
                )}
              </WithData>
            </section>
          </>
        );
      }}
    </WithData>
  );
}
