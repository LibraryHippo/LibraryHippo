#!/usr/bin/env python

import datetime
import pytest

from data import Item
from fakes import MyCard, MyLibrary


@pytest.mark.parametrize("first_status,second_status", [
    (datetime.date(2009, 4, 5), datetime.date(2009, 4, 5)),
    (datetime.date(2009, 5, 1), datetime.date(2009, 5, 1)),
    ('2009-04-01 +1 HOLD', '2009-04-01 +1 HOLD'),
])
def test__cmp__equal_statuses__compare_same(first_status, second_status):
    this = Item(MyLibrary(), MyCard())
    this.status = first_status
    other = Item(MyLibrary(), MyCard())
    other.status = second_status

    assert 0 == cmp(this, other)
    assert 0 == cmp(other, this)


@pytest.mark.parametrize("first_status,second_status", [
    # pairs of inequal statuses - earlier due dates first
    (datetime.date(2009, 4, 5), datetime.date(2009, 5, 1)),
    (datetime.date(2009, 4, 5), '2009-04-05 +1 HOLD'),
    ('2009-04-01 +1 HOLD', '2009-07-18 +1 HOLD'),
])
def test__cmp__inequal_statuses__correctly_ordered(first_status, second_status):
    this = Item(MyLibrary(), MyCard())
    this.status = first_status
    other = Item(MyLibrary(), MyCard())
    other.status = second_status

    assert cmp(this, other) < 0
    assert cmp(other, this) > 0
