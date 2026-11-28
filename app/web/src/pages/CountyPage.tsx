import { Link, useParams } from "react-router-dom";

import { api } from "../api/client";
import { Breadcrumbs } from "../components/Breadcrumbs";
import { PlaceOverview } from "../components/PlaceOverview";
import { TownsCompared } from "../components/TownsCompared";
import { Failure, Loading } from "../components/Status";
import { byFirstLetter, countyFromSlug, titleCase } from "../text";
import { useResource } from "../useResource";

const RAIL = [
  { id: "towns", label: "Towns compared" },
  { id: "activity", label: "Planning applications" },
  { id: "building", label: "Construction started" },
  { id: "map-title", label: "Map of schemes" },
  { id: "prices-title", label: "Sale prices" },
  { id: "settlements", label: "Towns A to Z" },
];

export function CountyPage() {
  const { slug = "" } = useParams();
  const name = titleCase(countyFromSlug(slug));
  const settlements = useResource((signal) => api.countySettlements(countyFromSlug(slug), signal), slug);

  return (
    <>
      <Breadcrumbs trail={[{ label: "Ireland", to: "/" }, { label: name }]} />
      <PlaceOverview
        county={countyFromSlug(slug)}
        title={name}
        place={
          settlements.kind === "ready"
            ? `County ${name} · ${settlements.data.length} town${settlements.data.length === 1 ? "" : "s"}`
            : `County ${name}`
        }
        rail={RAIL}
        lead={<TownsCompared county={countyFromSlug(slug)} />}
        after={
          <section aria-labelledby="settlements" className="level deferred">
            <h2 id="settlements" className="level-title">
              Towns A to Z
            </h2>
            {settlements.kind === "loading" && <Loading what="settlements" />}
            {settlements.kind === "error" && <Failure message={settlements.message} />}
            {settlements.kind === "ready" && settlements.data.length === 0 && (
              <p className="muted">No towns are recorded in this county.</p>
            )}
            {settlements.kind === "ready" &&
              byFirstLetter(settlements.data).map(([letter, items]) => (
                <section key={letter} className="letter" aria-labelledby={`letter-${letter}`}>
                  <h3 id={`letter-${letter}`} className="letter-mark">
                    {letter}
                  </h3>
                  <ul className="rows">
                    {items.map((s) => (
                      <li key={s.code}>
                        <Link to={`/settlements/${encodeURIComponent(s.code)}`} className="row">
                          <span>{s.name}</span>
                        </Link>
                      </li>
                    ))}
                  </ul>
                </section>
              ))}
          </section>
        }
      />
    </>
  );
}
