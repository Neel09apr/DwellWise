import { Link } from "react-router-dom";

import { Breadcrumbs } from "../components/Breadcrumbs";

export function NotFoundPage() {
  return (
    <>
      <Breadcrumbs trail={[{ label: "Ireland", to: "/" }, { label: "Not found" }]} />
      <header className="page-head">
        <h1>There is no page here.</h1>
        <p>
          <Link to="/">Find a town</Link> or browse by county.
        </p>
      </header>
    </>
  );
}
