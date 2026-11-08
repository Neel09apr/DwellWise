/** "CORK" -> "Cork", "DUN LAOGHAIRE-RATHDOWN" -> "Dun Laoghaire-Rathdown". */
export function titleCase(text: string): string {
  return text.toLowerCase().replace(/(^|[\s-])(\p{L})/gu, (_m, sep: string, ch: string) => sep + ch.toUpperCase());
}
