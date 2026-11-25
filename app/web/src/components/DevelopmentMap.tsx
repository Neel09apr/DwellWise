import { lazy, Suspense } from "react";

import { api } from "../api/client";
import { useResource } from "../useResource";
import { Failure, Loading } from "./Status";

const Canvas = lazy(() => import("./DevelopmentMapCanvas"));
const fmt = new Intl.NumberFormat("en-IE");

/** Schemes of five homes or more started (filled) or applied for (ringed) in the last 12 months. */
export function DevelopmentMap({ county }: { county?: string }) {
  const data = useResource((signal) => api.developments(county, signal), county ?? "ireland");
  return (
    <section aria-labelledby="map-title" className="level">
      <h2 id="map-title" className="level-title">
        Schemes of five homes or more, last 12 months
      </h2>
      {data.kind === "loading" && <Loading what="the map" />}
      {data.kind === "error" && <Failure message={data.message} />}
      {data.kind === "ready" && (
        <>
          <p className="legend">
            <span className="legend-started" aria-hidden="true" /> Construction started (
            {fmt.format(data.data.features.filter((f) => f.properties.kind === "started").length)})
            <span className="legend-applied" aria-hidden="true" /> Planning application (
            {fmt.format(data.data.features.filter((f) => f.properties.kind === "applied").length)})
          </p>
          <Suspense fallback={<Loading what="the map" />}>
            <Canvas data={data.data} />
          </Suspense>
          <p className="note">
            Circle size follows the number of homes. Smaller schemes and one-off houses are counted in the figures
            above but never placed on the map. Applications run to the national dataset&apos;s newest date.{" "}
            {data.data.attribution.join(" ")} Map: OpenFreeMap, OpenMapTiles, OpenStreetMap contributors.
          </p>
        </>
      )}
    </section>
  );
}
