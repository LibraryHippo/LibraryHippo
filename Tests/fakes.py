#!/usr/bin/env python


class MyResponse:
    def __init__(self, content, status_code=200, headers={}, final_url='http://www.google.ca/'):
        self.content = content
        self.content_was_truncated = False
        self.status_code = 200
        self.headers = headers
        self.final_url = final_url


class MyOpener:
    def __init__(self, *responses):
        self.responses = []
        for response in responses:
            if not isinstance(response, MyResponse):
                response = MyResponse(response)
            self.responses.append(response)

    def __call__(self, url,
                 payload=None, method='GET', headers={}, allow_truncated=False, follow_redirects=True, deadline=None):
        self.last_request = {
            'url': url,
            'payload': payload,
            'method': method,
            'headers': headers,
            'allow_truncated': allow_truncated,
            'follow_redirects': follow_redirects,
            'deadline': deadline
        }
        print 'request', self.last_request

        response = self.responses.pop(0)
        print 'response', response
        return response


class MyLibrary:
    def __init__(self):
        self.type = 'MyPL'
        self.name = 'My Public Library'


class MyCard:
    def __init__(self):
        self.library = MyLibrary()
        self.name = 'Name'
        self.number = 'Number'
        self.pin = 'pin'


class StoppedClock:
    def __init__(self, dt):
        self.dt = dt

    def today(self):
        return self.dt.date()

    def utcnow(self):
        return self.dt
