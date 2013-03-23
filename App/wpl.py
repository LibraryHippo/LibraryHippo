#!/usr/bin/env python

import sys
import urlparse
import logging
import datetime
import re
from BeautifulSoup import BeautifulSoup
from data import Hold, Item, LoginError, CardStatus
import utils.soup

def strip_tags(element): 
    return ''.join([e for e in element.recursiveChildGenerator() 
                    if isinstance(e,unicode)])
   

def parse_status(status_element):
    rest = []
    due_text = status_element.contents[0].strip()
    if due_text.startswith('DUE'):
        due = due_text[4:12]
        due = datetime.datetime.strptime(due, '%m-%d-%y').date()
        rest.extend(due_text[12:].split(' '))
    else:
        due = due_text
    rest.extend((('<br/>'.join(utils.soup.text(c)) for c in status_element.contents[1:])))
    return (due,) + tuple(rest)

def parse_hold_status(status_element):
    due_text = status_element.contents[0].strip()
    special_statuses = {
        'Ready.': Hold.READY,
        'IN TRANSIT': Hold.IN_TRANSIT,
        'CHECK SHELVES': Hold.CHECK_SHELVES,
        'TRACE': Hold.DELAYED,
      }

    if due_text in special_statuses:
        return special_statuses[due_text]

    parts = due_text.split()
    if len(parts) > 2 and parts[1] == 'of':
        return (int(parts[0]), int(parts[2]))
    else:
        return due_text

def parse_hold_expires(cell):
    text  = cell.contents[0].strip()
    return datetime.datetime.strptime(text, '%m-%d-%y').date()

def parse_hold_frozen(cell):
    if not cell.input:
        return False
    for attr_name, attr_value in cell.input.attrs:
        if attr_name == 'checked':
            return True
    return False

class LibraryAccount:
    def __init__(self, card, fetcher):
        self.card = card
        self.library = card.library
        self.fetcher = fetcher

    def login_url(self):
        return 'https://books.kpl.org/iii/cas/login?service=https://books.kpl.org/patroninfo~S3/j_acegi_cas_security_check&lang=eng&scope=3'

    def logout_url(self):
        return urlparse.urljoin(self.login_url(), '/logout?')

    def item_url(self, original_url):
        return urlparse.urljoin(self.login_url(), original_url)

    def login(self):
        form_fields = {}
        login_page = BeautifulSoup(self.fetcher(self.login_url()).content)

        for input_field in login_page.findAll(name='input'):
            if input_field['type'] == 'submit':
                form_fields['submit'] = input_field['name']
            else:
                form_fields[input_field['name']] = input_field['value']
        
        form_fields.update({
          'name': self.card.name,
          'code': self.card.number,
          })

        response = self.fetcher(self.login_url(), form_fields)
        
        response_data = response.content

        if '"patNameAddress"' not in response_data:
             l = LoginError(patron=self.card.name, library=self.card.library.name)
             logging.error('login failed: %s', l)
             raise l            

        return response.content

    def get_holds(self, holds_url):
        response = self.fetcher(holds_url)
        holds = self.parse_holds(BeautifulSoup(response.content))
        for hold in holds:
            hold.holds_url = holds_url
        return holds

    def get_items(self):
        if not hasattr(self, 'items_url'): return []
        response = self.fetcher(self.items_url)
        items =  self.parse_items(BeautifulSoup(response.content))
        for item in items:
            item.items_url = self.items_url
        return items

    def logout(self):
        response = self.fetcher(self.logout_url())

    def get_status(self):
        try:
            login_response = self.login()

            souped_response = BeautifulSoup(login_response)

            holds_anchors = souped_response.findAll(name='a', href=re.compile('/holds$'))
            if holds_anchors:
                holds_url = urlparse.urljoin(self.login_url(), holds_anchors[0]['href'])
                holds = self.get_holds(holds_url)
            else:
                holds = []
                
            items_anchors = souped_response.findAll(name='a', href=re.compile('/items$'))
            if items_anchors:
                self.items_url = urlparse.urljoin(self.login_url(), items_anchors[0]['href'])

            self.expires = None
            expires_location = login_response.find('EXP DATE:')
            if expires_location >= 0:
                expires_location += 9
                expires_string = login_response[expires_location:expires_location+10]
                self.expires = datetime.datetime.strptime(expires_string, '%m-%d-%Y').date()
        
            items = self.get_items()

        finally:
            self.logout()
        status = CardStatus(self.card, items, holds)
        if self.expires:
            status.expires = self.expires
        return status
        

    def parse_holds(self, response):
        tableHeader = response.find('tr', attrs={'class': 'patFuncHeaders'})
        if not tableHeader:
            return []
        headers = [th.string.strip() for th in tableHeader('th')]

        entries = []
        for row in tableHeader.findNextSiblings('tr'):
            entry = Hold(self.library, self.card)
            i = 0
            for cell in row('td'):
                columnName = headers[i]

                if columnName == 'TITLE':
                    self.parse_title(cell, entry)
                elif columnName == 'PICKUP LOCATION':
                    if cell.select:
                        entry.pickup = cell.select.findAll('option', selected='selected')[0].string
                    else:
                        entry.pickup = cell.string.strip()
                        
                elif columnName == 'STATUS':
                    entry.status = parse_hold_status(cell)

                elif columnName == 'CANCEL IF NOT FILLED BY':
                    try:
                        entry.expires = parse_hold_expires(cell)
                    except:
                        # expiration info isn't critical - ignore
                        pass

                elif columnName == 'FREEZE':
                    try:
                        if parse_hold_frozen(cell):
                            entry.add_status_note('frozen')
                    except:
                        # frozen info isn't critical - ignore
                        logging.warn('error getting frozen info', exc_info=True)
                        pass
                i += 1

            entries.append(entry)
        return entries

    def parse_title(self, cell, thing):
        title_parts = strip_tags(cell.a).split(' / ')
        thing.title = title_parts[0].strip()
        thing.author = ''.join(title_parts[1:]).strip()
        thing.url = self.item_url(cell.a['href'])

    def parse_items(self, items):
        tableHeader = items.find('tr', attrs={'class': 'patFuncHeaders'})
        if not tableHeader:
            return []
        headers = [th.string.strip() for th in tableHeader('th')]

        entries = []
        for row in tableHeader.findNextSiblings('tr'):
            entry = Item(self.library, self.card)
            i = 0
            for cell in row('td'):
                columnName = headers[i]
                if columnName == 'TITLE':
                    self.parse_title(cell, entry)

                elif columnName == 'STATUS':
                    status = parse_status(cell)
                    entry.status = status[0]
                    entry.add_status_note((' '.join(status[1:])).strip())
                i += 1
            entries.append(entry)
        return entries


def main(args=None):
    if args == None:
        args = sys.argv[1:]
    return 0


if __name__ == '__main__':
    sys.exit(main())

