#-*- coding: utf-8 -*-
"""
choco.py - An KakaoTalk Bot
Copyright 2014, ssut
Licensed under the MIT License.

Do you like chocopy? :)
"""

import time
import os
import sys
import base64
import json
import redis
import socket
from multiprocessing import Process, Queue
from collections import namedtuple
from datetime import datetime

from lib.endpoint import Endpoint
from lib.image import get_image_size
from lib.run_async import run_async
from modules import Cache, Session, Result, ResultType

home = os.getcwd()
sys.path.append(os.path.join(home, 'modules'))
sys.path.append(os.path.join(home, 'pykakao'))
from pykakao import kakaotalk

Message = namedtuple('Message', ['room', 'user_id', 'user_nick', 'text', 'attachment', 'time'])
class Choco(object):
    def __init__(self, config):
        self.config = config
        self.queue = Queue(10000)
        self.count = 0
        self.pool = [Process(target=self.process) for i in range(config.WORKER_COUNT)]
        self.ping_process = Process(target=self.auto_ping)
        self.exit = False
        self.kakao = None

        redis_pool = redis.ConnectionPool(host=config.REDIS_HOST,
            port=config.REDIS_PORT,
            db=config.REDIS_DB,
            password=config.REDIS_PASSWORD)
        self.cache = redis.Redis(connection_pool=redis_pool)
        self.module = Endpoint()
        self.module.set_prefix(config.COMMAND_PREFIX)

        auth_mail = self.cache.hget('choco_auth', 'mail')
        auth_pass = self.cache.hget('choco_auth', 'password')
        auth_client = self.cache.hget('choco_auth', 'client')
        auth_uuid = base64.b64encode(self.cache.hget('choco_auth', 'uuid'))

        if not auth_mail:
            print >> sys.stderr, "Authenticate failed: email address not found\n" + \
                "Please check config.py and set 'choco_auth' to redis server"
            sys.exit(1)
        elif not auth_pass:
            print >> sys.stderr, "Authenticate failed: password not found\n" + \
                "Please check config.py and set 'choco_auth' to redis server"
            sys.exit(1)
        elif not auth_client:
            print >> sys.stderr, "Authenticate failed: client name not found\n" + \
                "Please check config.py and set 'choco_auth' to redis server"
            sys.exit(1)
        elif not auth_uuid:
            print >> sys.stderr, "Authenticate failed: uuid not found\n" + \
                "Please check config.py and set 'choco_auth' to redis server"
            sys.exit(1)

        self.load_module()
        if self.auth_kakao(auth_mail, auth_pass, auth_client, auth_uuid):
            print >> sys.stdout, 'Successfully connected to KakaoTalk server'

    def load_module(self):
        from modules import init_module, module_loader
        init_module(self, self.module)
        module_loader(home, self.config)

    def auth_kakao(self, mail, password, client, uuid):
        user_session = self.cache.hget('choco_session', 'key')
        user_id = self.cache.hget('choco_session', 'id')

        if not user_session or not user_id:
            self.kakao = kakaotalk(debug=self.config.DEBUG)
            auth_result = self.kakao.auth(mail, password, client, uuid)
            if not auth_result:
                print >> sys.stderr, "KakaoTalk auth failed"
                sys.exit(1)
            else:
                login_result = self.kakao.login()
                if not login_result:
                    print >> sys.stderr, "KakaoTalk login failed"
                    sys.exit(1)
                else:
                    self.cache.hset('choco_session', 'key', self.kakao.session_key)
                    self.cache.hset('choco_session', 'id', self.kakao.user_id)
        else:
            self.kakao = kakaotalk(user_session, uuid, user_id,
                debug=self.config.DEBUG)
            login_result = self.kakao.login()
            if not login_result:
                print >> sys.stderr, "KakaoTalk login failed"
                sys.exit(1)

        return True

    def reload_kakao(self):
        print >> sys.stdout, 'Trying to reconnect..'
        self.ping_process.stop()
        for p in self.pool:
            p.stop()
        while not self.queue.empty():
            self.queue.get()
        self.kakao.s.close()
        user_session = self.kakao.session_key
        uuid = self.kakao.device_uuid
        user_id = self.kakao.user_id
        del self.kakao
        self.kakao = kakaotalk(user_session, uuid, user_id, debug=self.config.DEBUG)
        login = self.kakao.login()
        if login:
            print >> sys.stdout, 'Reconnected'
            self.exit = False
            self.ping_process.start()
            for p in self.pool:
                p.start()
            self.watch()
        else:
            print >> sys.stderr, 'ERROR: failed to re-authorize to KakaoTalk'

    @staticmethod
    def run(config):
        bot = Choco(config)
        bot.ping_process.start()
        for p in bot.pool:
            p.start()
        bot.watch()

    def watch(self):
        while not self.exit:
            try:
                data = self.kakao.translate_response()
                if not data:
                    print >> sys.stderr, 'WARNING: data is None. probably socket is disconnected?'
                    self.reload_kakao()
                    break
                elif data['command'] == 'MSG':
                    self.queue.put(data)
                    self.cache.incr('choco:count:recv')
                elif data['command'] == 'DECUNREAD':
                    body = data['body']
                    if 'chatId' in body:
                        chatId = str(body['chatId'])
                        exists = self.cache.sismember('choco:rooms', chatId)
                        if not exists:
                            data['command'] = 'NEW'
                            self.queue.put(data)
            except socket.timeout, e:
                print >> sys.stderr, 'ERROR: socket timeout'
            except KeyboardInterrupt, e:
                self.exit = True
            except Exception, e:
                print >> sys.stderr, e
                self.exit = True

    def auto_ping(self):
        while not self.exit:
            ping_success = False
            try:
                self.kakao.ping(False)
                ping_success = True
            except Exception, e:
                pass
            self.print_log(ping_success)
            time.sleep(60)

    def print_log(self, ping_success):
        now = datetime.now().strftime('%Y/%m/%d %H:%M:%S')
        recv_count = self.cache.get('choco:count:recv')
        exec_count = self.cache.get('choco:count:exec')
        sent_count = self.cache.get('choco:count:sent')
        room_count = self.cache.scard('choco:rooms')
        session_count = self.cache.hlen('choco:sessions')
        ping = '*' if ping_success is True else '-'
        print >> sys.stdout, '[{0}] {1}'.format(ping, now)
        print >> sys.stdout, 'RECV     : %s' % recv_count
        print >> sys.stdout, 'EXEC     : %s' % exec_count
        print >> sys.stdout, 'SENT     : %s' % sent_count
        print >> sys.stdout, 'ROOMS    : %s' % room_count
        print >> sys.stdout, 'SESSIONS : %s' % session_count
        pass

    def process(self):
        while not self.exit:
            item = self.queue.get()
            self.cache.incr('choco:count:exec')
            cmd = item['command']

            if cmd == 'MSG':
                data = item['body']
                attachment = None
                if 'attachment' in data['chatLog']:
                    attachment = json.loads(data['chatLog']['attachment'])
                try: t = datetime.fromtimestamp(data['chatLog']['sendAt'])
                except Exception, e:
                    t = None

                nick = data['authorNickname']
                user_id = str(data['chatLog']['authorId'])
                try: nick = nick.encode('utf-8') if isinstance(nick, unicode) else nick
                except UnicodeDecodeError, e:
                    pass

                message = Message(room=data['chatId'], user_id=user_id,
                    user_nick=nick, text=data['chatLog']['message'],
                    attachment=attachment, time=t)

                self.dispatch(data['chatId'], message)
            elif cmd == 'NEW':
                data = item['body']
                room = data['chatId']
                Cache.enter(room, data)

                content = u"[초코봇]\r\n방에 초대하신 분만 /나가/를 사용하실 수 있습니다."
                message = Result(type=ResultType.TEXT, content=content)
                self.dispatch(room, message, True)

    @run_async
    def dispatch(self, room, message, child=False):
        if not child:
            session = Session.get_or_create(room, message.user_id)
            result = self.module(message.text, message, session)
        else: result = message
        if result:
            if result.type is ResultType.TEXT:
                self.kakao.write(room, result.content, False)
            elif result.type is ResultType.IMAGE:
                content = result.content
                size = get_image_size(content)
                url = self.kakao.upload_image(content)
                if url:
                    self.kakao.write_image(room, url, size[0], size[1], False)
                else:
                    print >> sys.stderr, 'WARNING: Failed to upload photo'
            elif result.type is ResultType.LEAVE:
                Cache.leave(room)
                self.kakao.leave(room, False)
            self.cache.incr('choco:count:sent')
