import { api, type CommencementStats } from "../api/client";
import { dayLabel, titleCase } from "../text";
import { useResource } from "../useResource";
import { Failure, Loading } from "./Status";

const fmt = new Intl.NumberFormat("en-IE");

/** Homes whose construction has started, from commencement notices: Ireland, a county or a town. */
export function BuildingNow({ county, settlement }: { county?: string; settlement?: string }) {
  const stats = useResource(
    (signal) => api.commencementStats({ county, settlement }, signal),
    `${county ?? ""}:${settlement ?? ""}`,
  );
  const Heading = settlement ? "h3" : "h2";
  return (
    <section aria-labelledby="building" className={settlement ? "building" : "level"}>
      <Heading id="building" className="level-title">
        Construction started, last 12 months
      </Heading>
      {stats.kind === "loading" && <Loading what="construction starts" />}
      {stats.kind === "error" && <Failure message={stats.message} />}
      {stats.kind === "ready" && <Figures stats={stats.data} inTown={Boolean(settlement)} />}
    </section>
  );
}

function Figures({ stats, inTown }: { stats: CommencementStats; inTown: boolean }) {
  const { totals, last_7_days: week } = stats;
  return (
    <>
      <p className="headline">
        <span className="headline-number">{fmt.format(totals.homes)}</span> homes started
        <span className="muted"> · {fmt.format(week.homes)} in notices received in the past week</span>
      </p>
      <dl className="facts">
        <div>
          <dt>Notices</dt>
          <dd>{fmt.format(totals.notices)}</dd>
        </div>
        <div>
          <dt>Past week</dt>
          <dd>{fmt.format(week.notices)}</dd>
        </div>
        {stats.newest_submitted && (
          <div>
            <dt>Newest notice</dt>
            <dd>{dayLabel(stats.newest_submitted)}</dd>
          </div>
        )}
      </dl>
      {stats.recent_schemes.length > 0 && (
        <table className="counts">
          <caption className="level-title">Newest schemes of five homes or more</caption>
          <thead>
            <tr>
              <th scope="col" className="wording">
                Scheme
              </th>
              {!inTown && (
                <th scope="col" className="wording">
                  Where
                </th>
              )}
              <th scope="col">Homes</th>
              <th scope="col">Start</th>
              <th scope="col">Planning ref.</th>
            </tr>
          </thead>
          <tbody>
            {stats.recent_schemes.map((s) => (
              <tr key={s.notice_number}>
                <th scope="row" className="wording">
                  {s.project_name ?? "Unnamed scheme"}
                </th>
                {!inTown && <td className="wording">{s.settlement ?? titleCase(s.county)}</td>}
                <td>
                  {fmt.format(s.homes)}
                  {s.scheme_homes && s.scheme_homes > s.homes ? ` of ${fmt.format(s.scheme_homes)}` : ""}
                </td>
                <td className="nowrap">{s.commenced ? dayLabel(s.commenced) : "Not given"}</td>
                <td>{s.planning_ref ?? "None given"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      <p className="note">
        A commencement notice is filed with the council before building starts, so some start dates are a few weeks
        ahead. Homes are counted by start date; a scheme built in phases files one notice per phase. Schemes of fewer
        than five homes are counted but never listed.{" "}
        {stats.newest_submitted && `Notices received up to ${dayLabel(stats.newest_submitted)}. `}
        {stats.captured_at && `Captured ${dayLabel(stats.captured_at)}. `}
        {stats.attribution}
      </p>
    </>
  );
}
