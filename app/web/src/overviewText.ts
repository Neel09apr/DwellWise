/** Words and numbers for a place's headline figures: the same facts its sections show, never new ones. */

import type { ApplicationStats, CommencementStats, Prices } from "./api/client";
import { monthLabel } from "./components/planningText";
import { areaTitle, price } from "./components/priceText";

const fmt = new Intl.NumberFormat("en-IE");

export type Figure = {
  id: string;
  value: string;
  label: string;
  detail: string;
};

/** Up to three figures, each pointing at the section it comes from; a dataset not loaded yet is left out. */
export function headlineFigures(
  apps: ApplicationStats | null,
  starts: CommencementStats | null,
  prices: Prices | null,
): Figure[] {
  const figures: Figure[] = [];
  if (apps)
    figures.push({
      id: "activity",
      value: fmt.format(apps.totals.total),
      label: apps.residential ? "residential applications, 12 months" : "planning applications, 12 months",
      detail: `${fmt.format(apps.totals.granted)} granted so far`,
    });
  if (starts)
    figures.push({
      id: "building",
      value: fmt.format(starts.totals.homes),
      label: "homes started, 12 months",
      detail: `${fmt.format(starts.totals.notices)} commencement notices`,
    });
  const area = prices?.areas.find((a) => a.latest?.median != null);
  if (area?.latest)
    figures.push({
      id: "prices-title",
      value: price(area.latest.median),
      label: "median sale price",
      detail: `${areaTitle(area)}, ${monthLabel(area.latest.month)}`,
    });
  return figures;
}
