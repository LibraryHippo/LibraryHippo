import os
import logging
import uuid
import urlparse

from google.appengine.api import users
from google.appengine.api import urlfetch
from google.appengine.api import taskqueue
from google.appengine.ext import db
import webapp2
from webapp2_extras import jinja2
from webapp2_extras import sessions

import datetime
from cardchecker import CardChecker
import errors

import data
from app_engine_util import send_email
import utils
import utils.times
import utils.filters
from gael.urlfetch import Transcriber, PayloadEncoder, RedirectFollower, CookieHandler, Securer

from authomatic import Authomatic
from authomatic.adapters import Webapp2Adapter
import config

authomatic = Authomatic(
    config=config.authomatic_config,
    secret='secret',
    report_errors=True,
    logging_level=logging.DEBUG)

clock = utils.times.Clock()


class MyHandler(webapp2.RequestHandler):

    @webapp2.cached_property
    def jinja(self):
        jinja2.default_config['environment_args']['autoescape'] = False
        j = jinja2.get_jinja2(app=self.app)
        utils.filters.register_all(j.environment)
        return j

    def handle_exception(self, exception, debug_mode):
        error_uid = uuid.uuid4()
        logging.critical('Error ' + str(error_uid) + ' caught. Unable to proceed.', exc_info=True)

        message_body = str(self.request)
        for attr in ('user', 'family'):
            if hasattr(self.request, attr):
                message_body += '\n' + attr + ': ' + str(getattr(self.request, attr))

        send_email(['librarianhippo@gmail.com'],
                   'LibraryHippo Error ' + str(error_uid),
                   body=message_body)

        self.template_values['error_uid'] = error_uid
        self.render('error.html')
        self.response.set_status(500)

    def render(self, template_file):
        self.response.out.write(self.jinja.render_template(template_file, **self.template_values))

    def dispatch(self):
        self.template_values = {}

        # Get a session store for this request.
        self.session_store = sessions.get_store(request=self.request)

        try:
            self.assert_is_allowed()
            webapp2.RequestHandler.dispatch(self)
        finally:
            # Save all sessions.
            self.session_store.save_sessions(self.response)

    @webapp2.cached_property
    def session(self):
        # Returns a session using the default cookie key.
        return self.session_store.get_session()

    def get_family(self):
        user_email = self.session.get('user_email')
        impersonating_user_email = self.session.get('impersonating_user_email')

        logging.debug('user_email = %s', user_email)
        logging.debug('impersonating_user_email = %s', impersonating_user_email)

        if not user_email:
            self.session['next_url'] = self.request.url
            self.redirect('/oauth2/google')
            return (None, None)

        if impersonating_user_email is not None:
            self.template_values['stop_impersonating_url'] = '/admin/stopimpersonating'
            user_email = impersonating_user_email

        user = users.User(user_email)
        family = None
        for f in data.Family.all():
            for p in f.principals:
                principal_email = p.email()
                if principal_email == user.email():
                    user = p
                    family = f
                    break

        self.template_values['logout_url'] = '/logout'
        if self.is_current_user_admin():
            self.template_values['control_panel_url'] = '/admin/controlpanel'

        logging.info('user = [%s] and family = [%s]', user, family)

        return (user, family)

    def is_allowed(self):
        if self.is_current_user_admin():
            logging.debug('is_allowed: returning true because [%s] is an admin', self.session.get('user_email'))
            return True

        path = urlparse.urlsplit(self.request.url).path
        if path.startswith('/admin/'):
            logging.debug('is_allowed: returning false because [%s] is not an admin', self.session.get('user_email'))
            return False
        else:
            logging.debug('is_allowed: assuming true because [%s] is not an admin-only URL', self.request.url)
            return True

    def is_current_user_admin(self):
        return self.session.get('user_email') == 'blair.conrad@gmail.com'

    def assert_is_allowed(self):
        if not self.is_allowed():
            self.abort(403)


class OAuth2(MyHandler):
    def get(self, provider_name):

        result = authomatic.login(Webapp2Adapter(self), provider_name)

        if result:
            if result.error:
                error_message = result.error.message
                raise(Exception('Login failed to [%s]. Error was [%s].' % (provider_name, error_message)))
            elif result.user:
                if not (result.user.name and result.user.id):
                    logging.debug('No name or id. Getting.')
                    result.user.update()
                logging.info('user = [%s, %s, %s]', result.user.name, result.user.id, result.user.email)
                self.session['user_email'] = result.user.email
                next_url = self.session.get('next_url') or '/'
                logging.debug('redirecting to %s', next_url)
                return self.redirect(str(next_url))
            else:
                raise(Exception('Login to [%(provider_name)s] succeeded, but no user was returned.' % vars()))


class Account(MyHandler):

    def get(self):
        (user, family) = self.get_family()
        if user is None:
            return

        libraries = data.Library.all()

        self.template_values.update({
            'family': family,
            'libraries': libraries,
            'cards': family and list(family.card_set) or [],
            'principals': family and family.principals or [],
        })

        self.render('account.html')


class SaveCard(MyHandler):
    def post(self):
        (user, family) = self.get_family()
        if not family:
            self.redirect('/account')
            return

        card = data.Card(parent=family,
                         family=family,
                         number=self.request.get('number'),
                         name=self.request.get('name'),
                         pin=self.request.get('pin'),
                         library=data.Library.get(self.request.get('library_id'))
                         )
        card.put()
        self.redirect('/account')


class RemoveCard(MyHandler):
    def get(self, card_key):
        (user, family) = self.get_family()
        card = data.Card.get(card_key)
        if card.family.key() == family.key():
            logging.info('removing card %s', card.to_xml())
            card.delete()
            family.put()
            logging.info('saved family %s', family.to_xml())
        else:
            logging.error('request to remove card %s from family %s failed', card.to_xml(), family.to_xml())
        self.redirect('/account')


class ChangePin(MyHandler):
    def get(self, card_key, new_pin):
        (user, family) = self.get_family()
        card = data.Card.get(card_key)
        if card.family.key() == family.key():
            logging.info('updating pin for card %s', card.to_xml())
            card.pin = new_pin
            card.put()
            logging.info('saved card')
        else:
            logging.error('request to update pin for card %s that belongs to family %s failed',
                          card.to_xml(), family.to_xml())
        self.redirect('/account')


class RemoveResponsible(MyHandler):
    def post(self):
        (user, family) = self.get_family()
        removed_a_principal = False
        for principal_email in self.request.arguments():
            principal = users.User(principal_email)
            if principal in family.principals:
                send_email([principal_email],
                           'LibraryHippo: you are no longer a responsible person for the ' + family.name + ' family',
                           body=user.email() + ' has removed you from being a responsible person for the ' +
                           family.name + 'family at LibraryHippo (https://www.libraryhippo.com)')
                logging.info('removing principal %s ', principal)
                family.principals.remove(principal)
                removed_a_principal = True
            else:
                logging.error('request to remove principal %s from family %s failed', principal, family.to_xml())

        if len(family.principals) == 0:
            logging.info('no more principals - removing family %s', family.to_xml())
            cards = [c for c in family.card_set]
            db.delete(cards + [family])
        else:
            if removed_a_principal:
                family.put()
                logging.info('saved family %s', family.to_xml())

        self.redirect('/account')


class SaveFamily(MyHandler):
    def post(self):
        (user, family) = self.get_family()
        if not family:
            family = data.Family()
            send_email(['librarianhippo@gmail.com'],
                       'New family ' + self.request.get('name') + ' registered',
                       body=('registered to ' + str(user)))

        family.name = self.request.get('name')
        if not family.principals:
            family.principals = [user]
        family.put()

        self.redirect('/account')


class AddResponsible(MyHandler):
    def post(self):
        (user, family) = self.get_family()
        if not family:
            self.redirect('/account')

        new_principal = users.User(self.request.get('email'))

        if new_principal not in family.principals:
            if data.Family.all().filter('principals = ', new_principal).count():
                logging.info('%s is a member of a different family', new_principal.email())
                self.template_values.update({
                    'title': 'User Belongs to Another Family',
                    'message': new_principal.email() + ' is already responsible for another family',
                })
                self.render('info.html')
                return
            else:
                send_email([new_principal.email()],
                           'LibraryHippo: you are now a responsible person for the ' + family.name + ' family',
                           body=user.email() + ' has made you a responsible person for the ' + family.name +
                           ' family.\nLearn more by visiting LibraryHippo at https://www.libraryhippo.com')
                family.principals.append(new_principal)
                family.put()
        else:
            logging.debug(new_principal.email() + ' is already in ' + family.name)

        self.redirect('/account')


def make_test_summary(family):
    card = family.card_set[0]

    h = data.Hold(card.library, card)
    h.title = 'A Book'
    h.author = 'Some Author'
    h.url = 'http://books.wpl.ca/record=2017161~S3'
    h.status = data.Hold.READY
    h.pickup = 'The Book Source'
    h.add_status_note('note 1')
    h.add_status_note('note 2')
    holds_ready = [h]

    template_values = {}
    template_values['holds_ready'] = holds_ready
    template_values['items_due'] = []
    template_values['info'] = []
    template_values['family'] = family

    return template_values


def build_template(statuses, family):
    holds = sum((status.holds for status in statuses), [])
    items = sum((status.items for status in statuses), [])
    info = sum((status.info for status in statuses), [])

    holds.sort()
    items.sort()

    today = clock.today()

    item_due_cutoff = today + datetime.timedelta(days=3)
    items_due_soon = []
    items_due_later = []

    for item in items:
        if item.status <= item_due_cutoff:
            items_due_soon.append(item)
        else:
            items_due_later.append(item)

    hold_expires_cutoff = today + datetime.timedelta(days=30)
    holds_ready = []
    holds_not_ready = []
    for hold in holds:
        if hold.status == data.Hold.READY:
            holds_ready.append(hold)
        else:
            holds_not_ready.append(hold)

        if hold.expires <= hold_expires_cutoff:
            hold.add_status_note('expires on ' + utils.filters.duedate(hold.expires))

    template_values = {}
    template_values['family'] = family
    template_values['should_notify'] = False
    template_values['holds_ready'] = holds_ready
    template_values['holds_not_ready'] = holds_not_ready
    template_values['items_due'] = items_due_soon
    template_values['items_not_due'] = items_due_later
    template_values['info'] = []
    template_values['info'] += info

    template_values['error'] = bool(template_values['info'])

    if template_values['info'] or template_values['holds_ready'] or template_values['items_due']:
        template_values['should_notify'] = True

    expiry_first_warning_date = today + datetime.timedelta(days=7)
    for status in statuses:
        if status.expires <= expiry_first_warning_date:
            logging.debug('card expires within a week')
            if status.expires == today or status.expires == expiry_first_warning_date:
                template_values['should_notify'] = True

            if status.expires < today:
                message = 'card expired on ' + str(status.expires)
            elif status.expires == today:
                message = 'card expires today'
            else:
                message = 'card expires on ' + utils.filters.duedate(status.expires)
            template_values['info'] += [data.CardInfo(status.library_name, status.patron_name, message)]

    return template_values


class Summary(MyHandler):
    def get(self):
        (user, family) = self.get_family()
        if not user:
            return
        if not family:
            self.redirect('/account')
            return

        self.template_values['cards'] = [card for card in family.card_set]
        self.template_values['family'] = family

        self.render('summary.html')


class CheckCardBase(MyHandler):
    def check_card(self, user, card):
        fetcher = PayloadEncoder(RedirectFollower(CookieHandler(Securer(Transcriber(urlfetch.fetch)))))

        checker = CardChecker()
        try:
            card_status = checker.check(user, card, fetcher)
        except errors.TransientError as e:
            self.response.set_status(504)
            card_status = e.card_status

        return card_status


class CheckCard(CheckCardBase):
    def get(self, card_key):
        (user, family) = self.get_family()
        logging.info('CheckCard called ' + card_key)
        card = data.Card.get(card_key)
        if family.key() != card.family.key():
            logging.error('access denied: card family = ' + str(card.family) + ' family = ' + str(family))
            card_status = data.CardStatus(card)
            card_status.add_failure()
        else:
            card_status = self.check_card(user=user, card=card)

        self.template_values.update(build_template([card_status], family))
        self.render('ajax_content.html')


class Welcome(MyHandler):
    def get(self):
        self.render('welcome.html')


class About(MyHandler):
    def get(self):
        self.render('about.html')


class AdminNotify(MyHandler):
    def load_summary(self, family, checked_cards):
        logging.info('getting summary for family = ' + str(family.name))

        statuses = [c.payload for c in checked_cards]
        template = build_template(statuses, family)

        for c in checked_cards:
            elapsed = clock.utcnow() - c.datetime
            if elapsed > datetime.timedelta(hours=20):
                time_since_check = utils.filters.elapsed(elapsed)
                logging.error('unable to check card for ' + time_since_check)
                template['should_notify'] = True
                why_link = '<a href="https://www.libraryhippo.com/about#check_failed">Why?</a>'
                template['info'].append(data.CardInfo(c.payload.library_name, c.payload.patron_name,
                                                      'Unable to check card for ' + time_since_check + '. ' +
                                                      why_link))

        return template

    def get(self, family_key):
        family = data.Family.get(family_key)
        if not family:
            raise Exception('no family')

        # what happens if there are cards that have never been checked? Don't worry for now.
        checked_cards = data.CheckedCard.all().filter('card IN ', list(family.card_set))

        template_values = self.load_summary(family, checked_cards)

        if not template_values['should_notify']:
            logging.debug('no reason to notify')
            return

        subject = utils.build_notification_subject(template_values['info'],
                                                   template_values['items_due'],
                                                   template_values['holds_ready'])

        if subject:
            bccs = []
            if template_values['error']:
                bccs = ['librarianhippo@gmail.com']
            send_email([a.email() for a in family.principals],
                       subject,
                       bccs=bccs,
                       html=self.jinja.render_template('email.html', **template_values))


class AdminNotifyTest(MyHandler):
    def get(self, family_key):
        for_family = data.Family.get(family_key)
        if not for_family:
            raise Exception('no family')
        template_values = make_test_summary(for_family)

        send_email([a.email() for a in for_family.principals],
                   'LibraryHippo status for ' + for_family.name + ' Family',
                   html=self.jinja.render_template('email.html', **template_values))


class CheckAllCards(MyHandler):
    def get(self):
        cards = data.Card.all().fetch(1000)
        tasks = [taskqueue.Task(url='/system/checkcard/' + str(card.key()), method='GET') for card in cards]
        q = taskqueue.Queue()
        q.add(tasks)
        message = 'finished queuing tasks to check %d cards' % (len(tasks),)
        logging.info(message)
        self.response.out.write(message)


class AdminCheckCard(CheckCardBase):
    def get(self, card_key):
        card = data.Card.get(card_key)
        self.check_card(user=users.get_current_user(), card=card)


class ListFamilies(MyHandler):
    def get(self):
        families = data.Family.all().fetch(1000)
        logging.debug(families)
        self.template_values.update({'families': families})
        self.render('families.html')


class ControlPanel(MyHandler):
    def get(self):
        if os.environ['SERVER_SOFTWARE'].startswith('Development'):
            dashboard = 'http://localhost:8000/datastore'
        else:
            dashboard = 'https://console.cloud.google.com/home/dashboard?project=libraryhippo27'

        self.template_values = {'dashboard': dashboard}
        self.render('controlpanel.html')


class Impersonate(MyHandler):
    def get(self, username):
        self.session['impersonating_user_email'] = username
        self.template_values.update({'user': username})
        self.render('impersonate.html')
        return


class ViewCheckedCards(MyHandler):
    def get(self, family_key):
        family = data.Family.get(family_key)
        if not family:
            raise Exception('no family')

        checked_cards = data.CheckedCard.all().filter('card IN ', list(family.card_set)).fetch(1000)
        statuses = [cc.payload for cc in checked_cards]

        logging.debug('found ' + str(len(statuses)) + ' statuses')
        self.template_values = build_template(statuses, family)
        self.render('static_summary.html')


class AuditLog(MyHandler):
    def get(self, page='1'):
        page = int(page, 10)
        now = clock.utcnow()
        events = []
        for e in data.Event.all() \
                .filter('date_time_saved >', now - datetime.timedelta(days=page)) \
                .filter('date_time_saved <', now - datetime.timedelta(days=page - 1)) \
                .order('-date_time_saved'):
            logging.debug('Event user = ' + str(e.user))
            events.append(e)

        self.template_values = {'events': events, 'previouspage': page - 1, 'nextpage': page + 1}
        self.render('auditlog.html')


class StopImpersonating(MyHandler):
    def get(self):
        self.session['impersonating_user_email'] = None
        self.redirect('/')
        return


class NotifyAll(MyHandler):
    def get(self):
        count = 0
        families = data.Family.all().fetch(1000)
        for family in families:
            count += 1
            notify_url = '/system/notify/' + str(family.key())
            logging.info('queuing notify task for [%s] at [%s]', family.name, notify_url)
            taskqueue.add(url=notify_url, method='GET')

        message = 'queued tasks for %d families' % (count,)
        logging.info(message)
        self.response.out.write(message)


class NotFound(MyHandler):
    def get(self):
        self.render('notfound.html')
        self.response.set_status(404)


class PopulateData(MyHandler):
    def get(self):
        libraries = {}
        for l in data.Library.all():
            libraries[l.name] = l

        for l in (
            ('Waterloo Public Library', 'wpl'),
            ('Kitchener Public Library', 'kpl'),
            ('Region of Waterloo Library', 'rwl'),
        ):
            lib = libraries.setdefault(l[0], data.Library())
            lib.name = l[0]
            lib.type = l[1]

        db.put(libraries.values())

        self.response.out.write('done')


class Logout(MyHandler):
    def get(self):
        self.session['impersonating_user_email'] = None
        self.session['user_email'] = None
        self.redirect('/')


logging.getLogger().setLevel(logging.DEBUG)
logging.info('running main')
handlers = [
    ('/oauth2/([a-z]+)', OAuth2),
    ('/checkcard/(.*)$', CheckCard),
    ('/savecard', SaveCard),
    ('/removecard/(.*)$', RemoveCard),
    ('/changepin/(.*)/(.*)$', ChangePin),
    ('/admin/notify/(.*)$', AdminNotify),
    ('/system/notify/(.*)$', AdminNotify),
    ('/admin/notifytest/(.*)$', AdminNotifyTest),
    ('/admin/impersonate/(.*)$', Impersonate),
    ('/admin/checkcard/(.*)$', AdminCheckCard),
    ('/system/checkcard/(.*)$', AdminCheckCard),
    ('/admin/checkedcards/(.*)$', ViewCheckedCards),
    ('/admin/auditlog$', AuditLog),
    ('/admin/auditlog/(.*)$', AuditLog),
    ('/$', Welcome),
]

for c in (About, Summary, Account, SaveFamily, AddResponsible, SaveCard, RemoveResponsible, Logout):
    handlers.append(('/' + c.__name__.lower() + '$', c))

for c in (ListFamilies, PopulateData, NotifyAll, CheckAllCards, StopImpersonating, ControlPanel):
    handlers.append(('/admin/' + c.__name__.lower() + '$', c))

for c in (NotifyAll, CheckAllCards):
    handlers.append(('/system/' + c.__name__.lower() + '$', c))

handlers.append(('.*', NotFound))

application = webapp2.WSGIApplication(handlers, debug=True, config=config.webapp2_config)
