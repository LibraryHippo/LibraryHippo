#!/usr/bin/env python

import datetime
import logging
import json
import re
import urlparse
from BeautifulSoup import BeautifulSoup
from data import Hold, Item, LoginError, CardStatus


class LibraryAccount:
    def __init__(self, card, fetcher):
        self.card = card
        self.library = card.library
        self.fetcher = fetcher

    def base_url(self):
        return 'https://www.rwlibrary.ca'

    def login(self):
        home_page_url = self.base_url() + '/en/'
        logging.info('fetching home page from %s', home_page_url)
        home_page_content = self.fetcher(home_page_url, deadline=10).content
        home_page = BeautifulSoup(home_page_content)

        login_url = None
        login_anchor = home_page.body.find('a', attrs={'id': 'myAccount'})
        if login_anchor:
            login_url = login_anchor['href'].strip()

        if not login_url:
            self.raise_login_error("can't find login url on home page")

        logging.info('fetching login page from %s', login_url)
        login_page_content = self.fetcher(login_url, deadline=10).content
        login_page = BeautifulSoup(login_page_content)

        login_form = login_page.body('form', attrs={'id': 'loginPageForm'})[0]

        if not login_form:
            self.raise_login_error("can't find login form on login page")

        form_fields = {}

        for input_field in login_page.findAll(name='input'):
            if input_field['type'] == 'submit':
                form_fields['submit'] = input_field['name']
            else:
                form_fields[input_field['name']] = input_field.get('value', '')

        form_fields.update({
            'j_username': self.card.number,
            'j_password': self.card.pin,
        })

        submit_login_url = urlparse.urljoin(login_url, login_form['action'])
        logging.info('submitting login information to %s', submit_login_url)

        login_response = self.fetcher(submit_login_url, form_fields)
        login_response_content = login_response.content

        redirect_to_url = re.search("RedirectAfterLogin\('([^']+)'\)", login_response_content)
        if not redirect_to_url:
            self.raise_login_error("Can't find redirect. Login failed.")

        logging.info('redirecting to %s', redirect_to_url.group(1))
        return redirect_to_url.group(1)

    def raise_login_error(self, message):
        raise LoginError(
            patron=self.card.name,
            library=self.card.library.name,
            message=message)

    def load_info_page(self, info_path_url):
        self.fetcher(info_path_url, deadline=10).content

    def parse_status(self, hold_row):
        status = hold_row('td')[3].string

        if status.startswith('Pickup'):
            return Hold.READY

        rank = hold_row('td')[6].string
        return int(rank)

    def parse_holds(self, holds_soup):
        holds = []
        holds_rows = holds_soup.findAll('tr', {'class': 'pickupHoldsLine'})
        for row in holds_rows:
            title = row('td')[2].find('a').string
            author = row('td')[2].find('p').find(text=True)
            is_frozen = row('td')[3].string == 'Suspended'
            pickup = row('td')[4].string
            rank = int(row('td')[6].string)

            logging.debug('%s / %s / %s', title, author, rank)

            hold = Hold(self.library, self.card)
            hold.title = title
            hold.author = author
            hold.pickup = pickup
            hold.status = self.parse_status(row)
            if is_frozen:
                hold.freeze()

            holds.append(hold)

        return holds

    def parse_checkouts(self, checkouts_soup):
        checkouts = []

        checkouts_rows = checkouts_soup.findAll('tr', {'class': 'checkoutsLine'})

        for row in checkouts_rows:
            title = row('td')[2].find('a').string
            author = row('td')[2].find('p').find(text=True).strip()
            due_date = datetime.datetime.strptime(row('td')[4].string, '%m/%d/%y').date()

            logging.debug('%s / %s / %s', title, author, due_date)

            checkout = Item(self.library, self.card)
            checkout.title = title
            checkout.author = author
            checkout.status = due_date

            checkouts.append(checkout)

        return checkouts

    def get_status(self):
        my_account_url = self.login()
        self.load_info_page(my_account_url)

        url = urlparse.urljoin(my_account_url, 'account.holds.libraryholdsaccordion?')
        holds_page_response = self.fetcher(url, method='POST', deadline=10, headers={
            'Accept': 'text/javascript',
            'X-Requested-With': 'XMLHttpRequest',
            'Content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Origin': 'http://olco.canlib.ca',
            'Referer': 'http://olco.canlib.ca/client/en_US/rwl/search/account?',
            }, payload={'t%3Azoneid': 'libraryHoldsAccordion'}).content

        holds_page_response_json = json.loads(holds_page_response)

        holds_soup = BeautifulSoup(holds_page_response_json['content'])
        holds = self.parse_holds(holds_soup)

        url = urlparse.urljoin(my_account_url, 'account.checkouts.librarycheckoutsaccordion?')
        checkouts_page_response = self.fetcher(url, method='POST', deadline=10, headers={
            'Accept': 'text/javascript',
            'X-Requested-With': 'XMLHttpRequest',
            'Content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Origin': 'http://olco.canlib.ca',
            'Referer': 'http://olco.canlib.ca/client/en_US/rwl/search/account?',
            }, payload={'t%3Azoneid': 'libraryCheckoutsAccordion'}).content

        checkouts_page_response_json = json.loads(checkouts_page_response)

        checkouts_soup = BeautifulSoup(checkouts_page_response_json['content'])
        checkouts = self.parse_checkouts(checkouts_soup)

        return CardStatus(self.card, checkouts, holds)
