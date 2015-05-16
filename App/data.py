#!/usr/bin/env python

import datetime
import traceback
import gael.objectproperty

from google.appengine.ext import db
from google.appengine.api import users
from google.appengine.ext.db import polymodel


class LoginError(Exception):
    def __init__(self, patron, library, message):
        self.patron = patron
        self.library = library
        self.message = message

    def __str__(self):
        return "LoginError('%(patron)s', '%(library)s: %(message)s')" % self.__dict__


class Thing():
    def __init__(self, library, card):
        self.library_name = library.name
        self.user = card.name
        self.title = ''
        self.author = ''
        self.url = ''
        self.status = ''
        self.status_notes = []

    def __cmp__(self, other):
        return cmp(self.sortkey(), other.sortkey())

    def add_status_note(self, note):
        self.status_notes.append(note)


class Hold(Thing):
    READY = 'Ready'
    IN_TRANSIT = 'In transit'
    CHECK_SHELVES = 'Check Shelves'
    DELAYED = 'Delayed'

    special_sortkeys = {
        READY: '  1' + READY,
        IN_TRANSIT: '  2' + IN_TRANSIT,
        CHECK_SHELVES: '  3' + CHECK_SHELVES,
        DELAYED: '~' + DELAYED,
    }

    def __init__(self, library, card):
        Thing.__init__(self, library, card)
        self.pickup = ''
        self.holds_url = ''
        self.expires = datetime.date.max

    def sortkey(self):
        if self.status in Hold.special_sortkeys:
            key = Hold.special_sortkeys[self.status]
        elif isinstance(self.status, tuple):
            key = '%04d' % self.status[0]
        elif isinstance(self.status, int):
            key = '%04d' % self.status
        else:
            key = ' ' + str(self.status)
        return key + ' ' + self.title

    def status_text(self):
        if isinstance(self.status, tuple):
            return '%d of %d' % self.status
        else:
            return self.status


class Item(Thing):
    def __init__(self, library, card):
        Thing.__init__(self, library, card)
        self.items_url = ''

    def sortkey(self):
        return str(self.status) + ' ' + self.title


class Family(db.Model):
    principals = db.ListProperty(users.User)
    name = db.StringProperty()

    def __str__(self):
        return self.name


class Library(db.Model):
    type = db.StringProperty(choices=['wpl', 'kpl', 'rwl'])
    name = db.StringProperty()


class Card(db.Model):
    family = db.ReferenceProperty(Family)
    number = db.StringProperty()
    name = db.StringProperty()
    pin = db.StringProperty()
    library = db.ReferenceProperty(Library)


class CardInfo:
    def __init__(self, library_name, patron_name, message):
        self.message = message
        self.library_name = library_name
        self.patron_name = patron_name


class CardStatus:
    def __init__(self, card, items=None, holds=None):
        self.library_name = card.library.name
        self.patron_name = card.name
        self.items = items or []
        self.holds = holds or []
        self.info = []
        self.expires = datetime.date.max

    def add_failure(self):
        self.info.append(CardInfo(self.library_name,
                                  self.patron_name,
                                  'Failed to check card. <a href="/about#check_failed">Why?</a>'))


class CheckedCard(db.Model):
    card = db.ReferenceProperty(Card)
    datetime = db.DateTimeProperty(auto_now=True)
    payload = gael.objectproperty.ObjectProperty()


class Event(polymodel.PolyModel):
    date_time_saved = db.DateTimeProperty(auto_now=True)
    user = db.UserProperty()
    exception = db.TextProperty()

    def set_exception(self):
        self.exception = traceback.format_exc()


class CardCheckFailed(Event):
    family = db.StringProperty()
    holder = db.StringProperty()
    library = db.StringProperty()
    card_key = db.ReferenceProperty(Card)

    @classmethod
    def for_card(cls, card, user):
        e = CardCheckFailed()
        e.set_exception()
        e.user = user
        e.family = card.family.name
        e.holder = card.name
        e.library = card.library.type
        e.card_key = card.key()
        return e
