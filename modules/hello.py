#-*- coding: utf-8 -*-
import os
from modules import module, Result, ResultType

@module.route(u'안녕')
def hello(message, session):
    resp = '안녕 {0}!'.format(session.nick)
    return Result(type=ResultType.TEXT, content=resp)

@module.route(u'(\d+)\+(\d+)', re=True)
def sum_value(message, session, a, b):
    resp = '{0} + {1} = {2}'.format(a, b, int(a) + int(b))
    return Result(type=ResultType.TEXT, content=resp)

@module.route(u'사진', prefix=False)
def hello_photo(message, session):
    if message.attachment:
        return None
        # return Result(type=ResultType.TEXT, content=u'사진 받았다!')
    else:
        image = os.path.join('sample', 'image.png')
        return Result(type=ResultType.IMAGE, content=image)