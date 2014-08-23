#!/usr/bin/env python

import gael.testing
gael.testing.add_appsever_import_paths()

from datetime import datetime, timedelta
from utils.times import WaterlooTimeZone


def test__utcoffset__from_date__is_correct():
    def check(dt, offset):
        tz = WaterlooTimeZone()
        assert(timedelta(hours=offset) == tz.utcoffset(dt))

    for dt, offset in (
        (datetime(2009, 8, 22, 15, 30, 19), -4),
        (datetime(2010, 1, 1), -5),
        (datetime(2010, 3, 14, 1), -5),
        (datetime(2010, 3, 14, 3), -4),
        (datetime(2010, 11, 7, 1), -4),
        (datetime(2010, 11, 7, 3), -5)
    ):
        yield 'test__utcoffset__%s__has_offset_%d' % (str(dt), offset), check, dt, offset
