#!/usr/bin/env python

import datetime

from fakes import MyCard
from fakes import MyLibrary
from fakes import StoppedClock

from data import Hold
from data import Item
from data import CardInfo
from data import CardStatus

import gael.testing
gael.testing.add_appsever_import_paths()

import libraryhippo  # noqa E402 - module level import not at top of file


def setup_module(module):
    libraryhippo.clock = StoppedClock(datetime.datetime(2010, 2, 1))


def pytest_funcarg__card(request):
    """Sort of like setup - will provide a card argument to tests that want it"""
    return MyCard()


def pytest_funcarg__library(request):
    """Sort of like setup - will provide a library argument to tests that want it"""
    return MyLibrary()


def pytest_funcarg__status(request):
    """Sort of like setup - will provide a status argument to tests that want it"""
    card = request.getfuncargvalue('card')
    return CardStatus(card)


def test__build_template__card_expires_in_one_week__message_added_to_template(status):

    status.expires = datetime.date(2010, 2, 8)
    family = None

    template_values = libraryhippo.build_template([status], family)
    assert 1 == len(template_values['info'])
    assert 'card expires on 8&nbsp;February (Monday)' == template_values['info'][0].message


def test__build_template__card_expires_in_eight_days__no_message_added_to_template(status):
    status.expires = datetime.date(2010, 2, 9)
    family = None

    template_values = libraryhippo.build_template([status], family)
    assert 0 == len(template_values['info'])


def test__build_template__card_expired__expired_message_added_to_template_as_yyyymmdd(status):
    # because people may leave their cards expired for years, and it'd be nice to tell
    status.expires = datetime.date(2010, 1, 15)
    family = None

    template_values = libraryhippo.build_template([status], family)
    assert 1 == len(template_values['info'])
    assert template_values['info'][0].message == 'card expired on 2010-01-15'


def test__build_template__card_expires_today__expires_today_message__added_to_template(status):
    status.expires = datetime.date(2010, 2, 1)
    family = None

    template_values = libraryhippo.build_template([status], family)
    assert 1 == len(template_values['info'])
    assert template_values['info'][0].message == 'card expires today'


def test__build_template__card_expires_today__sets_should_notify(status):
    status.expires = datetime.date(2010, 2, 1)
    family = None

    template_values = libraryhippo.build_template([status], family)
    assert template_values['should_notify']


def test__build_template__card_expires_in_one_week__sets_should_notify(status):
    status.expires = datetime.date(2010, 2, 8)
    family = None

    template_values = libraryhippo.build_template([status], family)
    assert template_values['should_notify']


def test__build_template__card_expired__does_not_set_should_notify(status):
    status.expires = datetime.date(2010, 1, 14)
    family = None

    template_values = libraryhippo.build_template([status], family)
    assert not template_values['should_notify']


def test__build_template__no_messges_no_holds_ready_no_items_due__does_not_set_should_notify(status, library, card):
    item = Item(library, card)
    item.status = datetime.date(2010, 2, 10)
    status.items = [item]

    hold = Hold(library, card)
    hold.status = (3, 5)
    status.holds = [hold]

    family = None

    template_values = libraryhippo.build_template([status], family)
    assert not template_values['should_notify']


def test__build_template__one_messge_no_holds_ready_no_items_due__sets_should_notify(status, library, card):
    item = Item(library, card)
    item.status = datetime.date(2010, 2, 10)
    status.items = [item]

    hold = Hold(library, card)
    hold.status = (3, 5)
    status.holds = [hold]

    status.info = [CardInfo(status.library_name, status.patron_name, 'blah')]

    family = None

    template_values = libraryhippo.build_template([status], family)
    assert template_values['should_notify']


def test__build_template__no_messges_one_hold_ready_no_items_due__sets_should_notify(status, library, card):
    item = Item(library, card)
    item.status = datetime.date(2010, 2, 10)
    status.items = [item]

    hold = Hold(library, card)
    hold.status = Hold.READY
    status.holds = [hold]

    family = None

    template_values = libraryhippo.build_template([status], family)
    assert template_values['should_notify']


def test__build_template__no_messges_no_holds_ready_one_item_due__sets_should_notify(status, library, card):
    item = Item(library, card)
    item.status = datetime.date(2010, 2, 2)
    status.items = [item]

    hold = Hold(library, card)
    hold.status = (3, 5)
    status.holds = [hold]

    family = None

    template_values = libraryhippo.build_template([status], family)
    assert template_values['should_notify']


def test__build_template__one_messge_card_expired__ends_up_with_two_messages(status, library, card):
    status.info = [CardInfo(status.library_name, status.patron_name, 'blah')]
    status.expires = datetime.date(2010, 1, 14)

    family = None

    template_values = libraryhippo.build_template([status], family)
    assert 2 == len(template_values['info'])


def test__build_template__no_message__does_not_set_error(status, library, card):
    family = None

    template_values = libraryhippo.build_template([status], family)
    assert not template_values['error']


def test__build_template__one_message__should_set_error(status, library, card):
    status.info = [CardInfo(status.library_name, status.patron_name, 'blah')]

    family = None

    template_values = libraryhippo.build_template([status], family)
    assert template_values['error']


def test__build_tempate__hold_expires_soon__expires_added_to_status_note(status, library, card):
    family = None

    hold = Hold(library, card)
    hold.status = (3, 5)
    hold.expires = datetime.date(2010, 2, 28)
    status.holds = [hold]

    template_values = libraryhippo.build_template([status], family)
    assert 'expires on 28&nbsp;February (Sunday)' in template_values['holds_not_ready'][0].status_notes


def test__build_tempate__hold_expires_in_a_long_time__expires_not_added_to_status_note(status, library, card):
    family = None

    hold = Hold(library, card)
    hold.status = (3, 5)
    hold.expires = datetime.date(2010, 7, 13)
    status.holds = [hold]

    template_values = libraryhippo.build_template([status], family)
    assert [] == template_values['holds_not_ready'][0].status_notes
