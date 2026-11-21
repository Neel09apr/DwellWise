/** Links to Uisce Éireann's wastewater treatment capacity registers, one page per county. */

const REGISTER =
  "https://www.water.ie/connections/developer-services/capacity-registers/wastewater-treatment-capacity-register";

/** Counties whose register is split across pages. Dublin's pages only load with a trailing slash. */
const SPLIT: Record<string, { label: string; page: string }[]> = {
  DUBLIN: [
    { label: "Dublin", page: "Dublin/" },
    { label: "Fingal", page: "Fingal/" },
  ],
  CORK: [
    { label: "Cork County", page: "cork" },
    { label: "Cork City", page: "cork-city" },
  ],
  GALWAY: [
    { label: "Galway County", page: "galway" },
    { label: "Galway City", page: "galway-city" },
  ],
};

export type RegisterLink = { label: string; url: string };

/** The register page(s) covering a county; the national index when the county is unknown. */
export function registerLinks(county: string | null | undefined): RegisterLink[] {
  if (!county) return [{ label: "All county registers", url: REGISTER }];
  const key = county.trim().toUpperCase();
  const pages = SPLIT[key] ?? [{ label: key.charAt(0) + key.slice(1).toLowerCase(), page: key.toLowerCase() }];
  return pages.map((p) => ({ label: p.label, url: `${REGISTER}/${p.page}` }));
}
