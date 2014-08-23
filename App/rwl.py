#!/usr/bin/env python

import sys
import logging
import datetime
import re
from BeautifulSoup import BeautifulSoup
from data import Hold, Item, LoginError, CardStatus
import utils.soup


class LibraryAccount:
    def __init__(self, card, fetcher):
        self.card = card
        self.library = card.library
        self.fetcher = fetcher

    def base_url(self):
        return 'http://www.regionofwaterloo.canlib.ca'

    def login_url(self):
        return self.base_url() + '/uhtbin/cgisirsi/x/0/0/49?user_id=WEBSERVER&password='

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
        login_response = self.fetcher(self.login_url(), deadline=10)
        login_content = login_response.content
        login_page = BeautifulSoup(login_content)
        login_form = login_page.body('form', attrs={'name': 'loginform'})
        if not login_form:
            raise LoginError(patron=self.card.name, library=self.card.library.name)

        login_url = self.base_url() + login_form[0]['action']
        logging.debug('found login url: ' + login_url)

        form_fields = {
            'user_id': self.card.number,
            'password': self.card.pin,
            'submit': 'Login'
        }

        login_response = BeautifulSoup(self.fetcher(login_url, form_fields, deadline=10).content)
        my_account_url = login_response.body(text=lambda(x): x.find('My Account') >= 0)
        my_account_url = self.base_url() + my_account_url[0].parent['href']

        logging.debug('found account_response url: ' + my_account_url)
        return my_account_url

    def load_account_page(self, my_account_url):
        account_response = BeautifulSoup(self.fetcher(my_account_url, deadline=10).content)

        info_path_url = account_response.body(text=lambda(x): x.find('Review My Account') >= 0)
        info_path_url = info_path_url[0].parent['href']
        info_path_url = self.base_url() + info_path_url

        logging.debug('found info_path_url: ' + info_path_url)
        return info_path_url

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

    def get_holds(self):
        pass

    def get_items(self, page):
        items = []
        item_due_dates = page.findAll(text=' Due Date ')
        if item_due_dates:
            item_rows = [i.parent.parent for i in item_due_dates]
            items = [self.parse_item(row) for row in item_rows]
        return items

    def get_status(self):
        my_account_url = self.login()
        info_path_url = self.load_account_page(my_account_url)
        return self.load_info_page(info_path_url)


def main(args=None):
    if args is None:
        args = sys.argv[1:]
    return 0


if __name__ == '__main__':
    sys.exit(main())
