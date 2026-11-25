import { describe, expect, it } from "vitest";

import { areaTitle, price } from "./priceText";

describe("price", () => {
  it("formats euro without cents and says when the CSO suppressed a value", () => {
    expect(price(420000)).toBe("€420,000");
    expect(price(null)).toBe("Not published");
  });
});

describe("areaTitle", () => {
  it("names routing areas by code and town, CSO areas by name, and the national row as Ireland", () => {
    expect(areaTitle({ kind: "eircode", code: "C15", name: "Navan" })).toBe("Eircode area C15 (Navan)");
    expect(areaTitle({ kind: "region", code: "40", name: "Cork County" })).toBe("Cork County");
    expect(areaTitle({ kind: "region", code: "-", name: "All" })).toBe("Ireland");
  });
});
