import os
import sys
import imp
import pickle
import traceback
import md5
from collections import namedtuple

Result = namedtuple('Result', ['type', 'content'])
choco = None
module = None

def init_module(cc, ep):
    global choco, module
    choco = cc
    module = ep

def dispatch(room, message):
    choco.dispatch(room, message, True)

def module_loader(home, config):
    for fn in os.listdir(os.path.join(home, 'modules')):
        name = os.path.basename(fn)[:-3]
        if name in config.EXCLUDED_MODULES: continue
        if fn.endswith('.py') and not fn.startswith('_'):
            fn = os.path.join(os.path.dirname(os.path.realpath(__file__)), fn)
            try: imp.load_source(name, fn)
            except Exception, e:
                traceback.print_exc()
                print >> sys.stderr, "Error loading %s: %s" % (name, e)
                sys.exit(1)

class Cache(object):
    @staticmethod
    def get(room, name):
        key = 'choco:room:' + str(room)
        return choco.cache.hget(key, name)

    @staticmethod
    def get_incr(room, name):
        key = 'choco:room:' + str(room) + ':' + name
        c = choco.cache.get(key)
        if not c:
            return 0
        else:
            return int(c)

    @staticmethod
    def session_count(room):
        room_key = 'choco:room:' + str(room) + ':sessions'
        return choco.cache.scard(room_key)

    @staticmethod
    def incr(room, name):
        key = 'choco:room:' + str(room) + ':' + name
        choco.cache.incr(key)

    @staticmethod
    def sadd(room, name, item):
        key = 'choco:room:' + str(room) + ':' + name
        choco.cache.sadd(key, item)

    @staticmethod
    def s_count(room, name):
        key = 'choco:room:' + str(room) + ':' + name
        c = choco.cache.scard(key)
        if not c:
            return 0
        else:
            return c

    @staticmethod
    def s_exists(room, name, item):
        key = 'choco:room:' + str(room) + ':' + name
        return choco.cache.sismember(key, item)

    @staticmethod
    def enter(room, data):
        r = str(room)
        if not r or r == '': return None
        key = 'choco:room:' + r
        if choco.cache.exists(key): return None
        p = choco.cache.pipeline()
        p.sadd('choco:rooms', r)

        admin_id = ''
        if 'userId' in data:
            admin_id = str(data['userId'])
        elif 'chatLogs' in data:
            log = data['chatLogs'][0]
            if 'authorId' in log:
                admin_id = str(log['authorId'])

        if admin_id:
            p.hset(key, 'admin', str(admin_id))
        else:
            return None # admin not found
        p.execute()

        return Session.get_or_create(room, str(data['userId']))

    @staticmethod
    def leave(room):
        r = str(room)
        key = 'choco:room:' + r
        keys = 'choco:room:' + r + ':*'
        session = 'choco:room:' + r + ':sessions'
        p = choco.cache.pipeline()
        # remove session from room session set(list)
        for s in choco.cache.smembers(session):
            p.hdel('choco:sessions', s)
        # remove room
        p.srem('choco:rooms', r)
        # delete room hash
        p.delete(key)
        # delete keys
        for k in choco.cache.keys(keys):
            p.delete(k)
        # delete session set
        p.delete(session)
        p.execute()
        return True

class Session(object):
    def __init__(self, room, user, nick=''):
        self.room = str(room)
        self.user = str(user)
        self.nick = nick

    @staticmethod
    def generate_key(room, user):
        key = str(room) + ':' + str(user)
        return md5.md5(key).hexdigest()

    @staticmethod
    def get_or_create(room, user, nick=''):
        room = str(room)
        user = str(user)
        key = Session.generate_key(room, user)
        # if session is already exists
        if choco.cache.hexists('choco:sessions', key):
            session = choco.cache.hget('choco:sessions', key)
            return pickle.loads(session)
        else:
            # room session set(list)
            room_key = 'choco:room:' + room + ':sessions'
            # create session object
            session = Session(room, user, nick)
            session = pickle.dumps(session)
            p = choco.cache.pipeline()
            # set session to choco sessions
            p.hset('choco:sessions', key, session)
            # add session key to room set(list)
            p.sadd(room_key, key)
            p.execute()
            session = pickle.loads(session)
            return session

    def validate(self, message):
        if (self.nick == '' or self.nick != message.user_nick) \
        and len(message.user_nick) > 0:
            self.nick = message.user_nick
            self.save()

    def save(self):
        key = Session.generate_key(self.room, self.user)
        updated = pickle.dumps(self)
        choco.cache.hset('choco:sessions', key, updated)

    @property
    def is_admin(self):
        admin_id = Cache.get(self.room, 'admin')
        return admin_id == self.user