import { api, type Prices } from "../api/client";
import { dayLabel } from "../text";
import { type Resource, useResource } from "../useResource";
import { monthLabel } from "./planningText";
import { areaTitle, price } from "./priceText";
import { Failure, Loading } from "./Status";

const fmt = new Intl.NumberFormat("en-IE");

/** What homes sold for around a town (CSO), fetched here (the brief). Area figures, never a site's value. */
export function SalePrices({ settlement }: { settlement: string }) {
  const data = useResource((signal) => api.prices({ settlement }, signal), settlement);
  return (
    <div className="section-body">
      <Body data={data} />
    </div>
  );
}

/** Sale prices for Ireland or a county, from data the overview fetched. */
export function PriceSection({ data }: { data: Resource<Prices> }) {
  return (
    <section aria-labelledby="prices-title" className="level deferred">
      <h2 id="prices-title" className="level-title">
        Sale prices of homes
      </h2>
      <Body data={data} />
    </section>
  );
}

function Body({ data }: { data: Resource<Prices> }) {
  if (data.kind === "loading") return <Loading what="sale prices" />;
  if (data.kind === "error") return <Failure message={data.message} />;
  const prices = data.data;
  if (prices.areas.length === 0) return <p className="muted">No sale prices are published for this area.</p>;
  return (
    <>
      {prices.areas.map((area) => (
        <div key={`${area.kind}:${area.code}`} className="price-area">
          {prices.areas.length > 1 || area.kind === "eircode" ? (
            <h3 className="price-title">{areaTitle(area)}</h3>
          ) : null}
          {area.latest ? (
            <p className="headline">
              <span className="headline-number">{price(area.latest.median)}</span> median sale price
              <span className="muted">
                {" "}
                · {monthLabel(area.latest.month)}, {fmt.format(area.latest.sales ?? 0)} sales
              </span>
            </p>
          ) : (
            <p className="muted">No median is published for recent months.</p>
          )}
          <dl className="facts">
            <div>
              <dt>New homes</dt>
              <dd>{price(area.latest?.new_median)}</dd>
            </div>
            <div>
              <dt>Sales, 12 months</dt>
              <dd>{fmt.format(area.sales_12_months)}</dd>
            </div>
          </dl>
          <details className="chart-table">
            <summary>Show months</summary>
            <table className="counts">
              <thead>
                <tr>
                  <th scope="col">Month</th>
                  <th scope="col">Sales</th>
                  <th scope="col">Median</th>
                  <th scope="col">New homes</th>
                </tr>
              </thead>
              <tbody>
                {[...area.months].reverse().map((m) => (
                  <tr key={m.month}>
                    <th scope="row">{monthLabel(m.month)}</th>
                    <td>{m.sales == null ? "Not published" : fmt.format(m.sales)}</td>
                    <td>{price(m.median)}</td>
                    <td>{price(m.new_median)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </details>
        </div>
      ))}
      <p className="note">
        {prices.basis} Market purchases by households, by the month the deed was signed; the CSO leaves small counts
        unpublished. These figures describe sales across an area, not the value of any site or home.{" "}
        {prices.captured_at && `Captured ${dayLabel(prices.captured_at)}. `}
        {prices.attribution}
      </p>
    </>
  );
}
