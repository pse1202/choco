#-*- coding: utf-8 -*-
import time
import random
from modules import module
from choco.contrib.constants import ContentType
from choco.kakao.response import KakaoResponse

@module.route(u'나가', prefix=False)
def leave(request):
    session_count = len(request.room.sessions)
    leave_list = request.room.list('leaves')
    leave_count = len(leave_list)
    if not leave_list.exists(request.session.id):
        leave_list.append(request.session.id)
        leave_count += 1
    if (session_count <= 3 and leave_count >= session_count - 1) \
        or (session_count > 3 and leave_count >= 3):
        return KakaoResponse(None, content_type=ContentType.Leave)
    else:
        session_count = str(session_count)
        s = u"%s명 중 %s명이 나가를 외치셨습니다."  % (session_count, leave_count) + \
            u"\r\n방 인원이 3명 이상일 경우 최소 3명이 나가를 외치셔야 합니다!" + \
            u"\r\n(그 이하일 경우 모두가 나가를 외치셔야 합니다)"
        return KakaoResponse(s)

@module.route(ur'([가-힣ㄱ-ㅎ\d\s]+)\s{0,}?해봐', re=True)
def order(request, o):
    content = o
    if content.strip() == u'나가':
        out_messages = [u'싫어', u'니가 나가', u'싫으']
        content = random.choice(out_messages)
    return KakaoResponse(content)
