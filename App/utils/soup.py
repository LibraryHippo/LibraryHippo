#!/usr/bin/env python

from BeautifulSoup import Comment


def remove_comments(element):
    comments = element.findAll(text=lambda text: isinstance(text, Comment))
    [comment.extract() for comment in comments]


def text(element):
    if isinstance(element, unicode):
        return element.strip()
    return [e.strip() for e in element.recursiveChildGenerator() if isinstance(e, unicode) and e.strip()]
