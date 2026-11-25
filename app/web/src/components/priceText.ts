const euro = new Intl.NumberFormat("en-IE", { style: "currency", currency: "EUR", maximumFractionDigits: 0 });

/** 420000 -> "€420,000"; a suppressed value -> "Not published". */
export function price(value: number | null | undefined): string {
  return value == null ? "Not published" : euro.format(value);
}

/** The heading for an area: "Eircode area C15 (Navan)", "Cork County", "Ireland". */
export function areaTitle(area: { kind: string; code: string; name: string }): string {
  if (area.kind === "eircode") return `Eircode area ${area.code} (${area.name})`;
  return area.code === "-" ? "Ireland" : area.name;
}
