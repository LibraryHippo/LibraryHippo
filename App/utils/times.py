#!/usr/bin/env python

import calendar
import datetime


class WaterlooTimeZone(datetime.tzinfo):

    """Represents the time zone for Waterloo, Ontario, Canada"""
    def utcoffset(self, dt):
        return datetime.timedelta(hours=-5) + self.dst(dt)

    def dst(self, dt):
        # Daylight Saving Time begins on the second Sunday in March and ends
        # on the first Sunday in November. At 2 am

        if 3 < dt.month < 11:
            return datetime.timedelta(hours=1)

        month = calendar.monthcalendar(dt.year, dt.month)
        if 3 == dt.month:
            if month[0][dt.weekday()] == 0:
                secondSunday = month[2][dt.weekday()]
            else:
                secondSunday = month[1][dt.weekday()]
            if dt.day > secondSunday or (dt.day == secondSunday and dt.hour >= 2):
                return datetime.timedelta(hours=1)
        elif 11 == dt.month:
            if month[0][dt.weekday()] == 0:
                firstSunday = month[1][dt.weekday()]
            else:
                firstSunday = month[0][dt.weekday()]
            if dt.day < firstSunday or (dt.day == firstSunday and dt.hour < 2):
                return datetime.timedelta(hours=1)
        return datetime.timedelta(0)

    def tzname(self, dt):
        return 'Canada/Ontario/Waterloo'


class Clock(object):

    """A clock. Provides a basic abstraction over some datetime module functions."""

    def __init__(self, tzinfo=WaterlooTimeZone()):
        self.tzinfo = tzinfo

    def today(self):
        """Returns the date that is today"""
        return datetime.datetime.now(WaterlooTimeZone()).date()

    def utcnow(self):
        return datetime.datetime.utcnow()
