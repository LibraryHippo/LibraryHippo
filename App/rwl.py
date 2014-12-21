#!/usr/bin/env python

import sys
import logging
import datetime
import re
import urlparse
from BeautifulSoup import BeautifulSoup
from data import Hold, Item, LoginError, CardInfo, CardStatus
import utils.soup


class LibraryAccount:
    def __init__(self, card, fetcher):
        self.card = card
        self.library = card.library
        self.fetcher = fetcher

    def base_url(self):
        return 'http://www.rwlibrary.ca'

    def get_date_from_element(self, element):
        utils.soup.remove_comments(element)
        date = ''.join(utils.soup.text(element)).strip()
        logging.debug('date string is: %s', date)
        match = re.match('\d\d? \w{3} \d\d\d\d', date)
        if match:
            date = match.group()
            return datetime.datetime.strptime(date, '%d %b %Y').date()

        # just return the original string, as we don't know what else to do
        logging.error('using date string in unknown format: %s', date)
        return date

    def get_title_from_hold_row(self, hold_row):
        title_element = hold_row('td')[1]
        utils.soup.remove_comments(title_element)
        return ''.join(utils.soup.text(title_element))

    def get_position_from_hold_row(self, hold_row):
        position_element = hold_row('td')[2]
        utils.soup.remove_comments(position_element)
        position = ''.join(utils.soup.text(position_element))
        if position.startswith('Available'):
            return Hold.READY
        position = position.replace('Your position in the holds queue:', '').strip()
        try:
            position = int(position)
        except ValueError:
            pass
        return position

    def get_pickup_from_hold_row(self, hold_row):
        pickup_element = hold_row('td')[3]
        utils.soup.remove_comments(pickup_element)
        return ''.join(utils.soup.text(pickup_element))

    def get_expires_from_hold_row(self, hold_row):
        expires_element = hold_row('td')[4]
        expires = self.get_date_from_element(expires_element)
        if expires == 'Never expires':
            return datetime.date.max
        return expires

    def parse_hold(self, hold_row):
        entry = Hold(self.library, self.card)
        entry.title = self.get_title_from_hold_row(hold_row)
        entry.status = self.get_position_from_hold_row(hold_row)
        entry.pickup = self.get_pickup_from_hold_row(hold_row)
        entry.expires = self.get_expires_from_hold_row(hold_row)
        return entry

    def get_title_from_item_row(self, item_row):
        title_element = item_row('td')[0]
        utils.soup.remove_comments(title_element)
        return ''.join(utils.soup.text(title_element))

    def get_author_from_item_row(self, item_row):
        author_element = item_row('td')[1]
        utils.soup.remove_comments(author_element)
        return ''.join(utils.soup.text(author_element))

    def get_due_date_from_item_row(self, item_row):
        due_element = item_row('td')[2]
        return self.get_date_from_element(due_element)

    def get_fines_from_item_row(self, item_row):
        fines_element = item_row('td')[3]
        utils.soup.remove_comments(fines_element)
        return ''.join(utils.soup.text(fines_element))

    def parse_item(self, item_row):
        entry = Item(self.library, self.card)
        entry.title = self.get_title_from_item_row(item_row)
        entry.author = self.get_author_from_item_row(item_row)
        entry.status = self.get_due_date_from_item_row(item_row)
        entry.add_status_note(self.get_fines_from_item_row(item_row))
        return entry

    def login(self):
        home_page_url = self.base_url() + '/en'
        logging.info('fetching home page from %s', home_page_url)
        home_page_content = self.fetcher(home_page_url, deadline=10).content
        home_page = BeautifulSoup(home_page_content)

        login_url = None
        for link in home_page.body('a'):
            if link.string == 'Log in':
                login_url = link['href']
                break

        if not login_url:
            self.raise_login_error("can't find login url on home page")

        logging.info('fetching login page from %s', login_url)
        login_page_content = self.fetcher(login_url, deadline=10).content
        login_page = BeautifulSoup(login_page_content)

        login_form = login_page.body('form', attrs={'id': 'loginPageForm'})[0]

        if not login_form:
            self.raise_login_error("can't find login form on home page")

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
        info_page_response = BeautifulSoup(self.fetcher(info_path_url, deadline=10).content)

        holds = []
        holds_tables = info_page_response.findAll('tbody', id=['tblHold', 'tblAvail'])
        for holds_table in holds_tables:
            holds_rows = holds_table.findAll('tr')
            for row in holds_rows:
                holds.append(self.parse_hold(row))

        items = self.get_items(info_page_response)

        return CardStatus(self.card, items, holds)

    def get_items(self, page):
        items = []
        item_due_dates = page.findAll(text=' Due Date ')
        if item_due_dates:
            item_rows = [i.parent.parent for i in item_due_dates]
            items = [self.parse_item(row) for row in item_rows]
        return items

    def get_status(self):
        my_account_url = self.login()
        status = self.load_info_page(my_account_url)
        status.info.append(CardInfo(self.card.library.name, self.card.name,
                                    "RWL card-checking is temporarily unavailable. We're working on it."))
        return status


def main(args=None):
    if args is None:
        args = sys.argv[1:]
    return 0


if __name__ == '__main__':
    sys.exit(main())
