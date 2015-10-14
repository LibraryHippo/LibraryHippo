#!/usr/bin/env python

import datetime

from fakes import MyCard
from fakes import MyLibrary

import gael.testing
gael.testing.add_appsever_import_paths()

from data import Hold
from data import Item
from data import CardInfo
from data import CardStatus


def test__holds_sort__all_ready__sorted_by_title():
    l = MyLibrary()
    c = MyCard()
    holds = [
        Hold(l, c),
        Hold(l, c),
        Hold(l, c)
    ]
    holds[0].status = Hold.READY
    holds[0].title = 'B'
    holds[1].status = Hold.READY
    holds[1].title = 'A'
    holds[2].status = Hold.READY
    holds[2].title = 'C'

    holds.sort()
    assert ['A', 'B', 'C'] == [h.title for h in holds]


def test__holds_sort__rwl_holds_with_integer_status__sorted_by_status():
    l = MyLibrary()
    c = MyCard()
    holds = [
        Hold(l, c),
        Hold(l, c),
        Hold(l, c)
    ]
    holds[0].status = 15
    holds[1].status = 2
    holds[2].status = 7
    for i in range(len(holds)):
        holds[i].title = chr(i + ord('A'))
    holds.sort()
    assert ['B', 'C', 'A'] == [h.title for h in holds]


def test__holds_sort__holds_with_integer_status_some_frozen__frozen_sorts_last():
    l = MyLibrary()
    c = MyCard()
    holds = [
        Hold(l, c),
        Hold(l, c),
        Hold(l, c)
    ]
    holds[0].status = 1
    holds[1].status = 3
    holds[2].status = 2
    holds[2].freeze()
    for i in range(len(holds)):
        holds[i].title = chr(i + ord('A'))
    holds.sort()
    assert ['A', 'B', 'C'] == [h.title for h in holds]


def test__holds_sort__mixed_rwl_wpl_holds__sort_okay():
    l = MyLibrary()
    c = MyCard()
    holds = [
        Hold(l, c),
        Hold(l, c),
        Hold(l, c),
        Hold(l, c)
    ]
    holds[0].status = 15
    holds[1].status = (2, 9)
    holds[2].status = (7, 31)
    holds[3].status = 1
    for i in range(len(holds)):
        holds[i].title = chr(i + ord('A'))
    holds.sort()
    assert ['D', 'B', 'C', 'A'] == [h.title for h in holds]


def test__items_sort__same_date__sorted_by_name():
    l = MyLibrary()
    c = MyCard()
    items = [
        Item(l, c),
        Item(l, c),
        Item(l, c)
    ]
    items[0].status = datetime.date(2009, 9, 7)
    items[0].title = 'B'
    items[1].status = datetime.date(2009, 9, 7)
    items[1].title = 'A'
    items[2].status = datetime.date(2009, 9, 7)
    items[2].title = 'C'

    items.sort()
    assert ['A', 'B', 'C'] == [i.title for i in items]


def test__holds_sort__delayed_hold__sorts_last():
    l = MyLibrary()
    c = MyCard()
    holds = [
        Hold(l, c),
        Hold(l, c),
        Hold(l, c)
    ]
    holds[0].title = 'A'
    holds[0].status = 15
    holds[1].title = 'B'
    holds[1].status = Hold.DELAYED
    holds[2].title = 'C'
    holds[2].status = (7, 31)

    holds.sort()
    assert ['C', 'A', 'B'] == [h.title for h in holds]


def test__cardinfo_constructor__remembers_info():
    c = CardInfo('My Public Library', 'Name', 'hippos are cool')
    assert 'hippos are cool' == c.message
    assert 'My Public Library' == c.library_name
    assert 'Name' == c.patron_name


def test__cardstatus__add_failure__adds_good_info():
    card = MyCard()
    card_status = CardStatus(card)
    card_status.add_failure()

    assert card_status.info[0].library_name == 'My Public Library'
    assert card_status.info[0].patron_name == 'Name'
    assert card_status.info[0].message == 'Failed to check card. <a href="/about#check_failed">Why?</a>'
