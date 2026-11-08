import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { api, type SettlementSummary } from "../api/client";
import { titleCase } from "../text";

type State =
  | { kind: "idle" }
  | { kind: "loading" }
  | { kind: "error"; message: string }
  | { kind: "ready"; results: SettlementSummary[] };

const DEBOUNCE_MS = 250;

export function SearchPage() {
  const [query, setQuery] = useState("");
  const [state, setState] = useState<State>({ kind: "idle" });

  useEffect(() => {
    const term = query.trim();
    if (term.length < 2) {
      setState({ kind: "idle" });
      return;
    }
    const controller = new AbortController();
    const timer = setTimeout(() => {
      setState({ kind: "loading" });
      api
        .searchSettlements(term, controller.signal)
        .then((results) => setState({ kind: "ready", results }))
        .catch((error: unknown) => {
          if (error instanceof DOMException && error.name === "AbortError") return;
          setState({ kind: "error", message: error instanceof Error ? error.message : "Search failed." });
        });
    }, DEBOUNCE_MS);
    return () => {
      clearTimeout(timer);
      controller.abort();
    };
  }, [query]);

  return (
    <section className="search">
      <p className="eyebrow">Pre-planning brief</p>
      <h1>Which town is the housing proposal in?</h1>
      <label htmlFor="town">Town or village</label>
      <input
        id="town"
        type="search"
        autoComplete="off"
        placeholder="e.g. Castlebar"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
      />
      <div aria-live="polite">
        {state.kind === "loading" && <p className="muted">Searching…</p>}
        {state.kind === "error" && (
          <p className="error" role="alert">
            {state.message}
          </p>
        )}
        {state.kind === "ready" && state.results.length === 0 && (
          <p className="muted">No settlement matches “{query.trim()}”.</p>
        )}
      </div>
      {state.kind === "ready" && state.results.length > 0 && (
        <ul className="results">
          {state.results.map((s) => (
            <li key={s.code}>
              <Link to={`/settlements/${encodeURIComponent(s.code)}`}>
                <span className="result-name">{s.name}</span>
                {s.county && <span className="muted">Co. {titleCase(s.county)}</span>}
              </Link>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
