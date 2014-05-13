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
import redis
from multiprocessing import Process, Queue

from lib.endpoint import Endpoint
from lib.run_async import run_async

home = os.getcwd()
sys.path.append(os.path.join(home, 'modules'))
sys.path.append(os.path.join(home, 'pykakao'))
from pykakao import kakaotalk

class Choco(object):
    def __init__(self, config):
        self.config = config
        self.queue = Queue(10000)
        self.pool = [Process(target=self.process) for i in range(config.WORKER_COUNT)]
        self.exit = False

        redis_pool = redis.ConnectionPool(host=config.REDIS_HOST,
            port=config.REDIS_PORT,
            db=config.REDIS_DB,
            password=config.REDIS_PASSWORD)
        self.cache = redis.Redis(connection_pool=redis_pool)
        self.module = Endpoint()

        auth_mail = self.cache.hget('choco_auth', 'mail')
        auth_pass = self.cache.hget('choco_auth', 'password')
        auth_client = self.cache.hget('choco_auth', 'client')
        auth_uuid = self.cache.hget('choco_auth', 'uuid')

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

    def load_module(self):
        from modules import set_endpoint, module_loader
        set_endpoint(self.module)
        module_loader(home, self.config)

    @staticmethod
    def run(config):
        bot = Choco(config)
        for p in bot.pool:
            p.start()
        bot.watch()

    def watch(self):
        while True:
            pass

    def process(self):
        pass

    @run_async
    def dispatch(self):
        pass
