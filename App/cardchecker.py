import logging
import sys
import time

from google.appengine.api.urlfetch import DownloadError

import all_libraries
import data
import errors
import utils.times

clock = utils.times.Clock()


def is_transient_error(e):
    result = ((type(e).__name__ == 'DeadlineExceededError') or
              (type(e).__name__ == 'DownloadError') and
              (e.message.strip() == 'ApplicationError: 5' or
               e.message.strip() == 'ApplicationError: 2'))
    logging.debug('is_transient_error: testing [%s] [%s]: result = [%s]',
                  type(e), e, result)

    return result


class CardChecker:

    def check(self, user, card, fetcher):
        try:
            library_account = all_libraries.create(card, fetcher)

            logging.info('checking [%s] at [%s]', library_account.card.name, library_account.library.name)

            if library_account.card.number == 'timeout':
                logging.info('special timeout!')
                time.sleep(1)
                raise DownloadError('ApplicationError: 5')
            else:
                card_status = library_account.get_status()

            self.save_checked_card(library_account.card, card_status)

        except:
            e = data.CardCheckFailed.For(user, library_account.card)
            logging.info('event = ' + str(e.__dict__))
            e.put()
            logging.error('failed to check [%s] at [%s]',
                          library_account.card.name, library_account.library.name, exc_info=True)

            card_status = data.CardStatus(library_account.card)
            card_status.add_failure()

            for transaction in fetcher.transactions:
                logging.debug(transaction)

            exception_type, exception_value, exception_trace = sys.exc_info()

            if is_transient_error(sys.exc_info()[1]):
                raise errors.TransientError(card_status)

        return card_status

    def save_checked_card(self, card, card_status):
        try:
            logging.info('saving checked card for ' + card_status.patron_name)

            checked_card_key = data.CheckedCard.all(keys_only=True).filter('card =', card).get()
            if checked_card_key:
                checked_card = data.CheckedCard(key=checked_card_key)
            else:
                checked_card = data.CheckedCard()

            checked_card.card = card
            checked_card.payload = card_status
            checked_card.datetime = clock.utcnow()
            checked_card.put()
        except:
            logging.error('Failed to save checked card. Continuing.', exc_info=True)
