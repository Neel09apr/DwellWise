import { afterEach, describe, expect, it, vi } from "vitest";

import { ApiError, api } from "./client";

afterEach(() => vi.unstubAllGlobals());

describe("api client", () => {
  it("encodes the search query", async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response("[]", { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);
    await api.searchSettlements("Carrick & Shannon");
    expect(fetchMock.mock.calls[0]?.[0]).toBe("/v1/settlements?q=Carrick+%26+Shannon");
  });

  it("surfaces the API's own error message", async () => {
    const body = JSON.stringify({ error: { code: "not_found", message: "No settlement has the code 9." } });
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(body, { status: 404 })));
    await expect(api.settlement("9")).rejects.toEqual(new ApiError(404, "No settlement has the code 9."));
  });

  it("says plainly when the service cannot be reached", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("Failed to fetch")));
    await expect(api.settlement("1")).rejects.toMatchObject({ status: 0, message: expect.stringMatching(/reached/) });
  });
});
