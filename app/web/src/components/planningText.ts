const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

/** "2026-01" -> "Jan 2026". */
export function monthLabel(month: string): string {
  const [year, m] = month.split("-");
  return `${MONTHS[Number(m) - 1]} ${year}`;
}

/** Share of decided applications (granted or refused) that were granted, rounded; null when none were decided. */
export function decidedShare(granted: number, refused: number): number | null {
  const decided = granted + refused;
  return decided ? Math.round((granted / decided) * 100) : null;
}
