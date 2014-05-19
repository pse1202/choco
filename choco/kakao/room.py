#-*- coding: utf-8 -*-
import md5
import pickle
from choco.contrib.cache import ChocoCache, ChocoTextCache, ChocoListCache, ChocoDictCache
from choco.kakao.session import KakaoSession

class KakaoRoom(object):
    def __init__(self, id, data=None):
        self.id = str(id)
        self.created = False

    @staticmethod
    def get_or_create(id, data=None):
        room = str(id)

        key = 'choco:room:%s' % (room)
        if not ChocoCache.adapter.exists(key) and \
            not ChocoCache.adapter.hexists('choco:rooms', room):
            room_object = KakaoRoom(room, data=data)
            room_object = pickle.dumps(room_object)
            multi = ChocoCache.adapter.pipeline()
            multi.hset('choco:rooms', room, room_object)
            room_object = pickle.loads(room_object)
            admin_id = ''
            if 'userId' in data:
                admin_id = str(data['userId'])
            elif 'chatLogs' in data:
                log = data['chatLogs'][0]
                if 'authorId' in log:
                    admin_id = str(log['authorId'])
            elif 'chatLog' in data:
                log  = data['chatLog']
                if 'authorId' in log:
                    admin_id = str(log['authorId'])

            if admin_id:
                multi.hset(key, 'admin', str(admin_id))
                multi.execute()
                room_object.created = True

                # create admin session
                admin = KakaoSession.get_or_create(room_object, admin_id)

            return room_object
        else:
            room_object = ChocoCache.adapter.hget('choco:rooms', room)
            room_object = pickle.loads(room_object)

            return room_object


    def validate(self):
        pass

    def leave(self):
        key = 'choco:room:%s' % (self.id)
        keys = 'choco:room:%s:*' % (self.id)
        sessions = self.sessions
        for session in sessions:
            session.delete()
        multi = ChocoCache.adapter.pipeline()
        for k in ChocoCache.adapter.keys(keys):
            multi.delete(k)
        multi.delete(key)
        multi.hdel('choco:rooms', self.id)
        multi.execute()
        return True

    def list(self, name):
        list_cache = ChocoListCache(room=self, name=name)
        return list_cache

    def dict(self, name):
        dict_cache = ChocoDictCache(room=self, name=name)
        return dict_cache

    def text(self, name):
        text_cache = ChocoTextCache(room=self, name=name)
        return text_cache

    @property
    def sessions(self):
        key = 'choco:room:%s:sessions' % self.id
        session_keys = [k for k in ChocoCache.adapter.smembers(key)]
        sessions = [pickle.loads(ChocoCache.adapter.hget('choco:sessions', s)) \
                     for s in session_keys]

        return sessions

    def __str__(self):
        return '%s' % self.id

    def __repr__(self):
        return '%s' % self.id

    def __unicode__(self):
        return '%r' % self.id

