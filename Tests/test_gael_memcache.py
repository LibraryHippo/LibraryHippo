#!/usr/bin/env python

from gael.memcache import memoize

class MyCache:
    def __init__(self):
        self.cache = {}

    def get(self, key):
        return self.cache.get(key, None)

    def set(self, key, value, *args):
        self.cache[key] = value

def test__memoize__with_format_string__uses_interpolated_string_for_key():
    values = [1, 2]
    @memoize('hippo %(animal)s zebra', 100)
    def pop_it(animal):
        return values.pop()

    cache = MyCache()
    pop_it.cache = cache
    result = pop_it(animal='rabbit')
    assert 2 == result

    cached_value = cache.get('hippo rabbit zebra')
    assert 2 == cached_value

def test__memoize__second_call__does_not_call_underlying_function():
    count = [0]
    @memoize(lambda args, kwargs: str(kwargs['value']))
    def square_it(value, count=count):
        count[0] += 1
        return value * value

    cache = MyCache()
    square_it.cache = cache

    result = square_it(value=3)
    assert 9 == result 
    assert 1 == count[0]

    second_result = square_it(value=3)
    assert 9 == second_result 
    assert 1 == count[0]
