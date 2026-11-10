import { Link, Outlet } from "react-router-dom";

/** Header, page and the attribution every page must carry (CC BY 4.0). */
export function Layout() {
  return (
    <div className="shell">
      <a className="skip" href="#main">
        Skip to content
      </a>
      <header className="header">
        <Link to="/" className="brand">
          <img src="/mark-small.svg" alt="" width={22} height={22} />
          DwellWise
        </Link>
        <span className="header-tag">Pre-planning briefs · Ireland</span>
      </header>
      <main id="main" className="main">
        <Outlet />
      </main>
      <footer className="footer">
        <p>Boundaries © Tailte Éireann, CC BY 4.0.</p>
        <p>A non-statutory tool. Evidence describes towns, never a particular site. Not planning advice.</p>
      </footer>
    </div>
  );
}
