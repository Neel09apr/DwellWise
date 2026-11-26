import { type ReactNode, useState } from "react";

import { api } from "../api/client";
import { headlineFigures } from "../overviewText";
import { type Resource, useResource } from "../useResource";
import { BuildingSection } from "./BuildingNow";
import { DevelopmentMap } from "./DevelopmentMap";
import { PlanningActivity } from "./PlanningActivity";
import { PriceSection } from "./SalePrices";

const ready = <T,>(r: Resource<T>): T | null => (r.kind === "ready" ? r.data : null);

/** Ireland or one county: headline figures, an optional lead section, then the sections they come from. Each dataset is fetched once. */
export function PlaceOverview({ county, lead }: { county?: string; lead?: ReactNode }) {
  const [residential, setResidential] = useState(false);
  const place = county ?? "ireland";
  const apps = useResource((s) => api.applicationStats({ county, residential }, s), `${place}:${residential}`);
  const starts = useResource((s) => api.commencementStats({ county }, s), place);
  const prices = useResource((s) => api.prices({ county }, s), place);
  const figures = headlineFigures(ready(apps), ready(starts), ready(prices));

  return (
    <>
      {figures.length > 0 && (
        <ul className="figures" aria-label="Headline figures">
          {figures.map((f) => (
            <li key={f.id}>
              <a href={`#${f.id}`}>
                <span className="figure-value">{f.value}</span>
                <span className="figure-label">{f.label}</span>
                <span className="figure-detail">{f.detail}</span>
              </a>
            </li>
          ))}
        </ul>
      )}
      {lead}
      <PlanningActivity stats={apps} national={!county} residential={residential} onResidential={setResidential} />
      <BuildingSection stats={starts} />
      <DevelopmentMap county={county} />
      <PriceSection data={prices} />
    </>
  );
}
