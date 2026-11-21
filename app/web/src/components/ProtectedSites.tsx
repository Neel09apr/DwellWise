import type { Brief } from "../api/client";
import { DESIGNATIONS, distanceLabel } from "./protectedText";

const day = (iso: string) => new Date(iso).toLocaleDateString("en-IE", { dateStyle: "medium" });

/** Brief section 03: SACs, SPAs and NHAs near the town boundary, nearest first (F5). */
export function ProtectedSites({ protected: p }: { protected: Brief["protected"] }) {
  const km = p.radius_m / 1000;
  const touching = p.sites.filter((s) => s.band === "touches").length;
  const near = p.sites.filter((s) => s.band === "1km").length;

  return (
    <div className="section-body">
      {p.sites.length === 0 ? (
        <p>No SAC, SPA or NHA lies within {km} km of the town boundary.</p>
      ) : (
        <>
          <p className="headline">
            <span className="headline-number">{p.sites.length}</span> protected{" "}
            {p.sites.length === 1 ? "site" : "sites"} within {km} km
            <span className="muted">
              {" "}
              · {touching} touching the town · {near} within 1 km
            </span>
          </p>
          <table className="counts">
            <caption className="sr-only">Protected sites near the town, nearest first</caption>
            <thead>
              <tr>
                <th scope="col">Distance</th>
                <th scope="col" className="wording">
                  Site
                </th>
                <th scope="col" className="wording">
                  Designation
                </th>
              </tr>
            </thead>
            <tbody>
              {p.sites.map((s) => (
                <tr key={`${s.designation}/${s.site_code}`}>
                  <th scope="row">{distanceLabel(s.distance_m)}</th>
                  <td className="wording">{s.url ? <a href={s.url}>{s.name}</a> : s.name}</td>
                  <td className="wording">
                    <abbr title={DESIGNATIONS[s.designation]}>{s.designation}</abbr> {s.site_code}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}
      <p className="note">
        Distances run from the town boundary to each site's boundary, simplified to about 10 m. This describes the
        town's surroundings, not any site in it, and is not an Appropriate Assessment screening. Proposed NHAs are not
        included. {p.captured_at && `Captured ${day(p.captured_at)}. `}
        {p.attribution}
      </p>
    </div>
  );
}
