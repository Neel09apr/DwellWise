import { Link, Outlet } from "react-router-dom";

/** Header, page and the attribution every page must carry (CC BY 4.0). */
export function Layout() {
  return (
    <>
      <header className="header">
        <a className="skip" href="#main">
          Skip to content
        </a>
        <Link to="/" className="brand">
          <img src="/mark-small.svg" alt="" width={24} height={24} />
          DwellWise
        </Link>
      </header>
      <main id="main" className="page">
        <Outlet />
      </main>
      <footer className="footer">
        Boundaries © Tailte Éireann, CC BY 4.0. A non-statutory tool, not planning advice.
      </footer>
    </>
  );
}
