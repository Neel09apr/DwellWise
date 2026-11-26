import { describe, expect, it } from "vitest";

import { COUNCILS, DRAFT_KEY, EMPTY_FORM, costQuery, councilsFor, loadDraft, saveDraft } from "./costText";

describe("councils", () => {
  it("lists all 31 local authorities, each on HTTPS", () => {
    expect(COUNCILS).toHaveLength(31);
    expect(new Set(COUNCILS.map((c) => c.name)).size).toBe(31);
    expect(COUNCILS.every((c) => c.url.startsWith("https://"))).toBe(true);
  });

  it("offers a county's own councils, or every council when the county is unknown", () => {
    expect(councilsFor("DUBLIN").map((c) => c.name)).toHaveLength(4);
    expect(councilsFor(" cork ").map((c) => c.name)).toEqual(["Cork City Council", "Cork County Council"]);
    expect(councilsFor("Meath").map((c) => c.name)).toEqual(["Meath County Council"]);
    expect(councilsFor(undefined)).toHaveLength(31);
    expect(councilsFor("Atlantis")).toHaveLength(31);
    expect(councilsFor("Cor")).toHaveLength(31); // a whole county name, never a prefix
  });
});

describe("the cost form", () => {
  const filled = {
    ...EMPTY_FORM,
    homes: "8",
    floor_area_m2: "110",
    build_cost_per_m2: "2,800",
    contribution: "117",
    fees_pct: "10",
    contingency_pct: "5",
    finance_rate_pct: "8",
    finance_months: "18",
  };

  it("sends every figure, drops thousands separators, and leaves land out when empty", () => {
    const query = new URLSearchParams(costQuery(filled));
    expect(query.get("build_cost_per_m2")).toBe("2800");
    expect(query.get("contribution_basis")).toBe("per_m2");
    expect(query.has("land")).toBe(false);
    expect(new URLSearchParams(costQuery({ ...filled, land: "400000" })).get("land")).toBe("400000");
  });

  it("sends an empty required figure as empty, so the API refuses it rather than guessing", () => {
    expect(new URLSearchParams(costQuery({ ...filled, fees_pct: "" })).get("fees_pct")).toBe("");
  });

  it("remembers figures in this browser and survives storage that is blocked or holds junk", () => {
    const store = new Map<string, string>();
    const storage = { getItem: (k: string) => store.get(k) ?? null, setItem: (k: string, v: string) => store.set(k, v) };
    saveDraft(storage, filled);
    expect(loadDraft(storage)).toEqual(filled);
    store.set(DRAFT_KEY, "{not json");
    expect(loadDraft(storage)).toEqual(EMPTY_FORM);
    store.set(DRAFT_KEY, JSON.stringify({ homes: 8, contribution_basis: "per_acre" }));
    expect(loadDraft(storage)).toEqual(EMPTY_FORM);
    const blocked = {
      getItem: () => {
        throw new Error("blocked");
      },
      setItem: () => {
        throw new Error("blocked");
      },
    };
    expect(loadDraft(blocked)).toEqual(EMPTY_FORM);
    expect(() => saveDraft(blocked, filled)).not.toThrow();
  });
});
