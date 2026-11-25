import type { DevelopmentProperties } from "../api/client";
import { dayLabel } from "../text";

const STATUS: Record<string, string> = {
  granted: "granted",
  refused: "refused",
  pending: "pending",
  withdrawn: "withdrawn",
  other: "other outcome",
};

/** The lines of a map pop-up, as plain text (never HTML: names come from public filings). */
export function popupLines(p: DevelopmentProperties): string[] {
  const where = p.settlement ?? p.authority;
  if (p.kind === "started") {
    return [
      p.label ?? "Unnamed scheme",
      `${p.homes} homes, start ${dayLabel(p.day)}`,
      `${where}${p.reference ? ` · planning ref. ${p.reference}` : ""}`,
    ];
  }
  return [
    `Application ${p.reference ?? ""}`.trim(),
    `${p.homes} homes, received ${dayLabel(p.day)}, ${STATUS[p.status ?? ""] ?? "status unknown"}`,
    where,
  ];
}

/** Councils that rarely state units: their applications cannot be sized, so the map cannot show them. */
export function sparseUnitsNote(councils: { authority: string; share: number }[]): string | null {
  if (councils.length === 0) return null;
  const named = councils.map((c) => `${c.authority} (${c.share}% of applications)`);
  const list = named.length > 1 ? `${named.slice(0, -1).join(", ")} and ${named.at(-1)}` : named[0];
  return `Applications from ${list} rarely or never state a number of homes, so they cannot appear on the map; their construction starts still do.`;
}
