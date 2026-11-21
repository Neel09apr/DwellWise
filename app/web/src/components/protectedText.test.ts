import { describe, expect, it } from "vitest";

import { distanceLabel } from "./protectedText";

describe("distanceLabel", () => {
  it("says a site touching the town touches it", () => {
    expect(distanceLabel(0)).toBe("Touches the town");
  });

  it("uses metres under a kilometre and kilometres from one", () => {
    expect(distanceLabel(648)).toBe("650 m");
    expect(distanceLabel(999)).toBe("1000 m");
    expect(distanceLabel(1000)).toBe("1.0 km");
    expect(distanceLabel(2449)).toBe("2.4 km");
  });
});
