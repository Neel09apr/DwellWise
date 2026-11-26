import { useState } from "react";

import { api } from "../api/client";
import { useResource } from "../useResource";
import { ShortlistTable } from "./ShortlistTable";
import { Failure, Loading } from "./Status";

const SORTS = [
  { value: "started", label: "Homes started" },
  { value: "granted", label: "Applications granted" },
  { value: "protected", label: "Fewest protected sites" },
  { value: "price", label: "Lowest sale price" },
] as const;

/** A county's top five towns side by side, ranked by code on one stated column. Works with the assistant off. */
export function TownsCompared({ county }: { county: string }) {
  const [sort, setSort] = useState<string>("started");
  const list = useResource((s) => api.shortlist(county, sort, s), `${county}:${sort}`);
  return (
    <section aria-labelledby="towns" className="level">
      <div className="activity-head">
        <h2 id="towns" className="level-title">
          Towns compared
        </h2>
        <label className="toggle">
          Sort by{" "}
          <select value={sort} onChange={(e) => setSort(e.target.value)}>
            {SORTS.map((s) => (
              <option key={s.value} value={s.value}>
                {s.label}
              </option>
            ))}
          </select>
        </label>
      </div>
      {list.kind === "loading" && <Loading what="the towns" />}
      {list.kind === "error" && <Failure message={list.message} />}
      {list.kind === "ready" && <ShortlistTable shortlist={list.data} />}
    </section>
  );
}
