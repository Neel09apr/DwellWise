import { describe, expect, it } from "vitest";

import { checkedAgainst, historyOf, paragraphs } from "./askText";

describe("the question box's words", () => {
  it("names each source once, in order, and leaves out tools it does not know", () => {
    expect(
      checkedAgainst([
        "search_settlements",
        "sale_prices",
        "sale_prices",
        "run_sql",
      ]),
    ).toBe("town search, CSO sale prices");
    expect(checkedAgainst([])).toBe("");
  });

  it("splits an answer into paragraphs and strips Markdown symbols instead of rendering them", () => {
    const answer =
      "In Navan:\n\n* **Median:** €420,000\n* **New homes:** €432,500\n\nSource: CSO.";
    expect(paragraphs(answer)).toEqual([
      "In Navan:",
      "Median: €420,000",
      "New homes: €432,500",
      "Source: CSO.",
    ]);
    expect(paragraphs("One line only.")).toEqual(["One line only."]);
  });

  it("sends back only the latest four messages, each cut to 1,000 characters", () => {
    const exchanges = [
      { question: "first", answer: "a1" },
      { question: "second", answer: "x".repeat(1200) },
      { question: "third", answer: "a3" },
    ];
    const history = historyOf(exchanges);
    expect(history.map((h) => h.role)).toEqual([
      "user",
      "assistant",
      "user",
      "assistant",
    ]);
    expect(history[0]).toEqual({ role: "user", content: "second" });
    expect(history[1]?.content).toHaveLength(1000);
    expect(historyOf([])).toEqual([]);
  });

  it("names the shortlist as a source", () => {
    expect(checkedAgainst(["shortlist"])).toBe("the county shortlist");
  });
});
