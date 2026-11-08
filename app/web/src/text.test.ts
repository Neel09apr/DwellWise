import { expect, it } from "vitest";

import { titleCase } from "./text";

it("title-cases county names, including hyphenated ones", () => {
  expect(titleCase("CORK")).toBe("Cork");
  expect(titleCase("DUN LAOGHAIRE-RATHDOWN")).toBe("Dun Laoghaire-Rathdown");
});
