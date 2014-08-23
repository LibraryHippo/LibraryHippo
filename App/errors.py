#!/usr/bin/env python


class TransientError(Exception):
    def __init__(self, card_status):
        self.card_status = card_status
