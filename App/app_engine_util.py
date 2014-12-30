#!/usr/bin/env python

import logging
import urllib
import urlparse

from google.appengine.api import mail


def send_email(to, subject, **attributes):
    attributes.setdefault('sender', 'librarianhippo@gmail.com')

    message = mail.EmailMessage()
    for key, value in attributes.items():
        if value:
            setattr(message, key, value)
    message.to = to
    message.subject = subject

    logging.info('sending mail "%s" to "%s"', message.subject, message.to)
    message.send()


def create_openid_url(request_url=None, continue_url=None):
    continue_url = urlparse.urljoin(request_url, continue_url)
    return '/_ah/login_required?continue=%s' % urllib.quote(continue_url)
