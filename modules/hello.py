#-*- coding: utf-8 -*-
from modules import module, Result

@module.route(u'안녕')
def hello(message):
    return Result(text=u'안녕!', image=None)

@module.route(u'사진')
def hello_photo(message):
    if message.attachment:
        return Result(text=u'사진 받았다!', image=None)