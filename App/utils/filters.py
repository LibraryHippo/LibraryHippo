#!/usr/bin/env python

import datetime


def duedate(value):
    if isinstance(value, datetime.date):
        return value.strftime('%d').lstrip('0') + value.strftime('&nbsp;%B (%A)')
    else:
        return str(value)


def link(value, url):
    if url:
        return '<a href="%s">%s</a>' % (url, value)
    else:
        return value


def pluralize(count):
    if count == 1:
        return ''
    return 's'


def elapsed(value):

    if value.days:
        return str(value.days) + ' day' + pluralize(value.days)

    hours = value.seconds // 3600
    return str(hours) + ' hour' + pluralize(hours)


def humanize_time(value):
    delta = datetime.datetime.utcnow() - value
    if delta.days >= 1:
        return str(delta.days) + ' days ago'
    if delta.seconds < 45:
        return 'seconds ago'
    if delta.seconds < 105:
        return '1 minute ago'
    minutes = delta.seconds // 60
    if minutes < 50:
        return str(minutes) + ' minutes ago'
    if minutes < 110:
        return '1 hour ago'
    hours = minutes // 60
    return str(hours) + ' hours ago'


def register_all(environment):
    environment.filters['link'] = link
    environment.filters['duedate'] = duedate
    environment.filters['pluralize'] = pluralize
    environment.filters['elapsed'] = elapsed
    environment.filters['humanize_time'] = humanize_time
