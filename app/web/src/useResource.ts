import { useEffect, useState } from "react";

export type Resource<T> = { kind: "loading" } | { kind: "error"; message: string } | { kind: "ready"; data: T };

/** Load once per key, cancel on change or unmount. One shape for every page. */
export function useResource<T>(load: (signal: AbortSignal) => Promise<T>, key: string): Resource<T> {
  const [state, setState] = useState<Resource<T>>({ kind: "loading" });

  // `load` is a new closure every render; `key` is what identifies the resource.
  useEffect(() => {
    const controller = new AbortController();
    setState({ kind: "loading" });
    load(controller.signal)
      .then((data) => setState({ kind: "ready", data }))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setState({ kind: "error", message: error instanceof Error ? error.message : "Something went wrong." });
      });
    return () => controller.abort();
  }, [key]); // eslint-disable-line react-hooks/exhaustive-deps

  return state;
}
