#-*- coding: utf-8 -*-
from modules import module

@module.route(u'안녕')
def hello():
    return u'안녕!'