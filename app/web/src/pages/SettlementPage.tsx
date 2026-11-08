import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { api, type SettlementDetail } from "../api/client";
import { titleCase } from "../text";

type State = { kind: "loading" } | { kind: "error"; message: string } | { kind: "ready"; s: SettlementDetail };

/** Brief sections, in the order the design lists them. Each arrives with its data source. */
const SECTIONS = ["Wastewater capacity", "Planning precedents", "Protected sites nearby", "Nearby alternatives"];

export function SettlementPage() {
  const { code = "" } = useParams();
  const [state, setState] = useState<State>({ kind: "loading" });

  useEffect(() => {
    const controller = new AbortController();
    setState({ kind: "loading" });
    api
      .settlement(code, controller.signal)
      .then((s) => setState({ kind: "ready", s }))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setState({ kind: "error", message: error instanceof Error ? error.message : "Could not load." });
      });
    return () => controller.abort();
  }, [code]);

  if (state.kind === "loading") return <p className="muted">Loading…</p>;
  if (state.kind === "error")
    return (
      <div role="alert">
        <p className="error">{state.message}</p>
        <Link to="/">Search again</Link>
      </div>
    );

  const { s } = state;
  return (
    <article className="brief">
      <p className="eyebrow">Pre-planning brief</p>
      <h1>
        {s.name}
        {s.county && `, Co. ${titleCase(s.county)}`}
      </h1>
      <p className="muted">Evidence about the town, not about any particular site in it.</p>

      <dl className="facts">
        <div>
          <dt>Settlement area</dt>
          <dd>{s.area_km2.toFixed(2)} km²</dd>
        </div>
        <div>
          <dt>Location</dt>
          <dd>
            {s.latitude.toFixed(4)}, {s.longitude.toFixed(4)}
          </dd>
        </div>
        <div>
          <dt>CSO settlement code</dt>
          <dd className="mono">{s.code}</dd>
        </div>
      </dl>

      <h2>Brief sections</h2>
      <ul className="sections">
        {SECTIONS.map((name) => (
          <li key={name}>
            <span>{name}</span>
            <span className="muted">Data source not loaded yet</span>
          </li>
        ))}
      </ul>

      <h2>Sources</h2>
      <ul className="sources">
        {s.sources.map((src) => (
          <li key={src.name}>
            {src.attribution} Captured {new Date(src.captured_at).toLocaleDateString("en-IE")}.
          </li>
        ))}
      </ul>
      <p>
        <Link to="/">Search another town</Link>
      </p>
    </article>
  );
}
