import { describe, expect, it } from "vitest";

import { decidedShare, monthLabel } from "./planningText";

describe("monthLabel", () => {
  it("names the month and keeps the year", () => {
    expect(monthLabel("2026-01")).toBe("Jan 2026");
    expect(monthLabel("2025-12")).toBe("Dec 2025");
  });
});

describe("decidedShare", () => {
  it("counts only granted and refused, never pending", () => {
    expect(decidedShare(3, 1)).toBe(75);
    expect(decidedShare(2, 1)).toBe(67);
  });
  it("is null when nothing has been decided", () => {
    expect(decidedShare(0, 0)).toBeNull();
  });
});
