#-*- coding: utf-8 -*-
"""
CHOCO CLI(Command Line Interface) Handler
"""
import sys
import os
import shlex
import inspect
import imp
import traceback
try:
    import readline
except:
    print >> sys.stderr, 'GNU Readline is not supported by this environment'
from datetime import datetime
from modules import modules

class ChocoCLI(object):
    def __init__(self, choco):
        self.choco = choco

        # get cli methods
        self.commands = dict(inspect.getmembers(self, predicate=inspect.ismethod))
        del self.commands['open']

    def open(self):
        while True:
            command = raw_input('CHOCO ~# ')
            try:
                cmd = shlex.split(command)
                if len(cmd) > 0 and len(cmd[0]) > 0:
                    c = cmd[0]
                    if c in self.commands:
                        del cmd[0]
                        self.commands[c](*cmd)
            except Exception, e:
                traceback.print_exc()

    def status(self):
        now = datetime.now().strftime('%Y/%m/%d %H:%M:%S')
        recv_count = self.choco.cache.get('choco:count:recv')
        exec_count = self.choco.cache.get('choco:count:exec')
        sent_count = self.choco.cache.get('choco:count:sent')
        room_count = self.choco.cache.hlen('choco:rooms')
        session_count = self.choco.cache.hlen('choco:sessions')

        print '[C] {0}'.format(now)
        print 'RECV     : %s' % recv_count
        print 'EXEC     : %s' % exec_count
        print 'SENT     : %s' % sent_count
        print 'ROOMS    : %s' % room_count
        print 'SESSIONS : %s' % session_count
        print 'BUSY     : %s/%s' % (self.choco.working_count.value, self.choco.config.THREAD_COUNT)

    def reload(self):
        print 'RELOADING MODULES ..'
        self.choco.module.rules = []
        self.choco.module.functions = {}
        for m in modules:
            imp.reload(m)
        print 'RELOAD COMPLETE !'

    def exit(self):
        self.choco.exit.value = True
        os._exit(1)
