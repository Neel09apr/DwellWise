import { Link, NavLink, Outlet } from "react-router-dom";

/** Header, page and the attribution every page must carry (CC BY 4.0). */
export function Layout() {
  return (
    <div className="shell">
      <a className="skip" href="#main">
        Skip to content
      </a>
      <header className="header">
        <Link to="/" className="brand">
          <img src="/mark-small.svg" alt="" width={38} height={24} />
          DwellWise
        </Link>
        <nav className="header-nav" aria-label="Main">
          <NavLink to="/" end>
            Towns
          </NavLink>
          <NavLink to="/costs">Cost estimate</NavLink>
        </nav>
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
