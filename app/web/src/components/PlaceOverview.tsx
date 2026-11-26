import { type ReactNode, useState } from "react";

import { api } from "../api/client";
import { headlineFigures } from "../overviewText";
import { type Resource, useResource } from "../useResource";
import { BuildingSection } from "./BuildingNow";
import { DevelopmentMap } from "./DevelopmentMap";
import { Board } from "./Board";
import { PageRail } from "./PageRail";
import { PlanningActivity } from "./PlanningActivity";
import { PriceSection } from "./SalePrices";

const ready = <T,>(r: Resource<T>): T | null => (r.kind === "ready" ? r.data : null);

/** Ireland or one county: headline figures, an optional lead section, then the sections they come from. Each dataset is fetched once. */
type Props = {
  county?: string;
  title: string;
  place: ReactNode;
  lead?: ReactNode; // notices before the overview's own (a county's towns compared)
  after?: ReactNode; // notices after them (counties, a county's towns A to Z)
  rail: { id: string; label: string }[];
};

export function PlaceOverview({ county, title, place, lead, after, rail }: Props) {
  const [residential, setResidential] = useState(false);
  const key = county ?? "ireland";
  const apps = useResource((s) => api.applicationStats({ county, residential }, s), `${key}:${residential}`);
  const starts = useResource((s) => api.commencementStats({ county }, s), key);
  const prices = useResource((s) => api.prices({ county }, s), key);
  const figures = headlineFigures(ready(apps), ready(starts), ready(prices));

  return (
    <>
      <Board title={title} place={place} figures={figures} foot="Compiled nightly from public records." />
      <div className="with-rail">
        <PageRail links={rail} />
        <div className="notices">
          {lead}
          <PlanningActivity stats={apps} national={!county} residential={residential} onResidential={setResidential} />
          <BuildingSection stats={starts} />
          <DevelopmentMap county={county} />
          <PriceSection data={prices} />
          {after}
        </div>
      </div>
    </>
  );
}
