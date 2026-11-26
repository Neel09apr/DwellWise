import type { components } from "./schema";

type Schemas = components["schemas"];
export type County = Schemas["County"];
export type SettlementSummary = Schemas["SettlementSummary"];
export type SettlementDetail = Schemas["SettlementDetail"];
export type ApplicationStats = Schemas["ApplicationStats"];
export type Brief = Schemas["Brief"];
export type CommencementStats = Schemas["CommencementStats"];
export type Developments = Schemas["Developments"];
export type DevelopmentProperties = Schemas["DevelopmentProperties"];
export type Prices = Schemas["Prices"];
export type Costs = Schemas["Costs"];
export type Answer = Schemas["Answer"];
export type AssistantStatus = Schemas["AssistantStatus"];
export type Shortlist = Schemas["Shortlist"];
export type Turn = Schemas["Turn"];

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

async function get<T>(
  path: string,
  signal?: AbortSignal,
  init?: RequestInit,
): Promise<T> {
  let response: Response;
  try {
    response = await fetch(path, {
      ...init,
      headers: {
        Accept: "application/json",
        ...(init?.body ? { "Content-Type": "application/json" } : {}),
      },
      signal,
    });
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError")
      throw error;
    throw new ApiError(0, "The DwellWise service could not be reached.");
  }
  const body: unknown = await response.json().catch(() => null);
  if (!response.ok) {
    const message = (body as { error?: { message?: string } } | null)?.error
      ?.message;
    throw new ApiError(
      response.status,
      message ?? `Request failed (${response.status}).`,
    );
  }
  return body as T;
}

export const api = {
  counties: (signal?: AbortSignal) => get<County[]>("/v1/counties", signal),
  countySettlements: (name: string, signal?: AbortSignal) =>
    get<SettlementSummary[]>(
      `/v1/counties/${encodeURIComponent(name)}/settlements`,
      signal,
    ),
  searchSettlements: (q: string, signal?: AbortSignal) =>
    get<SettlementSummary[]>(
      `/v1/settlements?${new URLSearchParams({ q })}`,
      signal,
    ),
  settlement: (code: string, signal?: AbortSignal) =>
    get<SettlementDetail>(
      `/v1/settlements/${encodeURIComponent(code)}`,
      signal,
    ),
  brief: (code: string, signal?: AbortSignal) =>
    get<Brief>(`/v1/settlements/${encodeURIComponent(code)}/brief`, signal),
  applicationStats: (
    { county, residential }: { county?: string; residential?: boolean },
    signal?: AbortSignal,
  ) => {
    const params = new URLSearchParams();
    if (county) params.set("county", county);
    if (residential) params.set("residential", "true");
    const query = params.toString();
    return get<ApplicationStats>(
      `/v1/stats/applications${query ? `?${query}` : ""}`,
      signal,
    );
  },
  commencementStats: (
    { county, settlement }: { county?: string; settlement?: string },
    signal?: AbortSignal,
  ) => {
    const params = new URLSearchParams();
    if (county) params.set("county", county);
    if (settlement) params.set("settlement", settlement);
    const query = params.toString();
    return get<CommencementStats>(
      `/v1/stats/commencements${query ? `?${query}` : ""}`,
      signal,
    );
  },
  prices: (
    { county, settlement }: { county?: string; settlement?: string },
    signal?: AbortSignal,
  ) => {
    const params = new URLSearchParams();
    if (county) params.set("county", county);
    if (settlement) params.set("settlement", settlement);
    const query = params.toString();
    return get<Prices>(`/v1/prices${query ? `?${query}` : ""}`, signal);
  },
  costs: (query: string, signal?: AbortSignal) =>
    get<Costs>(`/v1/costs?${query}`, signal),
  assistant: (signal?: AbortSignal) =>
    get<AssistantStatus>("/v1/assistant", signal),
  ask: (
    question: string,
    settlement: string | undefined,
    history: Turn[],
    signal?: AbortSignal,
  ) =>
    get<Answer>("/v1/ask", signal, {
      method: "POST",
      body: JSON.stringify({ question, settlement, history }),
    }),
  developments: (county: string | undefined, signal?: AbortSignal) =>
    get<Developments>(
      `/v1/map/developments${county ? `?${new URLSearchParams({ county })}` : ""}`,
      signal,
    ),
};
