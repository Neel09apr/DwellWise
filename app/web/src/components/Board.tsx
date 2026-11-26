import type { ReactNode } from "react";

import type { Figure } from "../overviewText";

const DISCLAIMER = "Describes places as a whole, never a particular site, and is not planning advice.";

/** The notice board: the place in heavy caps and its record as the notice's prescribed lines, each a link. */
export function Board({
  title,
  place,
  figures,
  foot,
}: {
  title: string;
  place: ReactNode;
  figures: Figure[];
  foot?: string;
}) {
  return (
    <header className="board">
      <h1>{title}</h1>
      <p className="board-place">{place}</p>
      {figures.length > 0 && (
        <ul className="board-lines" aria-label="The record">
          {figures.map((f) => (
            <li key={f.id}>
              <a href={`#${f.id}`}>
                <strong>{f.value}</strong> {f.label}
                <span className="board-detail">{f.detail}</span>
              </a>
            </li>
          ))}
        </ul>
      )}
      <p className="board-foot">
        {foot ?? "Compiled from public records."} {DISCLAIMER}
      </p>
    </header>
  );
}
