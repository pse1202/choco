#-*- coding: utf-8 -*-
import time
from modules import module, dispatch, Cache, Result, ResultType

@module.route(u'나가')
def leave(message):
    if Cache.get(message.room, 'admin') == message.user_id:
        text_result = Result(type=ResultType.TEXT, content=u'3초 후에 나간다!')
        dispatch(message.room, text_result)
        time.sleep(3)

        return Result(type=ResultType.LEAVE, content=None)
