#!/usr/bin/env python

import gael.testing
gael.testing.add_appsever_import_paths()

import datetime
import libraryhippo
import data
import fakes

class Family(object):
    def __init__(self):
        self.name = 'Griffin'

def setup_module(module):
    libraryhippo.clock = fakes.StoppedClock(datetime.datetime(2011, 03, 31, 19, 12, 13))

def test__load_summary__recent_checks__no_late_warning():
    an = libraryhippo.AdminNotify(None, None)
    family = Family()
    
    cc = data.CheckedCard()
    cc.payload = data.CardStatus(fakes.MyCard(), items=[], holds=[])
    cc.datetime = datetime.datetime(2011, 03, 31, 17, 42, 13)

    template_values = an.load_summary(family, [cc])

    assert not template_values['info']

def test__load_summary__long_ago_checks__late_warning():
    an = libraryhippo.AdminNotify(None, None)
    family = Family()
    
    cc = data.CheckedCard()
    cc.payload = data.CardStatus(fakes.MyCard(), items=[], holds=[])
    cc.datetime = datetime.datetime(2011, 03, 30, 20, 42, 13)
    
    template_values = an.load_summary(family, [cc])

    assert template_values['info']
    assert 'unable to check card for 22 hours' in template_values['info'][0].message

def test__load_summary__long_ago_checks__turns_on_should_notify():
    an = libraryhippo.AdminNotify(None, None)
    family = Family()
    
    cc = data.CheckedCard()
    cc.payload = data.CardStatus(fakes.MyCard(), items=[], holds=[])
    cc.datetime = datetime.datetime(2011, 03, 30, 20, 42, 13)
    
    template_values = an.load_summary(family, [cc])

    assert template_values['should_notify']
