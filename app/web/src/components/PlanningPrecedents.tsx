import type { Brief } from "../api/client";
import { decidedShare, decisionLabel } from "./planningText";
import { dayLabel } from "../text";

const FIGURES = [
  { key: "granted", label: "Granted" },
  { key: "refused", label: "Refused" },
  { key: "pending", label: "Pending" },
  { key: "withdrawn", label: "Withdrawn" },
  { key: "other", label: "Other" },
] as const;

const fmt = new Intl.NumberFormat("en-IE");
const day = dayLabel;
const FIRST = 5; // applications shown before "Show all"

/** Brief section 02: recent residential planning applications in the town (F4). */
export function PlanningPrecedents({ precedents: p }: { precedents: Brief["precedents"] }) {
  const share = decidedShare(p.residential.granted, p.residential.refused);
  const since = day(p.since);

  return (
    <div className="section-body">
      {p.residential.total === 0 ? (
        <p>
          No residential applications were received within the town boundary since {since} (
          {fmt.format(p.all_applications)} of any kind).
        </p>
      ) : (
        <>
          <p className="headline">
            <span className="headline-number">{fmt.format(p.residential.total)}</span> residential applications since{" "}
            {since}
            {share !== null && <span className="muted"> · {share}% of decided ones granted</span>}
          </p>
          <dl className="facts">
            {FIGURES.map((f) => (
              <div key={f.key}>
                <dt>{f.label}</dt>
                <dd>{fmt.format(p.residential[f.key])}</dd>
              </div>
            ))}
          </dl>
          <ApplicationTable rows={p.recent.slice(0, FIRST)} caption="Most recent residential applications" />
          {p.recent.length > FIRST && (
            <details className="chart-table">
              <summary>Show all {p.recent.length} applications</summary>
              <ApplicationTable rows={p.recent.slice(FIRST)} caption="Older residential applications" />
            </details>
          )}
        </>
      )}
      <p className="note">
        Applications received within the town boundary since {since} that state new dwellings, out of{" "}
        {fmt.format(p.all_applications)} applications of any kind. They are counted as applications, not schemes: one
        scheme can be filed more than once. This describes the town, not any site in it, and says nothing about how a
        future application would be decided. Decisions are the council's own wording; pending ones may change.{" "}
        {p.captured_at && `Captured ${day(p.captured_at)}. `}
        {p.attribution}
      </p>
    </div>
  );
}

function ApplicationTable({ rows, caption }: { rows: Brief["precedents"]["recent"]; caption: string }) {
  return (
    <table className="counts">
      <caption className="sr-only">{caption}</caption>
      <thead>
        <tr>
          <th scope="col">Received</th>
          <th scope="col" className="wording">
            Reference
          </th>
          <th scope="col" className="wording">
            Decision
          </th>
          <th scope="col">Dwellings</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((a) => (
          <tr key={`${a.authority}/${a.application_number}`}>
            <th scope="row">{day(a.received)}</th>
            <td className="wording">{a.application_number}</td>
            <td className="wording">{decisionLabel(a.decision, a.decision_class)}</td>
            <td>{a.units_stated || "–"}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
