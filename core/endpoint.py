#-*- coding: utf-8 -*-
"""
Python endpoint implementation with regular expression

https://gist.github.com/ssut/6ecf93fac9457dd623b0
"""
import inspect
import re

def endpoint_from_func(func):
    assert func is not None, 'expected func if endpoint is not provided.'
    return func.__name__

class Endpoint(object):
    def __init__(self):
        self.rules = []
        self.functions = {}
        self.prefix = ''

    def __call__(self, *args):
        return self.dispatch(*args)

    def set_prefix(self, prefix):
        self.prefix = re.escape(prefix)

    @property
    def routes(self):
        routes = []
        routes.append(' %-30s| %-20s| %-16s' % ('Rule', 'Endpoint Function', 'Arguments'))
        for regex, endpoint in self.rules:
            args = tuple(inspect.getargspec(self.functions[endpoint]).args)
            route = ' %-30s| %-20s| %-16s' % (regex.pattern, endpoint, args)
            route = u' {:30s}| {:20s}| {:16s}'.format(regex.pattern, endpoint, args)
            routes.append(route)

        return '\n'.join(routes)

    def route(self, rule, **options):
        def decorator(f):
            endpoint = options.pop('endpoint', None)
            self.add_rule(rule, endpoint, f, **options)
            return f
        return decorator

    def add_rule(self, rule, endpoint=None, func=None, **options):
        """
        Basically this example:

            @app.route('f')
            def foo():
                pass

        Is equivalent to the following:

            def foo():
                pass
            app.add_rule('f', 'foo', foo)
        """
        if endpoint is None:
            endpoint = endpoint_from_func(func)
        options['endpoint'] = endpoint

        if func is not None:
            old_func = self.functions.get(endpoint)
            if old_func is not None and old_func != func:
                raise AssertionError('function mapping is overwriting an '
                                     'existing endpoint function: %s', endpoint)
            self.functions[endpoint] = func
            if not options.has_key('re'):
                if not options.has_key('prefix'):
                    rule = re.compile('^' + self.prefix + re.escape(rule) + '$')
                else:
                    rule = re.compile('^' + re.escape(rule) + '$')
            else:
                if not options.has_key('prefix'):
                    if rule.startswith('^'):
                        rule = rule[1:]
                        rule = '^' + self.prefix + rule
                    else:
                        rule = self.prefix + rule
                rule = re.compile(rule)
            rule = (rule, endpoint)
            self.rules.append(rule)

    def dispatch(self, rule, message, session):
        matches = (
            (regex.match(rule), ep) for regex, ep in self.rules
        )

        # print matches
        matches = (
            (match.groups(), ep) for match, ep in matches if match is not None
        )

        for args, endpoint in matches:
            session.validate(message)
            return self.functions[endpoint](message, session, *args)
        return None