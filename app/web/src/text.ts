import type { SettlementSummary } from "./api/client";

/** "CORK" -> "Cork", "DUN LAOGHAIRE-RATHDOWN" -> "Dun Laoghaire-Rathdown". */
export function titleCase(text: string): string {
  return text.toLowerCase().replace(/(^|[\s-])(\p{L})/gu, (_m, sep: string, ch: string) => sep + ch.toUpperCase());
}

/** URL form of a county name: "DUN LAOGHAIRE RATHDOWN" -> "dun-laoghaire-rathdown". */
export function countySlug(name: string): string {
  return name.toLowerCase().replace(/\s+/g, "-");
}

/** Back from the URL: "dun-laoghaire-rathdown" -> "dun laoghaire rathdown"; the API accepts any case. */
export function countyFromSlug(slug: string): string {
  return slug.replace(/-/g, " ");
}

/** Settlements grouped under their first letter, letters in order, names in order within each. */
export function byFirstLetter(items: SettlementSummary[]): [string, SettlementSummary[]][] {
  const groups = new Map<string, SettlementSummary[]>();
  for (const item of [...items].sort((a, b) => a.name.localeCompare(b.name, "en-IE"))) {
    const letter = item.name.normalize("NFD").charAt(0).toUpperCase();
    groups.set(letter, [...(groups.get(letter) ?? []), item]);
  }
  return [...groups.entries()];
}
