import type { Turn } from "./api/client";

/** Words for the question box: tool names a reader understands, and an answer split into paragraphs. */

const TOOLS: Record<string, string> = {
  search_settlements: "town search",
  settlement_brief: "the town's brief",
  application_stats: "planning applications",
  commencement_stats: "construction starts",
  sale_prices: "CSO sale prices",
  cost_estimate: "the cost estimate",
  shortlist: "the county shortlist",
};

const HISTORY = 4; // the API takes at most four earlier messages
const MESSAGE = 1000; // of at most 1,000 characters each

/** The conversation to send with the next question: the latest exchanges, each message cut to size. */
export function historyOf(exchanges: { question: string; answer: string }[]): Turn[] {
  return exchanges
    .flatMap((e): Turn[] => [
      { role: "user", content: e.question.slice(0, MESSAGE) },
      { role: "assistant", content: e.answer.slice(0, MESSAGE) },
    ])
    .slice(-HISTORY);
}

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
