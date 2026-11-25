import "maplibre-gl/dist/maplibre-gl.css";

import { Map, type MapLayerMouseEvent, NavigationControl, Popup, setWorkerUrl } from "maplibre-gl";
import workerUrl from "maplibre-gl/dist/maplibre-gl-worker.mjs?url";
import { useEffect, useRef } from "react";

import type { Developments } from "../api/client";
import { popupLines } from "./mapText";

// Bundled with a hashed name and served from this origin, so the CSP can say worker-src 'self'.
setWorkerUrl(workerUrl);

const IRELAND: [number, number, number, number] = [-10.7, 51.35, -5.9, 55.45];
const STYLE = "https://tiles.openfreemap.org/styles/";

function cssVar(name: string): string {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
}

/** Plain-text pop-up content: one line per element, set with textContent. */
function popupNode(lines: string[]): HTMLElement {
  const box = document.createElement("div");
  box.className = "map-popup";
  for (const [i, line] of lines.entries()) {
    const el = document.createElement(i === 0 ? "strong" : "span");
    el.textContent = line;
    box.append(el);
  }
  return box;
}

export default function DevelopmentMapCanvas({ data }: { data: Developments }) {
  const box = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!box.current) return;
    const dark = window.matchMedia("(prefers-color-scheme: dark)").matches;
    const bounds = data.county && data.features.length ? featureBounds(data) : IRELAND;
    const map = new Map({
      container: box.current,
      style: STYLE + (dark ? "dark" : "positron"),
      bounds,
      fitBoundsOptions: { padding: 24, maxZoom: 11 },
      cooperativeGestures: true, // the page scrolls past the map unless ctrl/two fingers are used
    });
    map.addControl(new NavigationControl({ showCompass: false }), "top-right");

    map.on("load", () => {
      map.addSource("developments", { type: "geojson", data: data as never });
      const radius = ["interpolate", ["linear"], ["sqrt", ["get", "homes"]], 2, 3, 12, 11, 34, 22];
      map.addLayer({
        id: "applied",
        type: "circle",
        source: "developments",
        filter: ["==", ["get", "kind"], "applied"],
        paint: {
          "circle-radius": radius as never,
          "circle-color": "rgba(0,0,0,0)",
          "circle-stroke-color": cssVar("--muted"),
          "circle-stroke-width": 1.5,
        },
      });
      map.addLayer({
        id: "started",
        type: "circle",
        source: "developments",
        filter: ["==", ["get", "kind"], "started"],
        paint: {
          "circle-radius": radius as never,
          "circle-color": cssVar("--accent"),
          "circle-opacity": 0.75,
          "circle-stroke-color": cssVar("--ground"),
          "circle-stroke-width": 1,
        },
      });
      for (const layer of ["started", "applied"]) {
        map.on("click", layer, (e: MapLayerMouseEvent) => {
          const feature = e.features?.[0];
          if (!feature) return;
          new Popup({ closeButton: true, maxWidth: "18rem" })
            .setLngLat(e.lngLat)
            .setDOMContent(popupNode(popupLines(feature.properties as never)))
            .addTo(map);
        });
        map.on("mouseenter", layer, () => (map.getCanvas().style.cursor = "pointer"));
        map.on("mouseleave", layer, () => (map.getCanvas().style.cursor = ""));
      }
    });
    return () => map.remove();
  }, [data]);

  return <div ref={box} className="map" role="region" aria-label="Map of housing schemes" />;
}

function featureBounds(data: Developments): [number, number, number, number] {
  const xs = data.features.map((f) => f.geometry.coordinates[0] ?? 0);
  const ys = data.features.map((f) => f.geometry.coordinates[1] ?? 0);
  return [Math.min(...xs), Math.min(...ys), Math.max(...xs), Math.max(...ys)];
}
