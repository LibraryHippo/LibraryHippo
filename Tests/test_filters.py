#!/usr/bin/env python

import datetime
import utils.filters


def test__duedate__may_first__rendered_correctly():
    assert '1&nbsp;May (Friday)' == utils.filters.duedate(datetime.date(2009, 5, 1))


def test__duedate__may_nineteenth__rendered_correctly():
    assert '19&nbsp;May (Tuesday)' == utils.filters.duedate(datetime.date(2009, 5, 19))


def test__duedate__string_type__left_alone():
    assert '2009-06-13 +1 HOLD' == utils.filters.duedate('2009-06-13 +1 HOLD')


def test__link__no_url__leaves_plain():
    assert 'title' == utils.filters.link('title', None)


def test__link__url__hrefed():
    assert '<a href="http://123.com/title">title</a>' == utils.filters.link('title', 'http://123.com/title')


def test__elapsed__no_days__writes_hours():
    assert '21 hours' == utils.filters.elapsed(datetime.timedelta(hours=21, minutes=13))


def test__elapsed__one_day__writes_one_day():
    assert '1 day' == utils.filters.elapsed(datetime.timedelta(days=1, hours=3))


def test__elapsed__two_days__writes_two_days():
    assert '2 days' == utils.filters.elapsed(datetime.timedelta(days=2, hours=17, minutes=13))
