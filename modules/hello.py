#-*- coding: utf-8 -*-
from modules import module, Result, ResultType

@module.route(u'안녕')
def hello(message):
    return Result(type=ResultType.TEXT, content=u'안녕!')

@module.route(u'(\d+)\+(\d+)', re=True)
def sum_value(message, a, b):
    resp = '{0} + {1} = {2}'.format(a, b, int(a) + int(b))
    return Result(type=ResultType.TEXT, content=resp)

@module.route(u'사진')
def hello_photo(message):
    if message.attachment:
        return Result(type=ResultType.TEXT, content=u'사진 받았다!')