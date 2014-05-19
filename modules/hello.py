#-*- coding: utf-8 -*-
import os
from modules import module
from choco.contrib.constants import ContentType
from choco.kakao.response import KakaoResponse

@module.route(u'안녕')
def hello(request):
    nick = request.session.nick
    resp = '안녕 {0}!'.format(nick)
    return KakaoResponse(resp)
