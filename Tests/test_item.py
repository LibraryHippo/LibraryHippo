#!/usr/bin/env python

import datetime

import gael.testing
gael.testing.add_appsever_import_paths()

from data import Item

from fakes import MyCard, MyLibrary

equal_statuses = (
    (datetime.date(2009,4,5), datetime.date(2009,4,5)),
    (datetime.date(2009,5,1), datetime.date(2009,5,1)),
    ('2009-04-01 +1 HOLD', '2009-04-01 +1 HOLD'),
    )

# pairs of inequal statuses - earlier due dates first
inequal_statuses = (
    (datetime.date(2009,4,5), datetime.date(2009,5,1)),
    (datetime.date(2009,4,5), '2009-04-05 +1 HOLD'),
    ('2009-04-01 +1 HOLD', '2009-07-18 +1 HOLD'),
    )

def test__cmp__equal_statuses__compare_same():
    def check(first_status, second_status):
        print 'first_status =', first_status, 'second_status =', second_status

        this = Item(MyLibrary(), MyCard())
        this.status = first_status
        other = Item(MyLibrary(), MyCard())
        other.status = second_status

        assert 0 == cmp(this, other)
        assert 0 == cmp(other, this)

    for s1, s2 in equal_statuses:
        yield check, s1, s2

def test__cmp__inequal_statuses__correctly_ordered():
    def check(first_status, second_status):
        print 'first_status =', first_status, 'second_status =', second_status
        this = Item(MyLibrary(), MyCard())
        this.status = first_status
        other = Item(MyLibrary(), MyCard())
        other.status = second_status

        assert cmp(this, other) < 0
        assert cmp(other, this) > 0

    for s1, s2 in inequal_statuses:
        yield check, s1, s2

