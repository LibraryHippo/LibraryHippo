#!/usr/bin/env python

import gael.testing
gael.testing.add_appsever_import_paths()

import BeautifulSoup
import utils
import utils.soup


def test__build_notification__no_events__subject_is_false():
    subject = utils.build_notification_subject([], [], [])
    assert not subject


def test__build_notification__one_message__subject_says_1_message():
    subject = utils.build_notification_subject(['Blair'], [], [])
    assert '1 Message' == subject


def test__build_notification__two_messages__subject_says_2_messages():
    subject = utils.build_notification_subject(['Blair', 'BookHippo'], [], [])
    assert '2 Messages' == subject


def test__build_notification__one_item_due__subject_says_1_item_due():
    subject = utils.build_notification_subject([], ['item 1'], [])
    assert '1 Item Due' == subject


def test__build_notification__one_item_due_and_two_holds_ready__subject_says_1_item_due_and_2_holds_ready():
    subject = utils.build_notification_subject([], ['item 1'], ['hold 1', 'hold 2'])
    assert '1 Item Due and 2 Holds Ready' == subject


def test__pluralize__default_subject__adds_s_or_not():
    def check(count, ending):
        assert ending == utils.pluralize([None] * count)

    for count, ending in (
        (0, 's'),
        (1, ''),
        (2, 's'),
    ):
        yield 'pluralize_%d_with_default_suffix' % count, check, count, ending


def test__soup_remove_comments__comments_present__removes_comments():
    soup = BeautifulSoup.BeautifulSoup('''<td class="defaultstyle">
    <!-- Title -->
    <label style="font-weight: normal" for="HLD^TITLE^36501004469008^FIC Niffe^28746
    0">Her fearful symmetry : a novel</label>
    </td>''')

    utils.soup.remove_comments(soup)
    assert 'Her fearful symmetry : a novel' == soup.label.string
