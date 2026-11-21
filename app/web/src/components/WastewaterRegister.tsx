import { registerLinks } from "./wastewaterText";

/** Brief section 01 (F3), for now a link: Uisce Éireann's terms do not allow republishing its registers. */
export function WastewaterRegister({ name, county }: { name: string; county: string | null | undefined }) {
  const links = registerLinks(county);

  return (
    <div className="section-body">
      <p>
        Look up {name} in Uisce Éireann's wastewater treatment capacity register:{" "}
        {links.map((l, i) => (
          <span key={l.url}>
            {i > 0 && " · "}
            <a href={l.url}>{l.label}</a>
          </span>
        ))}
        .
      </p>
      <p className="note">
        The register rates spare capacity at the treatment plant serving each settlement. It covers the plant, not the
        sewer network. A rating with no spare capacity means a Confirmation of Feasibility from Uisce Éireann and
        possibly an upgrade: time and cost, not a refusal. DwellWise links to the register rather than copying it,
        because Uisce Éireann's website terms do not allow its content to be republished.
      </p>
    </div>
  );
}
