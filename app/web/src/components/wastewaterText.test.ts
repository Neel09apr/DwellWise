import { describe, expect, it } from "vitest";

import { registerLinks } from "./wastewaterText";

const BASE =
  "https://www.water.ie/connections/developer-services/capacity-registers/wastewater-treatment-capacity-register";

describe("registerLinks", () => {
  it("links a county to its own page", () => {
    expect(registerLinks("MAYO")).toEqual([{ label: "Mayo", url: `${BASE}/mayo` }]);
  });

  it("gives counties with city registers both pages", () => {
    expect(registerLinks("CORK").map((l) => l.url)).toEqual([`${BASE}/cork`, `${BASE}/cork-city`]);
    expect(registerLinks("Galway").map((l) => l.label)).toEqual(["Galway County", "Galway City"]);
  });

  it("uses the trailing slash Dublin's pages need", () => {
    expect(registerLinks("DUBLIN").map((l) => l.url)).toEqual([`${BASE}/Dublin/`, `${BASE}/Fingal/`]);
  });

  it("falls back to the national index without a county", () => {
    expect(registerLinks(null)).toEqual([{ label: "All county registers", url: BASE }]);
  });
});
