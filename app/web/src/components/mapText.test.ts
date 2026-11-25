import { describe, expect, it } from "vitest";

import { popupLines } from "./mapText";

const base = {
  authority: "Meath County Council",
  homes: 7,
  day: "2026-11-25",
  settlement: "Trim",
  reference: "2660334",
};

describe("popupLines", () => {
  it("names a started scheme with its homes, start date and planning reference", () => {
    expect(popupLines({ ...base, kind: "started", label: "Haggard Street", status: null })).toEqual([
      "Haggard Street",
      "7 homes, start 25 Nov 2026",
      "Trim · planning ref. 2660334",
    ]);
  });

  it("describes an application by its reference and decision, falling back to the council", () => {
    expect(popupLines({ ...base, kind: "applied", label: null, status: "pending", settlement: null })).toEqual([
      "Application 2660334",
      "7 homes, received 25 Nov 2026, pending",
      "Meath County Council",
    ]);
  });

  it("keeps markup as text", () => {
    const [name] = popupLines({ ...base, kind: "started", label: "<img src=x onerror=alert(1)>", status: null });
    expect(name).toBe("<img src=x onerror=alert(1)>"); // rendered with textContent, so it shows as text
  });
});
