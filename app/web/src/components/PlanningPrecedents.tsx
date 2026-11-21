import { api, type Brief } from "../api/client";
import { useResource } from "../useResource";
import { decidedShare, decisionLabel } from "./planningText";
import { Failure, Loading } from "./Status";

const FIGURES = [
  { key: "granted", label: "Granted" },
  { key: "refused", label: "Refused" },
  { key: "pending", label: "Pending" },
  { key: "withdrawn", label: "Withdrawn" },
  { key: "other", label: "Other" },
] as const;

const fmt = new Intl.NumberFormat("en-IE");
const day = (iso: string) => new Date(iso).toLocaleDateString("en-IE", { dateStyle: "medium" });

/** Brief section 02: recent residential planning applications in the town (F4). */
export function PlanningPrecedents({ code }: { code: string }) {
  const brief = useResource((signal) => api.brief(code, signal), code);

  if (brief.kind === "loading") return <Loading what="planning applications" />;
  if (brief.kind === "error") return <Failure message={brief.message} />;
  return <Precedents precedents={brief.data.precedents} />;
}

function Precedents({ precedents: p }: { precedents: Brief["precedents"] }) {
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
          <table className="counts">
            <caption className="sr-only">Most recent residential applications</caption>
            <thead>
              <tr>
                <th scope="col">Received</th>
                <th scope="col" className="wording">Reference</th>
                <th scope="col" className="wording">Decision</th>
                <th scope="col">Dwellings</th>
              </tr>
            </thead>
            <tbody>
              {p.recent.map((a) => (
                <tr key={`${a.authority}/${a.application_number}`}>
                  <th scope="row">{day(a.received)}</th>
                  <td className="wording">{a.application_number}</td>
                  <td className="wording">{decisionLabel(a.decision, a.decision_class)}</td>
                  <td>{a.units_stated || "–"}</td>
                </tr>
              ))}
            </tbody>
          </table>
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
