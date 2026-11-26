/** Words for the question box: tool names a reader understands, and an answer split into paragraphs. */

const TOOLS: Record<string, string> = {
  search_settlements: "town search",
  settlement_brief: "the town's brief",
  application_stats: "planning applications",
  commencement_stats: "construction starts",
  sale_prices: "CSO sale prices",
  cost_estimate: "the cost estimate",
};

/** "town search, CSO sale prices": each source once, in the order first used; unknown tools left out. */
export function checkedAgainst(tools: string[]): string {
  return [...new Set(tools.map((t) => TOOLS[t]).filter((t): t is string => Boolean(t)))].join(", ");
}

/** Plain-text paragraphs. Any Markdown the model still sends is stripped of its symbols, never rendered. */
export function paragraphs(answer: string): string[] {
  return answer
    .replace(/\*\*([^*]+)\*\*/g, "$1")
    .split(/\n\s*\n|\n(?=\s*[*\-•] )/)
    .map((p) => p.replace(/^\s*[*\-•]\s+/gm, "").trim())
    .filter(Boolean);
}
