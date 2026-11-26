"""The shortlist without a database: one stated sort, its tie-breaks, the top five and one query."""

from datetime import date

from dwellwise_api.place import Place
from dwellwise_api.schemas import ShortlistTown
from dwellwise_api.shortlist import SORTS, TOP, rank, shortlist


def town(name, started=0, granted=0, near=0, median=None, **extra) -> ShortlistTown:
    return ShortlistTown(
        code=name.lower(), name=name, granted=granted, refused=0, pending=0, homes_started=started,
        protected_within_1km=near, price_area="X1" if median else None, median_price=median,
        price_month="2026-09" if median else None, **extra,
    )  # fmt: skip


TOWNS = [
    town("Athy", started=120, granted=64, near=2, median=285_000),
    town("Naas", started=640, granted=212, near=0, median=455_000),
    town("Kill", started=120, granted=90, near=0),
    town("Newbridge", started=410, granted=150, near=1, median=390_000),
]


def names(towns):
    return [t.name for t in towns]


def test_started_sorts_most_first_and_ties_go_to_more_granted():
    assert names(rank(TOWNS, "started")) == ["Naas", "Newbridge", "Kill", "Athy"]


def test_granted_protected_and_price_each_sort_their_own_way():
    assert names(rank(TOWNS, "granted")) == ["Naas", "Newbridge", "Kill", "Athy"]
    assert names(rank(TOWNS, "protected")) == ["Naas", "Kill", "Newbridge", "Athy"]
    assert names(rank(TOWNS, "price")) == ["Athy", "Newbridge", "Naas", "Kill"]  # no price: last


def test_only_the_top_five_are_kept():
    many = [town(f"T{i}", started=i) for i in range(9)]
    assert names(rank(many, "started")) == ["T8", "T7", "T6", "T5", "T4"] and TOP == 5


def test_every_sort_says_in_words_what_it_sorted_by():
    assert set(SORTS) == {"started", "granted", "protected", "price"}
    assert all(words for words, _key in SORTS.values())


class RowsConn:
    def __init__(self, rows):
        self.rows, self.queries, self.params = rows, 0, None

    def cursor(self, row_factory=None):
        conn = self

        class Cursor:
            def __enter__(self):
                return self

            def __exit__(self, *exc):
                return False

            def execute(self, _sql, params=None):
                conn.queries += 1
                conn.params = params

            def fetchall(self):
                return conn.rows

        return Cursor()


def test_a_shortlist_is_one_query_and_counts_every_town_in_the_county():
    conn = RowsConn([t.model_dump() for t in TOWNS] + [town(f"T{i}").model_dump() for i in range(3)])
    found = shortlist(conn, Place(county="KILDARE", counties=("KILDARE",)), "started", date(2026, 11, 26))
    assert conn.queries == 1 and conn.params["county"] == "KILDARE"
    assert found.towns_in_county == 7 and len(found.towns) == 5
    assert found.started_since == "2025-12" and found.applications_since == date(2021, 11, 26)
    assert conn.params["started_from"] == date(2025, 12, 1) and conn.params["started_to"] == date(2026, 12, 1)
    assert "not in DwellWise's data" in found.note
