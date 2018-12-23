#!/usr/bin/env python

import pytest

from datetime import datetime, timedelta
from utils.times import WaterlooTimeZone


@pytest.mark.parametrize("dt,offset", [
    (datetime(2009, 8, 22, 15, 30, 19), -4),
    (datetime(2010, 1, 1), -5),
    (datetime(2010, 3, 14, 1), -5),
    (datetime(2010, 3, 14, 3), -4),
    (datetime(2010, 11, 7, 1), -4),
    (datetime(2010, 11, 7, 3), -5),
])
def test__utcoffset__from_date__is_correct(dt, offset):
    tz = WaterlooTimeZone()
    assert(timedelta(hours=offset) == tz.utcoffset(dt))
