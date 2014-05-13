import os
import sys
import imp
from collections import namedtuple

Result = namedtuple('Result', ['type', 'content'])
module = None

class ResultType:
    TEXT = 0
    IMAGE = 1
    LEAVE = 2

def set_endpoint(ep):
    global module
    module = ep

def module_loader(home, config):
    for fn in os.listdir(os.path.join(home, 'modules')):
        name = os.path.basename(fn)[:-3]
        if name in config.EXCLUDED_MODULES: continue
        if fn.endswith('.py') and not fn.startswith('_'):
            fn = os.path.join(os.path.dirname(os.path.realpath(__file__)), fn)
            try: imp.load_source(name, fn)
            except Exception, e:
                print >> sys.stderr, "Error loading %s: %s" % (name, e)
                sys.exit(1)
