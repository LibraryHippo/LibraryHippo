#!/usr/bin/env python

from fakes import MyOpener, MyResponse

from gael.urlfetch import CookieHandler, RedirectFollower, PayloadEncoder, Transcriber


def test__cookiehandler__response_cookies__saved():

    wrapped_fetcher = MyOpener(MyResponse('my content',
                                          headers={'set-cookie':
                                                   'III_SESSION_ID=0bf0ce5fb384ddda97aff805246ec7a2; ' +
                                                   'path=/, SESSION_SCOPE=0; path=/'}))
    fetcher = CookieHandler(wrapped_fetcher)
    assert 'my content' == fetcher('http://www.google.ca/').content
    assert 'III_SESSION_ID' in fetcher.cookie_jar
    assert 'SESSION_SCOPE' in fetcher.cookie_jar


def test__cookiehandler__client_cookies__sent_with_request():

    wrapped_fetcher = MyOpener(
        MyResponse('my content',
                   headers={'set-cookie': 'III_SESSION_ID=0bf0ce5fb384ddda97aff805246ec7a2; ' +
                            'path=/, SESSION_SCOPE=0; path=/'}),
        'my content2',
    )

    fetcher = CookieHandler(wrapped_fetcher)
    fetcher('http://www.google.ca/')
    fetcher('http://www.google.ca/')

    last_sent_headers = wrapped_fetcher.last_request['headers']
    assert 'III_SESSION_ID=0bf0ce5fb384ddda97aff805246ec7a2; SESSION_SCOPE=0; ' == last_sent_headers['Cookie']


def test__redirect_follower__absolute_redirect__follows():

    wrapped_fetcher = MyOpener(
        MyResponse('my content', headers={'location': 'http://bing.com'}),
        'my content2',
    )

    fetcher = RedirectFollower(wrapped_fetcher)
    response = fetcher('http://www.google.ca/', method='POST', payload={'hippo': 'happy'})
    assert 'my content2' == response.content
    assert 'http://bing.com' == wrapped_fetcher.last_request['url']
    assert 'GET' == wrapped_fetcher.last_request['method']
    assert wrapped_fetcher.last_request['payload'] is None


def test__redirect_follower__relative_redirect__follows():

    wrapped_fetcher = MyOpener(
        MyResponse('my content', headers={'location': '/images/hippo'}),
        'my content2',
    )

    fetcher = RedirectFollower(wrapped_fetcher)
    fetcher('http://www.google.ca/')
    assert 'http://www.google.ca/images/hippo' == wrapped_fetcher.last_request['url']


def test__redirect_follower__no_redirect__stops():

    wrapped_fetcher = MyOpener('my content', 'my content2')
    fetcher = RedirectFollower(wrapped_fetcher)
    response = fetcher('http://www.google.ca/')
    assert 'my content' == response.content


def test__redirect_follower__turns_off_follow_redirects():
    wrapped_fetcher = MyOpener('')
    fetcher = RedirectFollower(wrapped_fetcher)
    fetcher('http://123.com/', 'hippo')

    assert not wrapped_fetcher.last_request['follow_redirects']


def pytest_generate_tests(metafunc):
    if 'decorator' in metafunc.funcargnames:
        for d in [CookieHandler, RedirectFollower, PayloadEncoder, Transcriber]:
            metafunc.addcall(funcargs=dict(decorator=d), id=d.__name__)


def test__decorator__positional_parameters__passed_along(decorator):
    wrapped_fetcher = MyOpener('my content')

    fetcher = decorator(wrapped_fetcher)
    fetcher('http://123.com/', {'hippo': 'happy'})

    assert wrapped_fetcher.last_request['payload'] is not None


def test__decorator__keyword_parameters__passed_along(decorator):
    wrapped_fetcher = MyOpener('my content')

    fetcher = decorator(wrapped_fetcher)
    fetcher('http://123.com/', method='PUT', payload=None, follow_redirects=False, allow_truncated=True, deadline=7)

    assert 'PUT' == wrapped_fetcher.last_request['method']
    assert wrapped_fetcher.last_request['payload'] is None
    assert not wrapped_fetcher.last_request['follow_redirects']
    assert wrapped_fetcher.last_request['allow_truncated']
    assert 7 == wrapped_fetcher.last_request['deadline']


def test__payloadencoder__no_payload__none_sent():
    wrapped_fetcher = MyOpener('my content')

    fetcher = PayloadEncoder(wrapped_fetcher)
    fetcher('http://123.com/')

    assert wrapped_fetcher.last_request['payload'] is None


def test__payloadencoder__dict_payload__encoded_before_request():
    wrapped_fetcher = MyOpener('my content')

    fetcher = PayloadEncoder(wrapped_fetcher)
    fetcher('http://123.com/', {'animal': 'hippo'})

    assert 'animal=hippo' == wrapped_fetcher.last_request['payload']
    assert 'POST' == wrapped_fetcher.last_request['method']


def test__transcriber__one_request__records_request_and_response():
    fetcher = Transcriber(MyOpener('my content'))
    fetcher('http://123.com/')
    assert 2 == len(fetcher.transactions)
