import webapp2
from google.appengine.api import users


class TryLogin(webapp2.RequestHandler):
    def get(self):
        providers = {
            'Google': 'www.google.com/accounts/o8/id',
            'MyOpenID': 'myopenid.com',
            'Blair Conrad\'s MyOpenID': 'blair.conrad.myopenid.com',
            'Blair Conrad\'s Wordpress': 'blairconrad.wordpress.com',
            'Yahoo': 'yahoo.com',
            'StackExchange': 'openid.stackexchange.com',
        }

        user = users.get_current_user()
        if user:  # signed in already
            self.response.out.write('Hello <em>%s</em>! [<a href="%s">sign out</a>]' % (
                user.nickname(), users.create_logout_url(self.request.uri)))
        else:     # let user choose authenticator
            self.response.out.write('Hello world! Sign in at: ')
            for name, uri in providers.items():
                self.response.out.write('[<a href="%s">%s</a>]' % (
                    users.create_login_url(dest_url='/trylogin', federated_identity=uri), name))

handlers = [
    ('/trylogin$', TryLogin),
]
