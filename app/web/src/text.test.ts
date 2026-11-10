import { describe, expect, it } from "vitest";

import { byFirstLetter, countyFromSlug, countySlug, titleCase } from "./text";

describe("text helpers", () => {
  it("title-cases county names, including hyphenated ones", () => {
    expect(titleCase("CORK")).toBe("Cork");
    expect(titleCase("DUN LAOGHAIRE-RATHDOWN")).toBe("Dun Laoghaire-Rathdown");
  });

  it("round-trips county names through the URL", () => {
    expect(countySlug("DUN LAOGHAIRE RATHDOWN")).toBe("dun-laoghaire-rathdown");
    expect(countyFromSlug("dun-laoghaire-rathdown")).toBe("dun laoghaire rathdown");
  });

  it("groups settlements A to Z, folding fadas into their letter", () => {
    const s = (name: string) => ({ code: name, name, county: "MAYO" });
    const groups = byFirstLetter([s("Castlebar"), s("Ballina"), s("Ébhéar"), s("Ballinrobe"), s("Easkey")]);
    expect(groups.map(([letter, items]) => [letter, items.map((i) => i.name)])).toEqual([
      ["B", ["Ballina", "Ballinrobe"]],
      ["C", ["Castlebar"]],
      ["E", ["Easkey", "Ébhéar"]],
    ]);
  });
});
