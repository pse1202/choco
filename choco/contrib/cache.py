#-*- coding: utf-8 -*-
"""
choco cache module

ChocoListCache: redis 'set'
ChocoDictCache: redis 'hash'
ChocoTextCache: redis 'string'
"""

class ChocoCache(object):
    def __init__(self, room=None):
        assert room is not None
        self.room = str(room)
        self.key = ''

    def generate_key(self, cache_type, name):
        return 'choco:room:%s:%s:%s' % (self.room, cache_type, name)

    adapter = None

class ChocoListCache(ChocoCache):
    def __init__(self, room=None, name=''):
        assert len(name) > 0
        super(ChocoListCache, self).__init__(room)
        self.key = self.generate_key('list', name)
        self.created = False if self.adapter.exists(self.key) else True

    def __len__(self):
        return self.adapter.scard(self.key)

    def exists(self, value):
        return self.adapter.sismember(self.key, value)

    def append(self, value):
        return self.adapter.sadd(self.key, value)

    def delete(self, value):
        return self.adapter.srem(self.key, value)


class ChocoDictCache(ChocoCache):
    pass

class ChocoTextCache(ChocoCache):
    pass