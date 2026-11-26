/** Councils, their websites, and the cost form's fields: the parts of the calculator page that are plain data. */

export type Council = { name: string; county: string; url: string };

// The 31 local authorities. Development contribution schemes are on each council's own site; DwellWise
// links to it rather than copying rates that are indexed every year.
export const COUNCILS: Council[] = [
  { name: "Carlow County Council", county: "CARLOW", url: "https://carlow.ie/" },
  { name: "Cavan County Council", county: "CAVAN", url: "https://www.cavancoco.ie/" },
  { name: "Clare County Council", county: "CLARE", url: "https://www.clarecoco.ie/" },
  { name: "Cork City Council", county: "CORK", url: "https://www.corkcity.ie/" },
  { name: "Cork County Council", county: "CORK", url: "https://www.corkcoco.ie/" },
  { name: "Donegal County Council", county: "DONEGAL", url: "https://www.donegalcoco.ie/" },
  { name: "Dublin City Council", county: "DUBLIN", url: "https://www.dublincity.ie/" },
  { name: "Dún Laoghaire-Rathdown County Council", county: "DUBLIN", url: "https://www.dlrcoco.ie/" },
  { name: "Fingal County Council", county: "DUBLIN", url: "https://www.fingal.ie/" },
  { name: "South Dublin County Council", county: "DUBLIN", url: "https://www.sdcc.ie/" },
  { name: "Galway City Council", county: "GALWAY", url: "https://www.galwaycity.ie/" },
  { name: "Galway County Council", county: "GALWAY", url: "https://www.galway.ie/" },
  { name: "Kerry County Council", county: "KERRY", url: "https://www.kerrycoco.ie/" },
  { name: "Kildare County Council", county: "KILDARE", url: "https://www.kildarecoco.ie/" },
  { name: "Kilkenny County Council", county: "KILKENNY", url: "https://www.kilkennycoco.ie/" },
  { name: "Laois County Council", county: "LAOIS", url: "https://laois.ie/" },
  { name: "Leitrim County Council", county: "LEITRIM", url: "https://www.leitrim.ie/" },
  { name: "Limerick City and County Council", county: "LIMERICK", url: "https://www.limerick.ie/" },
  { name: "Longford County Council", county: "LONGFORD", url: "https://www.longfordcoco.ie/" },
  { name: "Louth County Council", county: "LOUTH", url: "https://www.louthcoco.ie/" },
  { name: "Mayo County Council", county: "MAYO", url: "https://www.mayo.ie/" },
  { name: "Meath County Council", county: "MEATH", url: "https://www.meath.ie/" },
  { name: "Monaghan County Council", county: "MONAGHAN", url: "https://monaghan.ie/" },
  { name: "Offaly County Council", county: "OFFALY", url: "https://www.offaly.ie/" },
  { name: "Roscommon County Council", county: "ROSCOMMON", url: "https://www.roscommoncoco.ie/" },
  { name: "Sligo County Council", county: "SLIGO", url: "https://www.sligococo.ie/" },
  { name: "Tipperary County Council", county: "TIPPERARY", url: "https://www.tipperarycoco.ie/" },
  { name: "Waterford City and County Council", county: "WATERFORD", url: "https://waterfordcouncil.ie/" },
  { name: "Westmeath County Council", county: "WESTMEATH", url: "https://www.westmeathcoco.ie/" },
  { name: "Wexford County Council", county: "WEXFORD", url: "https://www.wexfordcoco.ie/" },
  { name: "Wicklow County Council", county: "WICKLOW", url: "https://www.wicklow.ie/" },
];

/** The councils for a county (Dublin has four, Cork and Galway two); every council when the county is unknown. */
export function councilsFor(county: string | null | undefined): [Council, ...Council[]] {
  const key = (county ?? "").trim().toUpperCase();
  const found = COUNCILS.filter((c) => c.county === key);
  return (found.length ? found : COUNCILS) as [Council, ...Council[]]; // never empty: COUNCILS has 31
}

export type CostForm = {
  homes: string;
  floor_area_m2: string;
  build_cost_per_m2: string;
  contribution: string;
  contribution_basis: "per_m2" | "per_home";
  fees_pct: string;
  contingency_pct: string;
  finance_rate_pct: string;
  finance_months: string;
  land: string;
};

/** Every field starts empty: the figures are the user's, never a default (DESIGN.md §16, M11). */
export const EMPTY_FORM: CostForm = {
  homes: "",
  floor_area_m2: "",
  build_cost_per_m2: "",
  contribution: "",
  contribution_basis: "per_m2",
  fees_pct: "",
  contingency_pct: "",
  finance_rate_pct: "",
  finance_months: "",
  land: "",
};

/** The query string for /v1/costs. Land is left out when empty; the API checks every other figure. */
export function costQuery(form: CostForm): string {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(form)) {
    const text = value.trim().replace(/,/g, "");
    if (key === "land" && text === "") continue;
    params.set(key, text);
  }
  return params.toString();
}

export const DRAFT_KEY = "dwellwise.costs.v1";

/** The user's last figures, kept in this browser only; empty when storage is blocked or holds something else. */
export function loadDraft(storage: Pick<Storage, "getItem"> | undefined): CostForm {
  try {
    const saved = JSON.parse(storage?.getItem(DRAFT_KEY) ?? "null") as Partial<CostForm> | null;
    if (!saved || typeof saved !== "object") return EMPTY_FORM;
    const form = { ...EMPTY_FORM };
    for (const key of Object.keys(EMPTY_FORM) as (keyof CostForm)[]) {
      if (typeof saved[key] === "string") (form as Record<string, string>)[key] = saved[key] as string;
    }
    if (form.contribution_basis !== "per_home") form.contribution_basis = "per_m2";
    return form;
  } catch {
    return EMPTY_FORM;
  }
}

export function saveDraft(storage: Pick<Storage, "setItem"> | undefined, form: CostForm): void {
  try {
    storage?.setItem(DRAFT_KEY, JSON.stringify(form));
  } catch {
    // storage blocked or full: the figures simply are not remembered
  }
}
