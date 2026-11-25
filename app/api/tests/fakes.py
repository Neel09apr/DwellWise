"""An in-memory gazetteer for apps and features tested without a database."""

from dwellwise_api.place import Gazetteer, Places

GAZETTEER = Gazetteer(
    counties=("CORK", "KILDARE", "MAYO", "MEATH"),
    settlements={"1": ("Athy", "KILDARE"), "2": ("Athboy", "MEATH"), "3": ("Castlebar", "MAYO")},
)


def memory_places(clock=None) -> Places:
    loads = []

    def load(_conn):
        loads.append(1)
        return GAZETTEER

    places = Places(load, clock) if clock else Places(load)
    places.loads = loads  # how many times the gazetteer was read
    return places
