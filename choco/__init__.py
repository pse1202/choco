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
import traceback
import base64
import json
import redis
import socket
import curses
from ctypes import c_int, c_bool
from threading import Thread
from multiprocessing import Process, Value, Lock, Queue, Manager
from collections import namedtuple
from datetime import datetime

from .endpoint import Endpoint
from .utils.image import get_image_size
from .kakao.response import KakaoResponse
from .kakao.room import KakaoRoom
from .kakao.session import KakaoSession
from .contrib.cache import ChocoCache
from .contrib.constants import ContentType
from .cli import ChocoCLI

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
        self.pool = [Thread(target=self.start) for i in range(config.THREAD_COUNT)]
        self.working_count = Value(c_int)
        self.working_count_lock = Lock()
        if os.name is 'nt':
            self.watch_process = Thread(target=self.watch)
            self.ping_process = Thread(target=self.auto_ping)
        else:
            self.watch_process = Process(target=self.watch)
            self.ping_process = Process(target=self.auto_ping)
        self.exit = Value(c_bool)
        self.kakao = None

        redis_pool = redis.ConnectionPool(host=config.REDIS_HOST,
            port=config.REDIS_PORT,
            db=config.REDIS_DB,
            password=config.REDIS_PASSWORD)
        self.cache = ChocoCache.adapter = redis.Redis(connection_pool=redis_pool)
        self.module = Endpoint()
        self.module.set_prefix(config.COMMAND_PREFIX)

        self.cli = ChocoCLI(self)

        auth_mail = self.cache.hget('choco_auth', 'mail')
        auth_pass = self.cache.hget('choco_auth', 'password')
        auth_client = self.cache.hget('choco_auth', 'client')
        auth_x_vc = self.cache.hget('choco_auth', 'x_vc')
        if self.cache.hexists('choco_auth', 'uuid_base64'):
            auth_uuid = self.cache.hget('choco_auth', 'uuid_base64')
        else:
            auth_uuid = base64.b64encode(self.cache.hget('choco_auth', 'uuid'))

        if not auth_client:
            print >> sys.stderr, "Authenticate failed: client name not found\n" + \
                "Please check config.py and set 'choco_auth' to redis server"
            sys.exit(1)
        elif not auth_uuid:
            print >> sys.stderr, "Authenticate failed: uuid not found\n" + \
                "Please check config.py and set 'choco_auth' to redis server"
            sys.exit(1)

        self.load_module()
        if self.auth_kakao(auth_mail, auth_pass, auth_client, auth_uuid, auth_x_vc):
            print >> sys.stdout, 'Successfully connected to KakaoTalk server'

    def load_module(self):
        from modules import init_module, module_loader
        init_module(self, self.module)
        module_loader(home, self.config)

    def auth_kakao(self, mail, password, client, uuid, x_vc):
        user_session = self.cache.hget('choco_session', 'key')
        user_id = self.cache.hget('choco_session', 'id')

        if not user_session or not user_id:
            if not mail:
                print >> sys.stderr, "Authenticate failed: email address not found\n" + \
                    "Please check config.py and set 'choco_auth' to redis server"
                sys.exit(1)
            elif not password:
                print >> sys.stderr, "Authenticate failed: password not found\n" + \
                    "Please check config.py and set 'choco_auth' to redis server"
                sys.exit(1)
            elif not x_vc:
                print >> sys.stderr, "Authenticate failed: X-VC token not found\n" + \
                    "Please check config.py and set 'choco_auth' to redis server"
                sys.exit(1)

            self.kakao = kakaotalk(debug=self.config.DEBUG)
            auth_result = self.kakao.auth(mail, password, client, uuid, x_vc)
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
            self.exit.value = False
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
        bot.watch_process.start()
        bot.cli.open()

    def watch(self):
        while not self.exit.value:
            try:
                data = self.kakao.translate_response()
                if not data:
                    print >> sys.stderr, \
                        'WARNING: data is None. probably socket is disconnected?'
                    self.reload_kakao()
                    break
                elif data['command'] == 'MSG':
                    body = data['body']
                    if 'chatId' in body:
                        chatId = str(body['chatId'])
                        exists = self.cache.hexists('choco:rooms', chatId)
                        if not exists:
                            data['command'] = 'NEW'

                    self.queue.put(data)
                    self.cache.incr('choco:count:recv')
                elif data['command'] == 'DECUNREAD' or data['command'] == 'WELCOME':
                    body = data['body']
                    if 'chatId' in body:
                        chatId = str(body['chatId'])
                        exists = self.cache.hexists('choco:rooms', chatId)
                        if not exists:
                            data['command'] = 'NEW'
                            self.queue.put(data)
            except socket.timeout, e:
                print >> sys.stderr, 'ERROR: socket timeout'
            except KeyboardInterrupt, e:
                self.send_exit()
                self.exit.value = True
            except Exception, e:
                print >> sys.stderr, e
                self.send_exit()
                self.exit.value = True

    def auto_ping(self):
        while not self.exit.value:
            ping_success = False
            try:
                self.kakao.ping(False)
                ping_success = True
            except Exception, e:
                pass
            time.sleep(30)

    def send_exit(self):
        for t in self.pool:
            self.queue.put({ 'exit': True })

    def start(self):
        while not self.exit.value:
            item = self.queue.get()
            if 'exit' in item: break
            with self.working_count_lock:
                self.working_count.value += 1
            self.cache.incr('choco:count:exec')
            cmd = item['command']

            if cmd == 'MSG':
                data = item['body']
                attachment = None
                if 'attachment' in data['chatLog']:
                    try:
                        attachment = json.loads(data['chatLog']['attachment'])
                    except:
                        pass
                try: t = datetime.fromtimestamp(data['chatLog']['sendAt'])
                except Exception, e:
                    t = None

                nick = data['authorNickname']
                user_id = str(data['chatLog']['authorId'])
                try: nick = nick.encode('utf-8') if isinstance(nick, unicode) else nick
                except UnicodeDecodeError, e:
                    pass

                room = KakaoRoom.get_or_create(data['chatId'])

                message = Message(room=room, user_id=user_id,
                    user_nick=nick, text=data['chatLog']['message'],
                    attachment=attachment, time=t)

                th = self.dispatch(room, message)
            elif cmd == 'NEW':
                data = item['body']
                room = data['chatId']
                created = False
                try:
                    room = KakaoRoom.get_or_create(room, data=data)
                    created = room.created
                except:
                    pass

                if created:
                    content = u"[초코봇]\r\n안녕하세요. 나가기를 원하면 '나가'를 입력해주세요."
                    message = KakaoResponse(content)
                    self.dispatch(room, message, True)
            elif cmd == 'ADMINMSG':
                room = item['room']
                content = item['message']
                message = KakaoResponse(content)
                self.dispatch(room, message, True)

            with self.working_count_lock:
                self.working_count.value -= 1

    def dispatch(self, room, message, child=False):
        if not child:
            session = KakaoSession.get_or_create(room, message.user_id)
            result = self.module(message.text, message, room, session)
        else: result = message

        if result:
            room_id = int(room.id)
            try:
                if result.content_type == ContentType.Text:
                    self.kakao.write(room_id, result.content, False)
                elif result.content_type == ContentType.Image:
                    content = result.content
                    size = get_image_size(content)
                    url = self.kakao.upload_image(content)
                    if url is not None:
                        self.kakao.write_image(room_id, url, size[0], size[1], False)
                    else:
                        print >> sys.stderr, 'WARNING: Failed to upload photo'
                    if 'tmp' in content and os.path.isfile(content):
                        os.remove(content)
                elif result.content_type == ContentType.Leave:
                    room.leave()
                    self.kakao.leave(room_id, False)
                self.cache.incr('choco:count:sent')
            except Exception, e:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                self.kakao.write(room_id, u'명령어 처리 도중 서버오류가 발생했습니다.', False)
                error = str(e) + ' ' + ''.join(traceback.format_tb(exc_traceback))
                self.cache.sadd('choco:errors', error)