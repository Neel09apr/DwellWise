import { Link, useParams } from "react-router-dom";

import { api } from "../api/client";
import { Breadcrumbs } from "../components/Breadcrumbs";
import { Failure, Loading } from "../components/Status";
import { byFirstLetter, countyFromSlug, titleCase } from "../text";
import { useResource } from "../useResource";

export function CountyPage() {
  const { slug = "" } = useParams();
  const name = titleCase(countyFromSlug(slug));
  const settlements = useResource((signal) => api.countySettlements(countyFromSlug(slug), signal), slug);

  return (
    <>
      <Breadcrumbs trail={[{ label: "Ireland", to: "/" }, { label: name }]} />
      <header className="page-head">
        <p className="eyebrow">County</p>
        <h1>{name}</h1>
        {settlements.kind === "ready" && (
          <p className="muted">
            {settlements.data.length} settlement{settlements.data.length === 1 ? "" : "s"}
          </p>
        )}
      </header>

      {settlements.kind === "loading" && <Loading what="settlements" />}
      {settlements.kind === "error" && <Failure message={settlements.message} />}
      {settlements.kind === "ready" && settlements.data.length === 0 && (
        <p className="muted">No settlements are recorded in this county.</p>
      )}
      {settlements.kind === "ready" &&
        byFirstLetter(settlements.data).map(([letter, items]) => (
          <section key={letter} className="letter" aria-labelledby={`letter-${letter}`}>
            <h2 id={`letter-${letter}`} className="letter-mark">
              {letter}
            </h2>
            <ul className="rows">
              {items.map((s) => (
                <li key={s.code}>
                  <Link to={`/settlements/${encodeURIComponent(s.code)}`} className="row">
                    <span>{s.name}</span>
                    <span className="row-meta" aria-hidden="true">
                      ›
                    </span>
                  </Link>
                </li>
              ))}
            </ul>
          </section>
        ))}
    </>
  );
}
