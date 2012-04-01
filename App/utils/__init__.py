#!/usr/bin/env python

def pluralize(items):
    if len(items) ==  1:
        return ''
    else:
        return 's'

def build_notification_subject(info, items_due, holds_ready):
    subject_events = []
    if info:
        subject_events.append(str(len(info)) + ' Message' + pluralize(info))
    if items_due:
        subject_events.append(str(len(items_due)) + ' Item' + pluralize(items_due) + ' Due')
    if holds_ready:
        subject_events.append(str(len(holds_ready)) + ' Hold' + pluralize(holds_ready) + ' Ready')
    return ' and '.join(subject_events)

    

