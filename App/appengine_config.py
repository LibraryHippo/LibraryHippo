#!/usr/bin/env python


import sys


def webapp_add_wsgi_middleware(app):
    from google.appengine.ext.appstats import recording
    app = recording.appstats_wsgi_middleware(app)
    return app

# Timezone offset.  This is used to convert recorded times (which are
# all in UTC) to local time.
appstats_TZOFFSET = 0

# DEBUG: True of False.  When True, verbose messages are logged at the
# DEBUG level.  Also, this flag is causes tracebacks to be shown in
# the web UI when an exception occurs.  (Tracebacks are always logged
# at the ERROR level as well.)
appstats_DEBUG = False

# Add any libraries installed in the "lib" folder.
sys.path.append('lib')
