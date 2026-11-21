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

const PLACEHOLDER = /^(n\/?a|none|-)?$/i;

/** The council's own decision wording, or the class when the wording is a placeholder such as "N/A". */
export function decisionLabel(decision: string | null | undefined, decisionClass: string): string {
  const text = (decision ?? "").trim();
  return PLACEHOLDER.test(text) ? decisionClass.charAt(0).toUpperCase() + decisionClass.slice(1) : text;
}
