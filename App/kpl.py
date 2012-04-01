#!/usr/bin/env python

import wpl

class LibraryAccount(wpl.LibraryAccount): 
    def login_url(self):
        return 'https://books.kpl.org/iii/cas/login?service=https://books.kpl.org/patroninfo~S1%2FIIITICKET&scope=3'




    
