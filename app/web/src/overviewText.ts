/** Words and numbers for a place's headline figures: the same facts its sections show, never new ones. */

import type { ApplicationStats, Brief, CommencementStats, Prices } from "./api/client";
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
  const median = medianFigure(prices, "prices-title");
  if (median) figures.push(median);
  return figures;
}

/** A brief's four figures, from data it already fetched: the same facts as the town's row in a shortlist. */
export function townFigures(brief: Brief | null, starts: CommencementStats | null, prices: Prices | null): Figure[] {
  const figures: Figure[] = [];
  if (brief) {
    const p = brief.precedents;
    figures.push({
      id: "precedents",
      value: fmt.format(p.residential.granted),
      label: `residential applications granted, ${p.years} years`,
      detail: `${fmt.format(p.residential.refused)} refused, ${fmt.format(p.residential.pending)} pending`,
    });
  }
  if (starts)
    figures.push({
      id: "building",
      value: fmt.format(starts.totals.homes),
      label: "homes started, 12 months",
      detail: `${fmt.format(starts.totals.notices)} commencement notices`,
    });
  if (brief) {
    const near = brief.protected.sites.filter((s) => s.band === "touches" || s.band === "1km").length;
    figures.push({
      id: "protected",
      value: fmt.format(near),
      label: "protected sites within 1 km",
      detail: `${fmt.format(brief.protected.sites.length)} within 5 km`,
    });
  }
  const median = medianFigure(prices, "prices");
  if (median) figures.push(median);
  return figures;
}

/** The first area with a published median, as a figure pointing at section ``id``. */
function medianFigure(prices: Prices | null, id: string): Figure | null {
  const area = prices?.areas.find((a) => a.latest?.median != null);
  if (!area?.latest) return null;
  return {
    id,
    value: price(area.latest.median),
    label: "median sale price",
    detail: `${areaTitle(area)}, ${monthLabel(area.latest.month)}`,
  };
}
