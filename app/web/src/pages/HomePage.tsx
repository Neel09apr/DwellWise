import { Link } from "react-router-dom";

import { api } from "../api/client";
import { AskBox } from "../components/AskBox";
import { PlaceOverview } from "../components/PlaceOverview";
import { SettlementSearch } from "../components/SettlementSearch";
import { Failure, Loading } from "../components/Status";
import { countySlug, titleCase } from "../text";
import { useResource } from "../useResource";

const RAIL = [
  { id: "find", label: "Find a town" },
  { id: "activity", label: "Planning applications" },
  { id: "building", label: "Construction started" },
  { id: "map-title", label: "Map of schemes" },
  { id: "prices-title", label: "Sale prices" },
  { id: "browse", label: "Counties" },
];

export function HomePage() {
  const counties = useResource((signal) => api.counties(signal), "counties");
  const towns = counties.kind === "ready" ? counties.data.reduce((n, c) => n + c.settlements, 0) : null;

  return (
    <PlaceOverview
      title="Ireland"
      place={
        <>
          Every town's public record, before the first planning meeting
          {counties.kind === "ready" && towns !== null && ` · ${counties.data.length} counties, ${towns.toLocaleString("en-IE")} towns`}
        </>
      }
      rail={RAIL}
      lead={
        <>
          <section aria-labelledby="find" className="level find notice-half">
            <h2 id="find" className="level-title">
              Find a town
            </h2>
            <p className="notice-about">
              Each town&rsquo;s brief: its planning precedents, construction starts, protected sites nearby and sale
              prices, every figure with its source and capture date.
            </p>
            <SettlementSearch />
          </section>
          <AskBox place="Ireland" />
        </>
      }
      after={
        <section aria-labelledby="browse" className="level deferred">
          <h2 id="browse" className="level-title">
            Counties
          </h2>
          {counties.kind === "loading" && <Loading what="counties" />}
          {counties.kind === "error" && <Failure message={counties.message} />}
          {counties.kind === "ready" && (
            <ul className="rows rows-columns">
              {counties.data.map((c) => (
                <li key={c.name}>
                  <Link to={`/counties/${countySlug(c.name)}`} className="row">
                    <span>{titleCase(c.name)}</span>
                    <span className="row-meta">{c.settlements} towns</span>
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </section>
      }
    />
  );
}
