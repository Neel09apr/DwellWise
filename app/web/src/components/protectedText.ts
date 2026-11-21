/** Wording for brief section 03. Distances are boundary to boundary, from the API. */

export const DESIGNATIONS: Record<string, string> = {
  SAC: "Special Area of Conservation",
  SPA: "Special Protection Area",
  NHA: "Natural Heritage Area",
};

/** "Touches the town", "650 m", "2.4 km". */
export function distanceLabel(metres: number): string {
  if (metres <= 0) return "Touches the town";
  if (metres < 1000) return `${Math.round(metres / 10) * 10} m`;
  return `${(metres / 1000).toFixed(1)} km`;
}
