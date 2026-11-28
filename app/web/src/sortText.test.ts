import { describe, expect, it } from "vitest";

import { nextSort, sortRows } from "./sortText";

const rows = [
  { name: "Wexford", total: 1200 },
  { name: "Carlow", total: 449 },
  { name: "Cork", total: 3224 },
  { name: "cavan", total: 449 },
];

describe("sorting table rows", () => {
  it("compares numbers as values, not as text", () => {
    expect(sortRows(rows, (r) => r.total, "number", "ascending").map((r) => r.total)).toEqual([449, 449, 1200, 3224]);
    expect(sortRows(rows, (r) => r.total, "number", "descending").map((r) => r.name)[0]).toBe("Cork");
  });

  it("compares text by locale, ignoring case, and keeps equal rows in their previous order", () => {
    expect(sortRows(rows, (r) => r.name, "text", "ascending").map((r) => r.name)).toEqual([
      "Carlow",
      "cavan",
      "Cork",
      "Wexford",
    ]);
    expect(
      sortRows(rows, (r) => r.total, "number", "ascending")
        .slice(0, 2)
        .map((r) => r.name),
    ).toEqual(["Carlow", "cavan"]);
    const cased = [{ name: "Navan" }, { name: "navan" }];
    expect(sortRows(cased, (r) => r.name, "text", "ascending").map((r) => r.name)).toEqual(["Navan", "navan"]);
  });

  it("puts rows with no value first when ascending and never reorders the input", () => {
    const zero = [{ u: null }, { u: 0 }, { u: 2 }];
    expect(sortRows(zero, (r) => r.u, "number", "descending").map((r) => r.u)).toEqual([2, 0, null]);
    const units = [{ u: 3 }, { u: null }, { u: 1 }];
    expect(sortRows(units, (r) => r.u, "number", "ascending").map((r) => r.u)).toEqual([null, 1, 3]);
    expect(units.map((r) => r.u)).toEqual([3, null, 1]);
  });

  it("starts ascending, flips on a repeat, and starts again on another column", () => {
    const first = nextSort(null, "total");
    expect(first).toEqual({ key: "total", direction: "ascending" });
    expect(nextSort(first, "total")).toEqual({ key: "total", direction: "descending" });
    expect(nextSort(nextSort(first, "total"), "name")).toEqual({ key: "name", direction: "ascending" });
  });
});
