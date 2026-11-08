import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { api, type SettlementSummary } from "../api/client";
import { titleCase } from "../text";
import { Failure } from "./Status";

type State =
  | { kind: "idle" }
  | { kind: "loading" }
  | { kind: "error"; message: string }
  | { kind: "ready"; results: SettlementSummary[] };

const DEBOUNCE_MS = 250;

export function SettlementSearch() {
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
    <div className="search" role="search">
      <label htmlFor="town" className="search-label">
        Find a town or village
      </label>
      <input
        id="town"
        type="search"
        autoComplete="off"
        spellCheck={false}
        placeholder="Castlebar, Athy, Kenmare…"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
      />
      <div aria-live="polite" className="search-status">
        {state.kind === "loading" && <span className="muted">Searching…</span>}
        {state.kind === "ready" && state.results.length === 0 && (
          <span className="muted">No settlement matches “{query.trim()}”.</span>
        )}
        {state.kind === "ready" && state.results.length > 0 && (
          <span className="sr-only">{state.results.length} results</span>
        )}
      </div>
      {state.kind === "error" && <Failure message={state.message} />}
      {state.kind === "ready" && state.results.length > 0 && (
        <ul className="rows">
          {state.results.map((s) => (
            <li key={s.code}>
              <Link to={`/settlements/${encodeURIComponent(s.code)}`} className="row">
                <span>{s.name}</span>
                <span className="row-meta">{s.county ? titleCase(s.county) : ""}</span>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
