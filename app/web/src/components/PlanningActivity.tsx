import { useState } from "react";
import { Link } from "react-router-dom";

import type { ApplicationStats } from "../api/client";
import { countySlug, dayLabel, titleCase } from "../text";
import { nextSort, type SortState, sortRows } from "../sortText";
import type { Resource } from "../useResource";
import { decidedShare, monthLabel } from "./planningText";
import { SortHeader, sortMessage } from "./SortHeader";
import { Failure, Loading } from "./Status";
import { TableRegion } from "./TableRegion";

const FIGURES = [
  { key: "granted", label: "Granted" },
  { key: "refused", label: "Refused" },
  { key: "pending", label: "Pending" },
  { key: "withdrawn", label: "Withdrawn" },
  { key: "other", label: "Other" },
] as const;

const fmt = new Intl.NumberFormat("en-IE");

type Props = {
  stats: Resource<ApplicationStats>;
  national: boolean;
  residential: boolean;
  onResidential: (residential: boolean) => void;
};

/** Planning applications for Ireland, or one county: figures, a monthly chart, and (for Ireland) each county. */
export function PlanningActivity({ stats, national, residential, onResidential }: Props) {
  return (
    <section aria-labelledby="activity" className="level activity">
      <div className="activity-head">
        <h2 id="activity" className="level-title">
          Planning applications, last 12 months
        </h2>
        <label className="toggle">
          <input type="checkbox" checked={residential} onChange={(e) => onResidential(e.target.checked)} />
          Residential only
        </label>
      </div>
      {stats.kind === "loading" && <Loading what="planning applications" />}
      {stats.kind === "error" && <Failure message={stats.message} />}
      {stats.kind === "ready" && <Figures stats={stats.data} national={national} />}
    </section>
  );
}

function Figures({ stats, national }: { stats: ApplicationStats; national: boolean }) {
  const { totals } = stats;
  const share = decidedShare(totals.granted, totals.refused);
  return (
    <>
      <p className="headline">
        <span className="headline-number">{fmt.format(totals.total)}</span>
        {stats.residential ? " residential applications" : " applications"} received
        {share !== null && <span className="muted"> · {share}% of decided ones granted</span>}
      </p>
      <dl className="facts">
        {FIGURES.map((f) => (
          <div key={f.key}>
            <dt>{f.label}</dt>
            <dd>{fmt.format(totals[f.key])}</dd>
          </div>
        ))}
      </dl>
      <MonthChart months={stats.months} />
      {national && <CountyTable counties={stats.counties} />}
      <p className="note">
        Counted by the month received and the decision as it stands now; the current month, hatched, is still filling
        in. “Other” covers invalid, exempt and split decisions.{" "}
        {stats.residential && "Residential means the application states new dwellings. "}
        {stats.newest_received &&
          `The national dataset runs to ${dayLabel(stats.newest_received)}: councils publish with a delay. `}
        {stats.captured_at && `Captured ${dayLabel(stats.captured_at)}. `}
        {stats.attribution}
      </p>
    </>
  );
}

const W = 640;
const H = 160;
const GAP = 2;

function MonthChart({ months }: { months: ApplicationStats["months"] }) {
  const max = Math.max(1, ...months.map((m) => m.total));
  const current = new Date().toISOString().slice(0, 7);
  const slot = W / months.length;
  return (
    <figure className="chart">
      <svg viewBox={`0 0 ${W} ${H + 22}`} role="img" aria-label="Applications received per month">
        <defs>
          {/* The month still filling in is hatched: a mark, not a paler colour. */}
          <pattern id="partial-month" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
            <line x1="0" y1="0" x2="0" y2="6" stroke="currentColor" strokeWidth="2" />
          </pattern>
        </defs>
        <line x1="0" x2={W} y1={H} y2={H} className="chart-axis" />
        {months.map((m, i) => {
          const h = Math.max((m.total / max) * (H - 18), m.total ? 2 : 0);
          const x = i * slot + GAP / 2;
          return (
            <g key={m.month} className={m.month === current ? "chart-bar chart-bar-partial" : "chart-bar"}>
              <rect x={i * slot} y="0" width={slot} height={H} className="chart-hit">
                <title>{`${monthLabel(m.month)}${m.month === current ? " so far" : ""}: ${fmt.format(m.total)} received, ${fmt.format(m.granted)} granted`}</title>
              </rect>
              <path d={bar(x, H, slot - GAP, h)} />
              {(months.length - 1 - i) % 3 === 0 && ( // every third month, counted back from the latest
                <text
                  x={i === months.length - 1 ? W : i * slot + slot / 2}
                  y={H + 16}
                  textAnchor={i === months.length - 1 ? "end" : "middle"}
                  className="chart-label"
                >
                  {monthLabel(m.month)}
                </text>
              )}
            </g>
          );
        })}
        <text x="0" y="10" className="chart-label">
          {fmt.format(max)}
        </text>
      </svg>
      <details className="chart-table">
        <summary>Show as a table</summary>
        <table>
          <thead>
            <tr>
              <th scope="col">Month</th>
              <th scope="col">Received</th>
              <th scope="col">Granted</th>
              <th scope="col">Refused</th>
            </tr>
          </thead>
          <tbody>
            {months.map((m) => (
              <tr key={m.month}>
                <th scope="row">{monthLabel(m.month)}</th>
                <td>{fmt.format(m.total)}</td>
                <td>{fmt.format(m.granted)}</td>
                <td>{fmt.format(m.refused)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </details>
    </figure>
  );
}

/** A bar with 4px rounded top corners, square at the baseline. */
function bar(x: number, base: number, w: number, h: number): string {
  if (h <= 0) return "";
  const r = Math.min(4, w / 2, h);
  return `M${x},${base}V${base - h + r}Q${x},${base - h} ${x + r},${base - h}H${x + w - r}Q${x + w},${base - h} ${x + w},${base - h + r}V${base}Z`;
}

const COUNTY_COLUMNS = [
  { key: "county", label: "County", type: "text" },
  { key: "total", label: "Received", type: "number" },
  { key: "granted", label: "Granted", type: "number" },
  { key: "refused", label: "Refused", type: "number" },
  { key: "pending", label: "Pending", type: "number" },
] as const;

type CountyRow = ApplicationStats["counties"][number];

function CountyTable({ counties }: { counties: ApplicationStats["counties"] }) {
  const [sort, setSort] = useState<SortState>(null);
  const column = COUNTY_COLUMNS.find((c) => c.key === sort?.key);
  const rows =
    sort && column ? sortRows(counties, (c: CountyRow) => c[column.key], column.type, sort.direction) : counties;
  return (
    <details className="chart-table">
      <summary>Show each county</summary>
      <TableRegion label="Planning applications by county">
        <table className="counts">
          <caption className="sr-only">Planning applications by county, last 12 months</caption>
          <thead>
            <tr>
              {COUNTY_COLUMNS.map((c) => (
                <SortHeader
                  key={c.key}
                  label={c.label}
                  column={c.key}
                  sort={sort}
                  onSort={(k) => setSort((s) => nextSort(s, k))}
                />
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((c) => (
              <tr key={c.county}>
                <th scope="row">
                  <Link to={`/counties/${countySlug(c.county)}`}>{titleCase(c.county)}</Link>
                </th>
                <td>{fmt.format(c.total)}</td>
                <td>{fmt.format(c.granted)}</td>
                <td>{fmt.format(c.refused)}</td>
                <td>{fmt.format(c.pending)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </TableRegion>
      <p role="status" className="sr-only">
        {sortMessage(column?.label, sort, rows.length)}
      </p>
    </details>
  );
}
