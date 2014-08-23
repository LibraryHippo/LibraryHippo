#!/usr/bin/env python

import gael.testing
gael.testing.add_appsever_import_paths()

from data import Hold
from fakes import MyCard, MyLibrary


class ThingToRank:
    def __init__(self, status):
        self.status = status

    def __repr__(self):
        return 'ThingToRank(' + repr(self.status) + ')'


equal_statuses = (
    (Hold.READY, Hold.READY),
    (Hold.IN_TRANSIT, Hold.IN_TRANSIT),
    (Hold.CHECK_SHELVES, Hold.CHECK_SHELVES),
    ((1, 2), (1, 2)),
    ((11, 100), (11, 100)),
    ((3, 3), (3, 3)),
    ("something I've never heard of", "something I've never heard of"),
)


# pairs of inequal statuses - higher priority first
# e.g., Hold.READY is higher priority (and should compare as "less than"
# Hold.IN_TRANSIT
inequal_statuses = (
    (Hold.READY, Hold.IN_TRANSIT),
    (Hold.READY, Hold.CHECK_SHELVES),
    (Hold.IN_TRANSIT, Hold.CHECK_SHELVES),
    (Hold.READY, (1, 2)),
    (Hold.IN_TRANSIT, (11, 20)),
    (Hold.CHECK_SHELVES, (3, 19)),
    ((1, 2), (2, 3)),
    ((2, 100), (11, 100)),
    (Hold.CHECK_SHELVES, "something"),
    ("something I've never heard of", (1, 2)),
    ("something I've never heard of", "something else I've never heard of"),
)


def test__cmp__equal_statuses__compare_same():
    def check(first_status, second_status):
        print 'first_status =', first_status, 'second_status =', second_status

        this = Hold(MyLibrary(), MyCard())
        this.status = first_status
        other = Hold(MyLibrary(), MyCard())
        other.status = second_status

        assert 0 == cmp(this, other)
        assert 0 == cmp(other, this)

    for s1, s2 in equal_statuses:
        yield check, s1, s2


def test__cmp__inequal_statuses__correctly_ordered():
    def check(first_status, second_status):
        print 'first_status =', first_status, 'second_status =', second_status
        this = Hold(MyLibrary(), MyCard())
        this.status = first_status
        other = Hold(MyLibrary(), MyCard())
        other.status = second_status

        assert cmp(this, other) < 0
        assert cmp(other, this) > 0

    for s1, s2 in inequal_statuses:
        yield check, s1, s2


def test__status_text__ready__correctly_rendered():
    h = Hold(MyLibrary(), MyCard())
    h.status = Hold.READY
    assert h.status_text() == 'Ready'


def test__status_text__in_transit__correctly_rendered():
    h = Hold(MyLibrary(), MyCard())
    h.status = Hold.IN_TRANSIT
    assert h.status_text() == 'In transit'


def test__status_text__unknown_status__correctly_rendered():
    h = Hold(MyLibrary(), MyCard())
    h.status = 'something I made up'
    assert h.status_text() == 'something I made up'


def test__status_text__position__correctly_rendered():
    h = Hold(MyLibrary(), MyCard())
    h.status = (3, 17)
    assert h.status_text() == '3 of 17'
