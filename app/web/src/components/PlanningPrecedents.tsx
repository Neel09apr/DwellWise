import { useState } from "react";

import type { Brief } from "../api/client";
import { nextSort, type SortState, sortRows } from "../sortText";
import { SortHeader, sortMessage } from "./SortHeader";
import { TableRegion } from "./TableRegion";
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
          <ApplicationTable rows={p.recent} />
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

const COLUMNS = [
  { key: "received", label: "Received", type: "text", className: undefined },
  { key: "application_number", label: "Reference", type: "text", className: "wording" },
  { key: "decision", label: "Decision", type: "text", className: "wording" },
  { key: "units_stated", label: "Dwellings", type: "number", className: undefined },
] as const;

type Application = Brief["precedents"]["recent"][number];
const cell = (a: Application, key: (typeof COLUMNS)[number]["key"]) =>
  key === "decision" ? decisionLabel(a.decision, a.decision_class) : a[key];

/** The recent applications, sortable by any column; the first five show until "Show all". */
function ApplicationTable({ rows }: { rows: Brief["precedents"]["recent"] }) {
  const [sort, setSort] = useState<SortState>(null);
  const [all, setAll] = useState(false);
  const column = COLUMNS.find((c) => c.key === sort?.key);
  const sorted = sort && column ? sortRows(rows, (a) => cell(a, column.key), column.type, sort.direction) : rows;
  const shown = all ? sorted : sorted.slice(0, FIRST);
  return (
    <>
      <TableRegion label="Recent residential applications">
        <table className="counts">
          <caption className="sr-only">Recent residential applications in the town</caption>
          <thead>
            <tr>
              {COLUMNS.map((c) => (
                <SortHeader
                  key={c.key}
                  label={c.label}
                  column={c.key}
                  sort={sort}
                  className={c.className}
                  onSort={(k) => setSort((s) => nextSort(s, k))}
                />
              ))}
            </tr>
          </thead>
          <tbody>
            {shown.map((a) => (
              <tr key={`${a.authority}/${a.application_number}`}>
                <th scope="row">{day(a.received)}</th>
                <td className="wording">{a.application_number}</td>
                <td className="wording">{decisionLabel(a.decision, a.decision_class)}</td>
                <td>{a.units_stated || "–"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </TableRegion>
      {rows.length > FIRST && (
        <button type="button" className="show-all" aria-expanded={all} onClick={() => setAll((v) => !v)}>
          {all ? "Show the newest five" : `Show all ${rows.length} applications`}
        </button>
      )}
      <p role="status" className="sr-only">
        {sortMessage(column?.label, sort, shown.length)}
      </p>
    </>
  );
}
