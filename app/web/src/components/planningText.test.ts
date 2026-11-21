import { describe, expect, it } from "vitest";

import { decidedShare, decisionLabel, monthLabel } from "./planningText";

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

describe("decisionLabel", () => {
  it("keeps the council's own wording", () => {
    expect(decisionLabel("CONDITIONAL", "granted")).toBe("CONDITIONAL");
    expect(decisionLabel("  Grant Permission  ", "granted")).toBe("Grant Permission");
  });
  it("shows the class when the wording is a placeholder or missing", () => {
    expect(decisionLabel("N/A", "pending")).toBe("Pending");
    expect(decisionLabel("n/a", "pending")).toBe("Pending");
    expect(decisionLabel("", "withdrawn")).toBe("Withdrawn");
    expect(decisionLabel(null, "pending")).toBe("Pending");
  });
});
