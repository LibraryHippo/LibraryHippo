#!/usr/bin/env python

import sys

modules = {}

def create(card, fetcher):
    id = card.library.type
    if not modules.has_key(id):
        modules[id] = __import__(id)
    return modules[id].LibraryAccount(card, fetcher)

def main(args=None):
    if args == None:
        args = sys.argv[1:]
    return 0


if __name__ == '__main__':
    sys.exit(main())

