#-*- coding: utf-8 -*-
"""
CHOCO CLI(Command Line Interface) Handler
"""
import shlex
import inspect

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
                        print self.commands[c](*cmd)
            except:
                pass

    def test(self):
        return 1
