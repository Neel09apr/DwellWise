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
