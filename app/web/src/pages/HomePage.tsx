import { Link } from "react-router-dom";

import { api } from "../api/client";
import { SettlementSearch } from "../components/SettlementSearch";
import { Failure, Loading } from "../components/Status";
import { countySlug, titleCase } from "../text";
import { useResource } from "../useResource";

export function HomePage() {
  const counties = useResource((signal) => api.counties(signal), "counties");

  return (
    <>
      <section className="intro">
        <p className="eyebrow">Pre-planning brief</p>
        <h1>What the public record says about a town, before the first planning meeting.</h1>
        <p className="lede">
          Wastewater capacity, planning precedents, protected sites and nearby alternatives, gathered from public data
          and kept traceable to its source.
        </p>
      </section>

      <SettlementSearch />

      <section aria-labelledby="browse" className="level">
        <h2 id="browse" className="level-title">
          Browse by county
        </h2>
        {counties.kind === "loading" && <Loading what="counties" />}
        {counties.kind === "error" && <Failure message={counties.message} />}
        {counties.kind === "ready" && (
          <ul className="rows rows-columns">
            {counties.data.map((c) => (
              <li key={c.name}>
                <Link to={`/counties/${countySlug(c.name)}`} className="row">
                  <span>{titleCase(c.name)}</span>
                  <span className="row-meta">{c.settlements}</span>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </section>
    </>
  );
}
