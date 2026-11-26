import type { Figure } from "../overviewText";

/** Headline figures, each a link to the section it comes from. Nothing shows until a figure has loaded. */
export function FigureStrip({ figures }: { figures: Figure[] }) {
  if (figures.length === 0) return null;
  return (
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
  );
}
