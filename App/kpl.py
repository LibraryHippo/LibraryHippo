#!/usr/bin/env python

from BeautifulSoup import BeautifulSoup
import logging
import re
import datetime

from data import CardStatus, LoginError
import wpl


class LibraryAccount(wpl.LibraryAccount):
    def login_url(self):
        return 'https://books.kpl.org/iii/cas/login?service=https://books.kpl.org:443/patroninfo~S1/IIITICKET&scope=1'

    def get_status(self):
            expires = None
            try:
                login_response = self.login()

                redirect = re.search('window\\.location="([^"]+)"', login_response)
                if not redirect:
                    raise LoginError(patron=self.card.name, library=self.card.library.name,
                                     message="Can't find redirect.")

                logging.info('redirecting to %s', redirect.group(1))
                main_page = BeautifulSoup(self.fetcher(redirect.group(1)).content)

                holds_url = ''
                items_anchors = main_page.findAll(name='iframe', src=re.compile('/items$'))
                if items_anchors:
                    self.items_url = items_anchors[0]['src']
                    holds_url = self.items_url[:-5] + 'holds'
                    logging.info('items_url = %s', self.items_url)
                else:
                    logging.info('no link to items found')

                if holds_url:
                    holds = self.get_holds(holds_url)
                    logging.info('holds_url = %s', holds_url)
                else:
                    logging.info('no link to holds found')
                    holds = []

                expires_location = login_response.find('EXP DATE:')
                if expires_location >= 0:
                    expires_location += 9
                    expires_string = login_response[expires_location:expires_location + 10]
                    expires = datetime.datetime.strptime(expires_string, '%m-%d-%Y').date()

                items = self.get_items()

            finally:
                try:
                    self.logout()
                except:
                    logging.error('unable to log out', exc_info=True)

            status = CardStatus(self.card, items, holds)
            if expires:
                status.expires = expires
            return status
