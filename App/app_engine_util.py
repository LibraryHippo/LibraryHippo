#!/usr/bin/env python

import logging
import urllib
import urlparse

from google.appengine.api import mail
from google.appengine.api import users

import data


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


def uses_family(func):
    def wrapper(self, *args, **kwargs):
        user = users.get_current_user()
        if not user:
            self.redirect(create_openid_url(request_url=self.request.uri))
            return

        if users.is_current_user_admin():
            impersonated_user = urllib.unquote(self.request.cookies.get('user', ''))
            logging.debug('impersonated_user = ' + impersonated_user)
            if impersonated_user:
                user = users.User(impersonated_user)
                logging.debug('pretending to be ' + str(user))
                logging.debug('template_values = ' + str(self.template_values))
                self.template_values['stop_impersonating_url'] = '/admin/stopimpersonating'
                logging.debug('template_values = ' + str(self.template_values))
        family = data.Family.all().filter('principals = ', user).get()
        logging.debug('family = ' + str(family))

        args = (user, family,) + args
        self.request.user = user
        self.request.family = family
        func(self, *args, **kwargs)
    return wrapper
