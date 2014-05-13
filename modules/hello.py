#-*- coding: utf-8 -*-
import os
from modules import module, Result, ResultType

@module.route(u'안녕')
def hello(message):
    resp = '안녕 {0}!'.format(message.user_nick)
    return Result(type=ResultType.TEXT, content=resp)

@module.route(u'(\d+)\+(\d+)', re=True)
def sum_value(message, a, b):
    resp = '{0} + {1} = {2}'.format(a, b, int(a) + int(b))
    return Result(type=ResultType.TEXT, content=resp)

@module.route(u'사진')
def hello_photo(message):
    if message.attachment:
        return Result(type=ResultType.TEXT, content=u'사진 받았다!')
    else:
        image = os.path.join('sample', 'image.png')
        print image
        return Result(type=ResultType.IMAGE, content=image)