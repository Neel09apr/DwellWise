import { Link } from "react-router-dom";

import type { Shortlist } from "../api/client";
import { price } from "./priceText";
import { TableRegion } from "./TableRegion";

/** The code-ranked table the answer explains: its order and links never come from the model's words. */
export function ShortlistTable({ shortlist }: { shortlist: Shortlist }) {
  const county = shortlist.county.charAt(0) + shortlist.county.slice(1).toLowerCase();
  return (
    <div className="ask-shortlist">
      <TableRegion label={`Towns in ${county} compared`}>
        <table className="counts">
          <caption className="table-caption">
            Top {shortlist.towns.length} of {shortlist.towns_in_county} towns in {county}, by {shortlist.sorted_by}.
          </caption>
          <thead>
            <tr>
              <th scope="col">Town</th>
              <th scope="col">Homes started</th>
              <th scope="col">Granted</th>
              <th scope="col">Refused</th>
              <th scope="col">Pending</th>
              <th scope="col">Protected sites ≤ 1 km</th>
              <th scope="col">Median sale price</th>
            </tr>
          </thead>
          <tbody>
            {shortlist.towns.map((t) => (
              <tr key={t.code}>
                <th scope="row">
                  <Link to={`/settlements/${encodeURIComponent(t.code)}`}>{t.name}</Link>
                </th>
                <td>{t.homes_started}</td>
                <td>{t.granted}</td>
                <td>{t.refused}</td>
                <td>{t.pending}</td>
                <td>{t.protected_within_1km}</td>
                <td>{t.median_price == null ? "No area" : `${price(t.median_price)} (${t.price_area})`}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </TableRegion>
      <p className="note">
        Homes started since {shortlist.started_since}; residential applications since {shortlist.applications_since}.{" "}
        {shortlist.note}
      </p>
    </div>
  );
}
