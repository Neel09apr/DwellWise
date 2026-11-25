from dataclasses import replace

from dwellwise_pipeline.sources import SOURCES
from dwellwise_pipeline.sources.commencements import routing_key
from dwellwise_pipeline.sources.prices import TABLES, check, fetch, parse, query
from dwellwise_pipeline.validate import validate


def cube(months=("201912", "202609"), areas=("-", "C15"), area_dim="C03349V04063"):
    """A tiny HPM04-shaped JSON-stat cube: measure x month x status x area x stage x buyer."""
    dims = ["STATISTIC", "TLIST(M1)", "C03346V04033", area_dim, "C03341V04028", "C03344V04031"]
    cats = [["HPM04C01", "HPM04C03", "HPM04C04"], list(months), ["-", "01"], list(areas), ["02"], ["-"]]
    values = []
    for m in cats[0]:
        for _month in cats[1]:
            for status in cats[2]:
                for _area in cats[3]:
                    base = {"HPM04C01": 38, "HPM04C03": 431_250.4, "HPM04C04": 420_000}[m]
                    values.append(None if (status == "01" and m != "HPM04C01") else base)
    labels = {"-": "All", "C15": "C15: Navan"}
    return {
        "id": dims,
        "size": [len(c) for c in cats],
        "dimension": {
            d: {"category": {"index": c, **({"label": labels} if d == area_dim else {})}}
            for d, c in zip(dims, cats, strict=True)
        },
        "value": values,
    }


def test_a_cube_becomes_one_row_per_area_month_and_status_from_2020():
    rows = [f["properties"] for f in parse("HPM04", cube())]
    assert {(r["code"], r["month"], r["status"]) for r in rows} == {
        ("C15", "2026-09-01", "all"),
        ("C15", "2026-09-01", "new"),
    }  # 2019 dropped; HPM04's "All" row dropped (HPM05 has the national figure)
    by_status = {r["status"]: r for r in rows}
    assert by_status["all"] == {
        "kind": "eircode", "code": "C15", "name": "Navan", "month": "2026-09-01", "status": "all",
        "sales": 38, "median": 420_000, "mean": 431_250,
    }  # fmt: skip
    assert (by_status["new"]["sales"], by_status["new"]["median"]) == (38, None)  # suppressed stays null


def test_a_row_with_every_value_suppressed_is_dropped():
    c = cube()
    c["value"] = [None] * len(c["value"])
    assert parse("HPM04", c) == []


def test_the_query_asks_only_for_executed_household_sales():
    q = query("HPM04")["params"]
    assert q["extension"]["matrix"] == "HPM04"
    assert q["dimension"]["C03341V04028"] == {"category": {"index": ["02"]}}  # executions, not filings
    assert q["dimension"]["STATISTIC"]["category"]["index"] == ["HPM04C01", "HPM04C03", "HPM04C04"]


def test_fetch_reads_both_tables():
    asked = []

    def post(_url, body):
        table = body["params"]["extension"]["matrix"]
        asked.append(table)
        return cube(area_dim=TABLES[table]["area"])

    fetch("https://ws.cso.ie/public/api.jsonrpc", post=post)
    assert asked == ["HPM04", "HPM05"]


def test_a_statistics_source_needs_no_geometry_but_a_map_source_does():
    collection = {"features": parse("HPM04", cube())}
    validate(replace(SOURCES["prices"], min_rows=1, check=None), collection, previous_rows=None)
    mapped = replace(SOURCES["prices"], min_rows=1, check=None, geometry=True)
    try:
        validate(mapped, collection, previous_rows=None)
    except ValueError as exc:
        assert "rows without geometry" in str(exc)
    else:
        raise AssertionError("a source with geometry must reject rows without it")


def test_missing_areas_old_data_or_implausible_prices_reject_the_run():
    rows = parse("HPM04", cube(months=("202001",)))
    rows[0]["properties"]["median"] = 99
    problems = check({"features": rows})
    assert "1 Eircode areas, expected about 139" in problems
    assert any("older than six months" in p for p in problems)
    assert any("outside 10,000 to 5,000,000" in p for p in problems)


def test_only_the_routing_key_of_a_valid_eircode_is_kept():
    assert routing_key("c15 x2y4") == "C15"
    assert routing_key("D6W XY12") == "D6W"
    assert routing_key("not given") is None
    assert routing_key("C15") is None  # a routing key alone is not an Eircode
