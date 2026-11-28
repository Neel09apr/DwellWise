import type { SortState } from "../sortText";

/** A sortable column heading: a button inside the th, aria-sort on the sorted column's th only. */
export function SortHeader({
  label,
  column,
  sort,
  onSort,
  className,
}: {
  label: string;
  column: string;
  sort: SortState;
  onSort: (column: string) => void;
  className?: string;
}) {
  const direction = sort?.key === column ? sort.direction : undefined;
  return (
    <th scope="col" aria-sort={direction} className={className ? `sortable ${className}` : "sortable"}>
      <button type="button" onClick={() => onSort(column)}>
        {label}
        <svg className="sort-mark" aria-hidden="true" viewBox="0 0 10 12" width="10" height="12">
          <path d="M5 1 L9 5 H1 Z" className="sort-up" />
          <path d="M5 11 L9 7 H1 Z" className="sort-down" />
        </svg>
      </button>
    </th>
  );
}

/** What a screen reader hears once per sort; the table itself is never a live region. */
export function sortMessage(label: string | undefined, sort: SortState, rows: number): string {
  return sort && label ? `Sorted by ${label}, ${sort.direction}, ${rows} rows` : "";
}
