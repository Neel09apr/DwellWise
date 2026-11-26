import { describe, expect, it } from "vitest";

import type { ApplicationStats, Brief, CommencementStats, Prices } from "./api/client";
import { headlineFigures, townFigures } from "./overviewText";

const counts = {
  granted: 7000,
  refused: 900,
  pending: 2000,
  withdrawn: 100,
  other: 50,
  total: 10050,
};
const apps = {
  residential: null,
  totals: counts,
} as unknown as ApplicationStats;
const starts = {
  totals: { notices: 1234, homes: 30500 },
} as unknown as CommencementStats;
const month = (m: string, median: number | null) => ({
  month: m,
  sales: 10,
  median,
  new_sales: null,
  new_median: null,
});
const prices = {
  areas: [
    {
      kind: "region",
      code: "39",
      name: "Cork City",
      latest: null,
      sales_12_months: 0,
      months: [],
    },
    {
      kind: "region",
      code: "40",
      name: "Cork County",
      latest: month("2026-09", 340000),
      sales_12_months: 9,
      months: [],
    },
  ],
} as unknown as Prices;

describe("a place's headline figures", () => {
  it("gives applications, homes started and the first area with a median, each pointing at its section", () => {
    expect(headlineFigures(apps, starts, prices)).toEqual([
      {
        id: "activity",
        value: "10,050",
        label: "planning applications, 12 months",
        detail: "7,000 granted so far",
      },
      {
        id: "building",
        value: "30,500",
        label: "homes started, 12 months",
        detail: "1,234 commencement notices",
      },
      {
        id: "prices-title",
        value: "€340,000",
        label: "median sale price",
        detail: "Cork County, Sep 2026",
      },
    ]);
  });

  it("says residential when the planning figures are residential only", () => {
    const [first] = headlineFigures({ ...apps, residential: true }, null, null);
    expect(first?.label).toBe("residential applications, 12 months");
  });

  it("leaves out what has not loaded and an area with no median", () => {
    expect(headlineFigures(null, null, null)).toEqual([]);
    const none = { areas: [prices.areas[0]] } as unknown as Prices;
    expect(headlineFigures(null, starts, none).map((f) => f.id)).toEqual(["building"]);
    const unpublished = {
      areas: [{ ...prices.areas[1], name: "Suppressed", latest: month("2026-10", null) }, prices.areas[1]],
    } as unknown as Prices;
    expect(headlineFigures(null, null, unpublished)[0]?.detail).toBe("Cork County, Sep 2026");
  });
});

describe("a brief's summary figures", () => {
  const decisions = { granted: 12, refused: 3, pending: 2, withdrawn: 0, other: 1, total: 18 };
  const site = (band: string) => ({ designation: "SAC", site_code: band, name: band, url: null, distance_m: 0, band });
  const brief = {
    precedents: { years: 4, residential: decisions },
    protected: { sites: [site("touches"), site("1km"), site("5km")] },
  } as unknown as Brief;

  it("gives grants, homes started, protected sites within 1 km and the area's price, each pointing at its section", () => {
    expect(townFigures(brief, starts, prices)).toEqual([
      {
        id: "precedents",
        value: "12",
        label: "residential applications granted, 4 years",
        detail: "3 refused, 2 pending",
      },
      { id: "building", value: "30,500", label: "homes started, 12 months", detail: "1,234 commencement notices" },
      { id: "protected", value: "2", label: "protected sites within 1 km", detail: "3 within 5 km" },
      { id: "prices", value: "€340,000", label: "median sale price", detail: "Cork County, Sep 2026" },
    ]);
  });

  it("leaves out what has not loaded", () => {
    expect(townFigures(null, null, null)).toEqual([]);
    expect(townFigures(null, starts, null).map((f) => f.id)).toEqual(["building"]);
  });
});
