import csv
import io

from dwellwise_pipeline.sources import SOURCES
from dwellwise_pipeline.sources.commencements import check, parse

SOURCE = SOURCES["commencements"]
HEADER = [
    "CN_Number",
    "CN_Proposed_use_of_building",
    "CN_Date_Submitted_or_Received",
    "CN_Commencement_Date",
    "CN_Proposed_end_date",
    "CN_Units_for_phase",
    "CN_Total_Number_of_Dwelling_Units",
    "CN_Planning_Permission_Number",
    "CN_Project_Name",
    "CN_Street",
    "CN_Eircode",
    "CN_LAT",
    "CN_LNG",
    "CCC_Number",
    "CCC_Units_Completed",
    "LocalAuthority",
]


def notice(
    number="CN1",
    use="^1_residential_dwellings^",
    submitted="2026-11-23 09:00:00",
    homes="9",
    name="Bunclody Woods",
    ccc="",
    ccc_homes="",
    authority="Carlow County Council",
    lat="52.65",
):
    return {
        "CN_Number": number,
        "CN_Proposed_use_of_building": use,
        "CN_Date_Submitted_or_Received": submitted,
        "CN_Commencement_Date": "2026-12-01",
        "CN_Proposed_end_date": "2027-10-01",
        "CN_Units_for_phase": homes,
        "CN_Total_Number_of_Dwelling_Units": "27",
        "CN_Planning_Permission_Number": "23/68",
        "CN_Project_Name": name,
        "CN_Street": "1 Main Street",
        "CN_Eircode": "R93 X0X0",
        "CN_LAT": lat,
        "CN_LNG": "-6.66",
        "CCC_Number": ccc,
        "CCC_Units_Completed": ccc_homes,
        "LocalAuthority": authority,
    }


def lines(*rows):
    out = io.StringIO()
    writer = csv.DictWriter(out, HEADER)
    writer.writeheader()
    writer.writerows(rows)
    return io.StringIO(out.getvalue())


def test_one_feature_per_residential_notice_since_2020():
    c = parse(
        lines(
            notice(),
            notice(),  # two buildings of one notice
            notice("CN2", use="^4_office^"),
            notice("CN3", submitted="2019-12-31 23:00:00"),
            notice(""),  # the file has one row with no number
        )
    )
    assert [f["properties"]["notice_number"] for f in c["features"]] == ["CN1"]
    p = c["features"][0]["properties"]
    assert (p["submitted"], p["commenced"], p["homes"], p["scheme_homes"]) == (
        "2026-11-23",
        "2026-12-01",
        9,
        27,
    )
    assert c["features"][0]["geometry"] == {"type": "Point", "coordinates": [-6.66, 52.65]}


def test_addresses_are_never_kept_and_small_notices_stay_unnamed():
    c = parse(lines(notice(), notice("CN2", homes="1", name="Murphy family home")))
    kept = {k for f in c["features"] for k in f["properties"]}
    assert not kept & {"CN_Street", "CN_Eircode", "street", "eircode"}
    names = {f["properties"]["notice_number"]: f["properties"]["project_name"] for f in c["features"]}
    assert names == {"CN1": "Bunclody Woods", "CN2": None}


def test_completed_homes_count_each_certificate_once():
    c = parse(
        lines(
            notice(ccc="CCC1", ccc_homes="3"),
            notice(ccc="CCC1", ccc_homes="3"),
            notice(ccc="CCC2", ccc_homes="2"),
        )
    )
    assert c["features"][0]["properties"]["homes_completed"] == 5


def test_notices_without_coordinates_are_counted_not_loaded():
    c = parse(lines(notice(lat="")))
    assert (c["features"], c["no_location"]) == ([], 1)


def test_councils_named_differently_still_get_a_county():
    c = parse(lines(notice(authority="D\u00fan-Laoghaire Rathdown County Council")))
    assert check(c) == []
    assert SOURCE.transform(c)[0]["county"] == "DUBLIN"
    assert check(parse(lines(notice(authority="Atlantis County Council")))) == [
        "unknown local authorities: Atlantis County Council"
    ]


def test_an_impossible_commencement_date_rejects_the_run():
    c = parse(lines(notice()))
    c["features"][0]["properties"]["commenced"] = "2075-01-01"
    assert "commencement date missing or outside" in check(c)[0]
