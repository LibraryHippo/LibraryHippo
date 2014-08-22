import logging
import uuid

from google.appengine.api import users
from google.appengine.api import urlfetch
from google.appengine.api import taskqueue
from google.appengine.ext import db
import webapp2
from webapp2_extras import jinja2

import datetime
from cardchecker import CardChecker
import errors

import data
from app_engine_util import uses_family, send_email
import utils
import utils.times
import utils.filters
from gael.urlfetch import Transcriber, PayloadEncoder, RedirectFollower, CookieHandler

clock = utils.times.Clock()

class MyHandler(webapp2.RequestHandler):

    @webapp2.cached_property
    def jinja(self):
        jinja2.default_config['environment_args']['autoescape'] =False
        j = jinja2.get_jinja2(app=self.app)
        utils.filters.register_all(j.environment)
        return j

    def __init__(self, request, response):
        webapp2.RequestHandler.__init__(self, request, response)
        self.template_values = {}
        self.add_action_urls()

    def handle_exception(self, exception, debug_mode):
        error_uid = uuid.uuid4()
        logging.critical('Error ' + str(error_uid) + ' caught. Unable to proceed.', exc_info=True)

        message_body = str(self.request)
        for attr in ('user', 'family'):
            if hasattr(self.request, attr):
                message_body += '\n' + attr + ': ' + str(getattr(self.request, attr))

        send_email('librarianhippo@gmail.com',
                   'LibraryHippo Error ' + str(error_uid),
                   body=message_body)

        self.template_values['error_uid'] = error_uid
        self.render('error.html')
        self.response.set_status(500)

    def add_action_urls(self):
        if users.get_current_user():
            self.template_values['logout_url'] =  '/logout'
            if users.is_current_user_admin():
                self.template_values['control_panel_url'] = '/static/controlpanel.html'

    def render(self, template_file):
        self.response.out.write(self.jinja.render_template(template_file, **self.template_values))

class Account(MyHandler):
    @uses_family
    def get(self, user, family):
        logging.debug('family = ' + str(family))

        libraries = data.Library.all()

        self.template_values.update({
            'family': family,
            'libraries': libraries,
            'cards': family and list(family.card_set) or [],
            'principals': family and family.principals or [],
            })

        self.render('account.html')

class SaveCard(MyHandler):
    @uses_family
    def post(self, user, family):
        if not family:
            self.redirect('/account')
            return
        
        card = data.Card(parent=family,
                                         family=family,
                                         number=self.request.get('number'),
                                         name=self.request.get('name'),
                                         pin=self.request.get('pin'),
                                         library = data.Library.get(self.request.get('library_id'))
                                         )
        card.put()
        self.redirect('/account')

class RemoveCard(MyHandler):
    @uses_family
    def get(self, user, family, card_key):
        card = data.Card.get(card_key)
        if card.family.key() == family.key():
            logging.info('removing card ' + card.to_xml())
            card.delete()
            family.put()
            logging.info('saved family ' + family.to_xml())
        else:
            logging.error('request to remove card ' + card.to_xml() + ' from family ' + family.to_xml())
        self.redirect('/account')
    
class ChangePin(MyHandler):
    @uses_family
    def get(self, user, family, card_key, new_pin):
        card = data.Card.get(card_key)
        if card.family.key() == family.key():
            logging.info('updating pin for card ' + card.to_xml())
            card.pin = new_pin
            card.put()
            logging.info('saved card')
        else:
            logging.error('request to update pin for card card ' + card.to_xml() + ' that belongs to family ' + family.to_xml())
        self.redirect('/account')
    
class RemoveResponsible(MyHandler):
    @uses_family
    def post(self, user, family):
        removed_a_principal = False
        for principal_email in self.request.arguments():
            principal = users.User(principal_email)
            if principal in family.principals:
                send_email(principal_email,
                           'LibraryHippo: you are no longer a responsible person for the ' + family.name + ' family',
                           body=user.email() + ' has removed you from being a responsible person for the ' + family.name + ' family at LibraryHippo ' +
                           '(http://libraryhippo.com)')
                logging.info('removing principal ' + str(principal))
                family.principals.remove(principal)
                removed_a_principal = True
            else:
                logging.error('request to remove principal ' + str(principal) + ' from family ' + family.to_xml())            

        if len(family.principals) == 0:
            logging.info('no more principals - removing family ' + family.to_xml())
            cards = [c for c in family.card_set]
            db.delete(cards + [family])
        else:
            if removed_a_principal:
                family.put()
                logging.info('saved family ' + family.to_xml())

        self.redirect('/account')
        
class SaveFamily(MyHandler):
    @uses_family
    def post(self, user, family):

        if not family:
            family = data.Family()
            send_email('librarianhippo@gmail.com',
                       'New family ' + self.request.get('name') + ' registered',
                       body = ('registered to '  + str(user)))

        family.name = self.request.get('name')
        if not family.principals:
            family.principals = [user]
        family.put()

        self.redirect('/account')

class AddResponsible(MyHandler):
    @uses_family
    def post(self, user, family):
        if not family:
            self.redirect('/account')

        new_principal = users.User(self.request.get('email'))

        if new_principal not in family.principals:
            if data.Family.all().filter('principals = ', new_principal).count():
                logging.info(new_principal.email() + ' is a member of a different family')
                self.template_values.update({
                    'title': 'User Belongs to Another Family',
                    'message': new_principal.email() + ' is already responsible for another family',
                })
                self.render('info.html')
                return
            else:
                send_email(new_principal.email(),
                           'LibraryHippo: you are now a responsible person for the ' + family.name + ' family',
                           body=user.email() + ' has made you a responsible person for the ' + family.name + ' family.\nLearn more by visiting LibraryHippo' +
                           ' at http://libraryhippo.com')
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
            if status.expires == today  or status.expires == expiry_first_warning_date:
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
    @uses_family
    def get(self, user, family):
        if not family:
            self.redirect('/account')
            return
        
        self.template_values['cards'] = [card for card in family.card_set]
        self.template_values['family'] = family
        
        self.render('summary.html')

class CheckCardBase(MyHandler):
    def check_card(self, user, card):
        fetcher = Transcriber(PayloadEncoder(RedirectFollower(CookieHandler(urlfetch.fetch))))

        checker = CardChecker()
        try:
            card_status = checker.check(user, card, fetcher)
        except errors.TransientError as e:
            self.response.set_status(504)
            card_status = e.card_status

        return card_status

class CheckCard(CheckCardBase):
    @uses_family
    def get(self, user, family, card_key):
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
                template['info'].append(data.CardInfo(c.payload.library_name, c.payload.patron_name, 'Unable to check card for ' + time_since_check + '. <a href="http://libraryhippo.com/about#check_failed">Why?</a>'))
                    
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
            send_email([a.email() for a in family.principals],
                       subject,
                       bcc=template_values['error'] and 'librarianhippo@gmail.com',
                       html = self.jinja.render_template('email.html', **template_values))

class AdminNotifyTest(MyHandler):
    def get(self, family_key):
        for_family = data.Family.get(family_key)
        if not for_family:
            raise Exception('no family')
        template_values = make_test_summary(for_family)

        send_email([a.email() for a in for_family.principals],
                   'LibraryHippo status for ' + for_family.name + ' Family',
                   html = self.jinja.render_template('email.html', **template_values))

class CheckAllCards(MyHandler):
    def get(self):
        cards = data.Card.all().fetch(1000)
        tasks = [taskqueue.Task(url='/admin/checkcard/' + str(card.key()), method='GET') for card in cards]
        q = taskqueue.Queue()
        q.add(tasks)
        logging.info('done')
        self.response.out.write('done')

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

class Impersonate(MyHandler):
    def get(self, username):
        self.response.headers.add_header(
            'Set-Cookie', 'user=%s; path=/' % username)
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
        page = int(page,10)
        now = clock.utcnow()
        events = []
        for e in data.Event.all() \
                .filter('date_time_saved >', now - datetime.timedelta(days=page)) \
                .filter('date_time_saved <', now - datetime.timedelta(days=page-1)) \
                .order('-date_time_saved'):
            logging.debug('Event user = ' + str(e.user))
            events.append(e)
            
        self.template_values = {'events': events, 'previouspage': page-1, 'nextpage': page+1 }
        self.render('auditlog.html')

def remove_user_cookie(response):
        response.headers.add_header('Set-Cookie',
                                    'user=nouser; path=/; expires=Sun, 4-Apr-2010 23:59:59 GMT')

class StopImpersonating(MyHandler):
    def get(self):
        remove_user_cookie(self.response)
        self.redirect('/')
        return

class NotifyAll(MyHandler):
    def get(self):
        families = data.Family.all().fetch(1000)
        for family in families:
            logging.info('queuing ' + family.name)
            taskqueue.add(
                url='/admin/notify/' + str(family.key()),
                method='GET',
                )
        logging.info('done')
        self.response.out.write('done')

class MigrateLibraries(MyHandler):
    def get(self):
        wpl = data.Library(
            key_name='wpl',
            type='wpl',
            name= 'Waterloo')

        wpl.put()

        kpl = data.Library(
            key_name='kpl',
            type='wpl',
            name='Kitchener')

        kpl.put()
        
        self.redirect('/account')

class MigrateCards(MyHandler):
    def get(self):
        user = users.get_current_user()

        logging.debug('user ' + str(user) + ' is an admin? ' + str(users.is_current_user_admin()))
        if not user or not users.is_current_user_admin():
            return

        cards = data.Card.all().fetch(1000)
        for card in cards:
            logging.debug('loaded card ' + card.to_xml())
            card.library = data.Library.get_by_key_name(card.library_id)
            card.put()
            logging.info('saved card ' + card.to_xml())

        self.redirect('/account')

class MigrateUserToPrincipal(MyHandler):
    def get(self):
        families = data.Family.all().fetch(1000)
        for family in families:
            logging.debug('loaded family ' + family.to_xml())
            if family.principals:
                continue
            family.principals = [family.user]
            family.put()
            logging.info('saved family ' + family.to_xml())

        self.redirect('/account')

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
        remove_user_cookie(self.response)
        self.redirect(users.create_logout_url('/'))

class TryLogin(webapp2.RequestHandler):
    def get(self):
        providers = {
            'Google'   : 'www.google.com/accounts/o8/id',
            'MyOpenID' : 'myopenid.com',
            'Blair Conrad\'s MyOpenID' : 'blair.conrad.myopenid.com',
            'Blair Conrad\'s Wordpress' : 'blairconrad.wordpress.com',
            'Yahoo' : 'yahoo.com',
            'StackExchange': 'openid.stackexchange.com',
            }
        
        user = users.get_current_user()
        if user:  # signed in already

            logging.debug('nickname: %s, email: %s, user_id: %s, federated_identity: %s, federated_provider: %s',
                          user.nickname(), user.email(), user.user_id(), user.federated_identity(), user.federated_provider())
            
            self.response.out.write('Hello <em>%s</em>! [<a href="%s">sign out</a>]' % (
                user.nickname(), users.create_logout_url(self.request.uri)))

        else:     # let user choose authenticator
            self.response.out.write('Hello world! Sign in at: ')
            for name, uri in providers.items():
                self.response.out.write('[<a href="%s">%s</a>]' % (
                    users.create_login_url(dest_url= '/trylogin', federated_identity=uri), name))

class OpenIdLoginHandler(MyHandler):
    def get(self):
        continue_url = self.request.GET.get('continue')
        login_url = users.create_login_url(dest_url=continue_url)
        logging.debug('OpenIdLoginHandler: redirecting to %s', login_url)
        
        self.redirect(login_url)        

logging.getLogger().setLevel(logging.DEBUG)
logging.info('running main')
handlers = [
    ('/trylogin$', TryLogin),
    ('/_ah/login_required$', OpenIdLoginHandler),
    ('/checkcard/(.*)$', CheckCard),
    ('/savecard', SaveCard),
    ('/removecard/(.*)$', RemoveCard),
    ('/changepin/(.*)/(.*)$', ChangePin),
    ('/admin/migrateusertoprincipal$', MigrateUserToPrincipal),
    ('/admin/notify/(.*)$', AdminNotify),
    ('/admin/notifytest/(.*)$', AdminNotifyTest),
    ('/admin/impersonate/(.*)$', Impersonate),
    ('/admin/checkcard/(.*)$', AdminCheckCard),
    ('/admin/checkedcards/(.*)$', ViewCheckedCards),
    ('/admin/auditlog$', AuditLog),
    ('/admin/auditlog/(.*)$', AuditLog),
    ('/$', Welcome),
    ]

for c in (About, Summary, Account, SaveFamily, AddResponsible, SaveCard, RemoveResponsible, Logout):
    handlers.append(('/' + c.__name__.lower() + '$', c))

for c in (ListFamilies, PopulateData, MigrateLibraries, MigrateCards, NotifyAll, CheckAllCards, StopImpersonating):
    handlers.append(('/admin/' + c.__name__.lower() + '$', c))

handlers.append(('.*', NotFound))

application = webapp2.WSGIApplication(handlers, debug=True)
