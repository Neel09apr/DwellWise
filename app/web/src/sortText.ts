/** Sorting for data tables: text by locale (numbers inside text in order), numbers and dates as values. */

export type SortDirection = "ascending" | "descending";
export type SortState = { key: string; direction: SortDirection } | null;
export type SortType = "text" | "number";

const collator = new Intl.Collator("en-IE", { numeric: true, sensitivity: "base" });

/** A new array in the requested order; equal rows keep their previous order (the sort is stable). */
export function sortRows<T>(
  rows: readonly T[],
  value: (row: T) => string | number | null | undefined,
  type: SortType,
  direction: SortDirection,
): T[] {
  const factor = direction === "ascending" ? 1 : -1;
  const num = (row: T) => {
    const v = value(row);
    return v === null || v === undefined || v === "" ? Number.NEGATIVE_INFINITY : Number(v);
  };
  return [...rows].sort((a, b) =>
    type === "number"
      ? factor * (num(a) - num(b) || 0)
      : factor * collator.compare(String(value(a) ?? ""), String(value(b) ?? "")),
  );
}

/** The first press on a column sorts ascending, a repeat flips it, another column starts ascending again. */
export function nextSort(current: SortState, key: string): SortState {
  if (current?.key !== key) return { key, direction: "ascending" };
  return { key, direction: current.direction === "ascending" ? "descending" : "ascending" };
}
