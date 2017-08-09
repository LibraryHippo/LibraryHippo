#!/usr/bin/env python

import wpl


class LibraryAccount(wpl.LibraryAccount):
    def login_url(self):
        return 'https://books.kpl.org/iii/cas/login?service=' + \
               'https://books.kpl.org/patroninfo~S2/j_acegi_cas_security_check&lang=eng&scope=2'
