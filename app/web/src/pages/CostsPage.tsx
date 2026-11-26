import { type FormEvent, useState } from "react";
import { useSearchParams } from "react-router-dom";

import { api, type Costs, type Prices } from "../api/client";
import { Board } from "../components/Board";
import { Breadcrumbs } from "../components/Breadcrumbs";
import { areaTitle, price } from "../components/priceText";
import { monthLabel } from "../components/planningText";
import { Failure, Loading } from "../components/Status";
import { type CostForm, costQuery, councilsFor, estimateFigures, loadDraft, saveDraft } from "../costText";
import { titleCase } from "../text";
import { type Resource, useResource } from "../useResource";

const storage = typeof window === "undefined" ? undefined : window.localStorage;

type Field = { key: keyof CostForm; label: string; hint: string; unit?: string };

const FIELDS: Field[] = [
  { key: "homes", label: "Homes", hint: "e.g. 8" },
  { key: "floor_area_m2", label: "Floor area of each home", unit: "m²", hint: "e.g. 110" },
  {
    key: "build_cost_per_m2",
    label: "Build cost",
    unit: "€ per m²",
    hint: "SCSI (Dec 2025): €2,600 to €3,150 per m² for apartments",
  },
  { key: "fees_pct", label: "Professional fees", unit: "% of build", hint: "e.g. 10" },
  { key: "contingency_pct", label: "Contingency", unit: "% of build", hint: "e.g. 5" },
  { key: "finance_rate_pct", label: "Interest", unit: "% a year", hint: "your lender's rate" },
  { key: "finance_months", label: "Borrowed for", unit: "months", hint: "e.g. 18" },
  { key: "land", label: "Land (optional)", unit: "€", hint: "leave empty to leave it out" },
];

/** A cost estimate from the user's own figures: computed by the API, kept in this browser, never a valuation. */
export function CostsPage() {
  const [params] = useSearchParams();
  const county = params.get("county");
  const settlement = params.get("settlement");
  const councils = councilsFor(county);
  const [council, setCouncil] = useState(councils[0].name);
  const [form, setForm] = useState<CostForm>(() => loadDraft(storage));
  const [query, setQuery] = useState<string | null>(null);
  const chosen = councils.find((c) => c.name === council) ?? councils[0];

  const set = (key: keyof CostForm) => (value: string) => setForm((f) => ({ ...f, [key]: value }));
  const submit = (event: FormEvent) => {
    event.preventDefault();
    saveDraft(storage, form);
    setQuery(costQuery(form));
  };

  const estimate = useResource((signal) => (query ? api.costs(query, signal) : Promise.resolve(null)), query ?? "none");
  const ready = estimate.kind === "ready" ? estimate.data : null;

  return (
    <article>
      <Breadcrumbs trail={[{ label: "Ireland", to: "/" }, { label: "Cost estimate" }]} />
      <Board
        title="Cost estimate"
        place="What might a scheme cost? Your figures, worked line by line."
        figures={ready ? estimateFigures(ready) : []}
        foot="Nothing is filled in for you and nothing leaves this browser except the sums. An estimate of building costs, never the value of a site."
        disclaimer={false}
      />

      <form className="notices cost-form" onSubmit={submit}>
        <section aria-labelledby="contributions-title">
          <h2 id="contributions-title">Development contributions</h2>
          <label className="cost-field">
            <span>Council</span>
            <select value={council} onChange={(e) => setCouncil(e.target.value)}>
              {councils.map((c) => (
                <option key={c.name}>{c.name}</option>
              ))}
            </select>
          </label>
          <p className="note">
            Find the current rate in the development contribution scheme on{" "}
            <a href={chosen.url} target="_blank" rel="noreferrer">
              {chosen.name}&rsquo;s website
            </a>
            , with its date, and check whether a waiver applies. Rates are indexed every year.
          </p>
          <label className="cost-field">
            <span>Charge (€)</span>
            <input
              inputMode="decimal"
              value={form.contribution}
              placeholder="from the council's scheme"
              onChange={(e) => set("contribution")(e.target.value)}
            />
          </label>
          <label className="cost-field">
            <span>Charged</span>
            <select
              value={form.contribution_basis}
              onChange={(e) => set("contribution_basis")(e.target.value as CostForm["contribution_basis"])}
            >
              <option value="per_m2">per m² of floor area</option>
              <option value="per_home">per home</option>
            </select>
          </label>
        </section>

        <section aria-labelledby="scheme-title">
          <h2 id="scheme-title">The scheme</h2>
          {FIELDS.map((f) => (
            <label key={f.key} className="cost-field">
              <span>
                {f.label}
                {f.unit ? <span className="muted"> ({f.unit})</span> : null}
              </span>
              <input
                inputMode="decimal"
                value={form[f.key]}
                placeholder={f.hint}
                onChange={(e) => set(f.key)(e.target.value)}
              />
            </label>
          ))}
          <button type="submit" className="cost-submit">
            Work it out
          </button>
          <p className="note">
            Build cost hint: Society of Chartered Surveyors Ireland, The Real Costs of New Apartment Delivery (December
            2025). Professional fees, contingency and finance are your own assumptions.
          </p>
        </section>
      </form>

      {query || settlement ? (
        <div className="notices">
          {query ? (
            <section aria-labelledby="estimate-title">
              <h2 id="estimate-title">Estimate</h2>
              <EstimateBody data={estimate} />
            </section>
          ) : null}
          {settlement ? <AreaPrices settlement={settlement} county={county} /> : null}
        </div>
      ) : null}
    </article>
  );
}

function EstimateBody({ data }: { data: Resource<Costs | null> }) {
  if (data.kind === "loading") return <Loading what="the estimate" />;
  if (data.kind === "error") return <Failure message={data.message} />;
  const costs = data.data;
  if (!costs) return null;
  return (
    <>
      <table className="counts">
        <thead>
          <tr>
            <th scope="col">Item</th>
            <th scope="col" className="cost-working">
              Working
            </th>
            <th scope="col">Euro</th>
          </tr>
        </thead>
        <tbody>
          {costs.lines.map((line) => (
            <tr key={line.item}>
              <th scope="row">{line.item}</th>
              <td className="cost-working">{line.working}</td>
              <td>{price(line.amount)}</td>
            </tr>
          ))}
          <tr>
            <th scope="row">Total</th>
            <td className="cost-working">{costs.homes === 1 ? "1 home" : `${costs.homes} homes`}</td>
            <td>{price(costs.total)}</td>
          </tr>
          <tr>
            <th scope="row">Per home</th>
            <td className="cost-working" />
            <td>{price(costs.per_home)}</td>
          </tr>
        </tbody>
      </table>
      <p className="note">{costs.note}</p>
    </>
  );
}

function AreaPrices({ settlement, county }: { settlement: string; county: string | null }) {
  const data = useResource((signal) => api.prices({ settlement }, signal), settlement);
  return (
    <section aria-labelledby="area-prices-title">
      <h2 id="area-prices-title">What homes sold for nearby</h2>
      <AreaPricesBody data={data} county={county} />
    </section>
  );
}

function AreaPricesBody({ data, county }: { data: Resource<Prices>; county: string | null }) {
  if (data.kind === "loading") return <Loading what="sale prices" />;
  if (data.kind === "error") return <Failure message={data.message} />;
  const area = data.data.areas[0];
  if (!area?.latest) return <p className="muted">No sale prices are published for this area.</p>;
  const latest = area.latest;
  return (
    <>
      <p>
        In {areaTitle(area)}
        {county ? `, County ${titleCase(county)}` : ""}, homes sold in {monthLabel(latest.month)} for a median of{" "}
        {price(latest.median)}
        {latest.new_median != null ? `; new homes ${price(latest.new_median)}` : ""}.
      </p>
      <p className="note">
        {data.data.basis} An area figure from the CSO, set beside your cost per home for comparison; it is not the value
        of any site. {data.data.attribution}
      </p>
    </>
  );
}
