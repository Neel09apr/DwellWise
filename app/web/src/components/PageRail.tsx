import { useEffect, useRef } from "react";

/** Mark one link as current, for sight (a class the CSS shares with :target-current) and for screen readers. */
function mark(links: HTMLAnchorElement[], current: Element | null) {
  for (const link of links) {
    const on = link === current;
    link.classList.toggle("target-current", on);
    if (on) link.setAttribute("aria-current", "true");
    else link.removeAttribute("aria-current");
  }
}

/**
 * The page's sections as plain links in a sticky column beside them (hidden on narrow screens). The link for the
 * section in view is marked: natively with scroll-target-group where the browser has it (aria-current synced when
 * scrolling ends), otherwise with an IntersectionObserver watching the line across the middle of the screen.
 */
export function PageRail({ links }: { links: { id: string; label: string }[] }) {
  const list = useRef<HTMLOListElement>(null);
  const ids = links.map((l) => l.id).join(" ");

  useEffect(() => {
    const ol = list.current;
    if (!ol) return;
    const anchors = [...ol.querySelectorAll("a")];
    if (CSS.supports("scroll-target-group: auto")) {
      const sync = () => mark(anchors, ol.querySelector("a:target-current"));
      sync();
      document.addEventListener("scrollend", sync);
      return () => document.removeEventListener("scrollend", sync);
    }
    // A link may point at a heading; watch the notice it heads, so the band across the middle always meets it.
    const linkFor = new Map<Element, HTMLAnchorElement>();
    for (const a of anchors) {
      const target = document.getElementById(decodeURIComponent(a.hash.slice(1)));
      if (target) linkFor.set(target.closest("section") ?? target, a);
    }
    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) if (entry.isIntersecting) mark(anchors, linkFor.get(entry.target) ?? null);
      },
      { rootMargin: "-50% 0px -50% 0px" },
    );
    for (const target of linkFor.keys()) observer.observe(target);
    return () => observer.disconnect();
  }, [ids]);

  return (
    <nav className="rail" aria-label="On this page">
      <ol ref={list}>
        {links.map((l) => (
          <li key={l.id}>
            <a href={`#${l.id}`}>{l.label}</a>
          </li>
        ))}
      </ol>
    </nav>
  );
}
