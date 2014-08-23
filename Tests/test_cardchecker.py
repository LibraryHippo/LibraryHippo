#!/usr/bin/env python

import pytest
import gael.testing
gael.testing.add_appsever_import_paths()

import google.appengine.runtime 		 	# NOQA
import google.appengine.runtime.apiproxy_errors 	# NOQA
import google.appengine.api.urlfetch 		 	# NOQA

import cardchecker


@pytest.mark.parametrize("error,expected", [
    ("google.appengine.runtime.DeadlineExceededError()", True),
    ("google.appengine.runtime.apiproxy_errors.DeadlineExceededError()", True),
    ("google.appengine.api.urlfetch_errors.DeadlineExceededError()", True),
    ("google.appengine.api.urlfetch.DownloadError('ApplicationError: 5')", True),
    ("google.appengine.api.urlfetch.DownloadError('ApplicationError: 2')", True),
    ("google.appengine.api.urlfetch.DownloadError('ApplicationError: 3')", False),
])
def test_eval(error, expected):
    assert cardchecker.is_transient_error(eval(error)) == expected
