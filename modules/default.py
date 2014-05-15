#-*- coding: utf-8 -*-
import time
from modules import module, dispatch, Cache, Result, ResultType

@module.route(u'나가', prefix=False)
def leave(message, session):
    sessions = Cache.session_count(message.room)
    leave_count = Cache.s_count(message.room, 'leaves')
    if not Cache.s_exists(message.room, 'leaves', session.user):
        Cache.sadd(message.room, 'leaves', session.user)
        leave_count += 1
    if (sessions <= 3 and leave_count > 0) or (sessions > 3 and leave_count >= 2):
        return Result(type=ResultType.LEAVE, content=None)
    else:
        sessions = str(sessions)
        s = u"%s명 중 %s명이 나가를 외치셨습니다.\r\n방 인원이 3명 이상일 경우 최소 2명이 나가를 외치셔야 합니다!" % (sessions, leave_count)
        return Result(type=ResultType.TEXT, content=s)
