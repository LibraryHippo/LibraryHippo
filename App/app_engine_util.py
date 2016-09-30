#!/usr/bin/env python

import config
import logging
import urllib
import urlparse


def send_email(tos, subject, **attributes):
    import sendgrid
    from sendgrid.helpers.mail import Email, Content, Mail

    first_to = tos[0]

    sg = sendgrid.SendGridAPIClient(apikey=config.sendgrid_config['sendgrid_api_key'])
    from_email = Email('librarianhippo@gmail.com')
    to_email = Email(first_to)

    body = attributes.get('body', None)
    html = attributes.get('html', None)
    if body:
        content = Content('text/plain', body)
    elif html:
        content = Content('text/html', html)

    message = Mail(from_email, subject, to_email, content)
    for additional_to in tos[1:]:
        message.personalizations[0].add_to(Email(additional_to))

    bccs = attributes.get('bccs', [])
    for bcc in bccs:
        message.personalizations[0].add_bcc(Email(bcc))

    logging.info('sending mail "%s" to "%s"', subject, tos)

    response = sg.client.mail.send.post(request_body=message.get())
    logging.debug('sent mail with status code %d', response.status_code)


def create_openid_url(request_url=None, continue_url=None):
    continue_url = urlparse.urljoin(request_url, continue_url)
    return '/_ah/login_required?continue=%s' % urllib.quote(continue_url)
