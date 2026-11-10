import type { components } from "./schema";

type Schemas = components["schemas"];
export type County = Schemas["County"];
export type SettlementSummary = Schemas["SettlementSummary"];
export type SettlementDetail = Schemas["SettlementDetail"];

/** Every API error carries {error: {code, message}}; this keeps the status too. */
export class ApiError extends Error {
  constructor(
    readonly status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function get<T>(path: string, signal?: AbortSignal): Promise<T> {
  let response: Response;
  try {
    response = await fetch(path, { headers: { Accept: "application/json" }, signal });
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") throw error;
    throw new ApiError(0, "The DwellWise service could not be reached.");
  }
  const body: unknown = await response.json().catch(() => null);
  if (!response.ok) {
    const message = (body as { error?: { message?: string } } | null)?.error?.message;
    throw new ApiError(response.status, message ?? `Request failed (${response.status}).`);
  }
  return body as T;
}

export const api = {
  counties: (signal?: AbortSignal) => get<County[]>("/v1/counties", signal),
  countySettlements: (name: string, signal?: AbortSignal) =>
    get<SettlementSummary[]>(`/v1/counties/${encodeURIComponent(name)}/settlements`, signal),
  searchSettlements: (q: string, signal?: AbortSignal) =>
    get<SettlementSummary[]>(`/v1/settlements?${new URLSearchParams({ q })}`, signal),
  settlement: (code: string, signal?: AbortSignal) =>
    get<SettlementDetail>(`/v1/settlements/${encodeURIComponent(code)}`, signal),
};
