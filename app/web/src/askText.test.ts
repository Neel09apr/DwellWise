import { describe, expect, it } from "vitest";

import { checkedAgainst, paragraphs } from "./askText";

describe("the question box's words", () => {
  it("names each source once, in order, and leaves out tools it does not know", () => {
    expect(checkedAgainst(["search_settlements", "sale_prices", "sale_prices", "run_sql"])).toBe(
      "town search, CSO sale prices",
    );
    expect(checkedAgainst([])).toBe("");
  });

  it("splits an answer into paragraphs and strips Markdown symbols instead of rendering them", () => {
    const answer = "In Navan:\n\n* **Median:** €420,000\n* **New homes:** €432,500\n\nSource: CSO.";
    expect(paragraphs(answer)).toEqual(["In Navan:", "Median: €420,000", "New homes: €432,500", "Source: CSO."]);
    expect(paragraphs("One line only.")).toEqual(["One line only."]);
  });
});
