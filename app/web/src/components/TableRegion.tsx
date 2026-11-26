import type { ReactNode } from "react";

/** A table that scrolls sideways inside a named, focusable region, so a keyboard can reach every column. */
export function TableRegion({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="table-region" role="region" aria-label={label} tabIndex={0}>
      {children}
    </div>
  );
}
