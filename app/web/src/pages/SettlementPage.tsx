import { useParams } from "react-router-dom";

import { api } from "../api/client";
import { Breadcrumbs } from "../components/Breadcrumbs";
import { Failure, Loading } from "../components/Status";
import { countySlug, titleCase } from "../text";
import { useResource } from "../useResource";

/** The brief's sections in order (docs/DESIGN.md F3–F6). Each fills in when its data source lands. */
const SECTIONS = [
  { id: "wastewater", title: "Wastewater capacity", about: "Spare capacity at the treatment plant serving the town." },
  { id: "precedents", title: "Planning precedents", about: "Recent residential planning applications and decisions." },
  { id: "protected", title: "Protected sites nearby", about: "SAC, SPA and NHA sites within 1 km and 5 km." },
  { id: "alternatives", title: "Nearby alternatives", about: "Nearby settlements with spare capacity, by distance." },
];

const number = (i: number) => String(i + 1).padStart(2, "0");

export function SettlementPage() {
  const { code = "" } = useParams();
  const settlement = useResource((signal) => api.settlement(code, signal), code);

  if (settlement.kind === "loading") return <Loading what="the brief" />;
  if (settlement.kind === "error")
    return (
      <>
        <Breadcrumbs trail={[{ label: "Ireland", to: "/" }, { label: "Settlement" }]} />
        <Failure message={settlement.message} />
      </>
    );

  const s = settlement.data;
  const county = s.county ? titleCase(s.county) : null;
  const trail = [
    { label: "Ireland", to: "/" },
    ...(county ? [{ label: county, to: `/counties/${countySlug(s.county ?? "")}` }] : []),
    { label: s.name },
  ];

  return (
    <article>
      <Breadcrumbs trail={trail} />
      <header className="page-head">
        <p className="eyebrow">Pre-planning brief</p>
        <h1>{s.name}</h1>
        <p className="muted">
          {county ? `County ${county}. ` : ""}Evidence about the town as a whole, not about any site in it.
        </p>
        <dl className="facts">
          <div>
            <dt>Area</dt>
            <dd>{s.area_km2.toFixed(2)} km²</dd>
          </div>
          <div>
            <dt>Centre</dt>
            <dd>
              {s.latitude.toFixed(4)}, {s.longitude.toFixed(4)}
            </dd>
          </div>
          <div>
            <dt>CSO code</dt>
            <dd>{s.code}</dd>
          </div>
        </dl>
      </header>

      <nav aria-labelledby="contents" className="contents">
        <h2 id="contents" className="level-title">
          Contents
        </h2>
        <ol>
          {SECTIONS.map((section, i) => (
            <li key={section.id}>
              <a href={`#${section.id}`}>
                <span className="num">{number(i)}</span>
                {section.title}
              </a>
            </li>
          ))}
          <li>
            <a href="#sources">
              <span className="num">{number(SECTIONS.length)}</span>
              Sources
            </a>
          </li>
        </ol>
      </nav>

      {SECTIONS.map((section, i) => (
        <section key={section.id} id={section.id} className="section" aria-labelledby={`${section.id}-title`}>
          <h2 id={`${section.id}-title`}>
            <span className="num">{number(i)}</span>
            {section.title}
          </h2>
          <p className="muted">{section.about}</p>
          <p className="pending">Not loaded yet. This section fills in when its public data source is added.</p>
        </section>
      ))}

      <section id="sources" className="section" aria-labelledby="sources-title">
        <h2 id="sources-title">
          <span className="num">{number(SECTIONS.length)}</span>
          Sources
        </h2>
        <ul className="sources">
          {s.sources.map((src) => (
            <li key={src.name}>
              <span>{src.attribution}</span>
              <span className="row-meta">
                captured {new Date(src.captured_at).toLocaleDateString("en-IE", { dateStyle: "medium" })}
              </span>
            </li>
          ))}
        </ul>
      </section>
    </article>
  );
}
