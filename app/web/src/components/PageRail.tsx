/** The page's sections as plain links, in a sticky column beside them on wide screens (hidden on narrow ones). */
export function PageRail({ links }: { links: { id: string; label: string }[] }) {
  return (
    <nav className="rail" aria-label="On this page">
      <ol>
        {links.map((l) => (
          <li key={l.id}>
            <a href={`#${l.id}`}>{l.label}</a>
          </li>
        ))}
      </ol>
    </nav>
  );
}
