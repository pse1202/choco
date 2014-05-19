#-*- coding: utf-8 -*-
"""
CHOCO CLI(Command Line Interface) Handler
"""
import sys
import os
import shlex
import inspect
import imp
import psutil
import pickle
import traceback
import time
try:
    import readline
except:
    print >> sys.stderr, 'GNU Readline is not supported by this environment'
from datetime import datetime
from modules import modules
from .utils.number import sizeof_fmt

class ChocoCLI(object):
    def __init__(self, choco):
        self.choco = choco
        self.first = True

        # get cli methods
        self.commands = dict(inspect.getmembers(self, predicate=inspect.ismethod))
        del self.commands['open']
        del self.commands['__init__']

    def open(self):
        while True:
            if self.first:
                self.first = False
                print 'Welcome to CHOCO Shell'
                print ' * Do not press CTRL + C.'
                print '   If you want to exit choco, just enter "exit".'
                print ' * When you need help, enter "help" or "?".'
                print ''
            command = raw_input('CHOCO ~# ')
            try:
                cmd = shlex.split(command)
                if len(cmd) > 0 and len(cmd[0]) > 0:
                    c = cmd[0].replace('-', '_').replace('?', 'help')
                    if c in self.commands:
                        del cmd[0]
                        self.commands[c](*cmd)
                    else:
                        print 'choco-shell: command not found: {0}'.format(c)
            except Exception, e:
                traceback.print_exc()

    def help(self):
        print ' COMMAND LIST :'
        for c in self.commands:
            print '        {0}'.format(c.replace('_', '-'))

    def send_all(self, message):
        room_list = self.choco.cache.hgetall('choco:rooms')
        for k, v in room_list.iteritems():
            d = {
                'command': 'ADMINMSG',
                'room': pickle.loads(v),
                'message': message,
            }
            self.choco.queue.put(d)
            time.sleep(0.05)

        print 'Success'

    def app_status(self):
        p = psutil.Process(os.getpid())
        cpu_usage = p.get_cpu_percent(interval=1)
        memory_info = p.get_memory_info()
        rss = sizeof_fmt(memory_info.rss)
        vms = sizeof_fmt(memory_info.vms)
        thread_count = p.get_num_threads()
        if os.name != 'nt':
            fd_count = p.get_num_fds()

        print "CPU Usage : {0}%".format(cpu_usage)
        print "Memory    : {0} (RSS), {1} (VMS)".format(rss, vms)
        print "Threads   : {0}".format(thread_count)
        if os.name != 'nt':
            print "FDs       : {0}".format(fd_count)

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
