# DwellWise domain terms

The words the code, the API and the docs use. When a term changes meaning, change
it here first. The design is in [`docs/DESIGN.md`](docs/DESIGN.md).

**Place**: what a request is about: Ireland, one county, or one settlement.
Exactly one per request; naming a county and a settlement together is refused.
Resolved once, by `app/api/dwellwise_api/place.py`, before any feature runs.
_Avoid_: area, location, region (region is a CSO grouping of counties).

**County**: one of the 26 traditional counties, by its canonical upper-case name
(`KILDARE`). Councils map onto counties: Cork City and Cork County Councils are
both Cork; Fingal, South Dublin, Dun Laoghaire-Rathdown and Dublin City are all
Dublin. _Avoid_: local authority or council when the county is meant.

**Settlement**: a CSO settlement (a town or village with a CSO boundary), keyed
by its CSO code (`11016` is Navan). It always lies in one county, which a
resolved Place carries. Evidence describes the settlement, never a site in it.
_Avoid_: town as an identifier (names repeat: there are two Kells).

**Months**: the whole months a stats request covers, from `from` to `to`
(YYYY-MM, inclusive; by default the last 12 up to this month, at most 120).
Checked once by the API's `MonthRange` dependency; features receive `Months`.
_Avoid_: period, date range.

**Source**: one public dataset the pipeline loads (`planning`, `commencements`,
`prices`...), declared once in the pipeline's `SOURCES` with its attribution, and
registered in `dw.source` on every run. Each source owns its reader (`fetch`):
an ArcGIS `Layer`, the commencements CSV or the CSO's PxStat API. `/ready`
requires every registered source to have loaded within 48 hours. _Avoid_: feed, dataset as a code identifier.
