#-*- coding: utf-8 -*-
import urllib
import json
import time
import traceback
import random
from core.ext.unicode import u
from core.ext.temp import generate_temp_name
from modules import module, dispatch, Result, ResultType

SEARCH_PIC_URL = "http://ajax.googleapis.com/ajax/services/search/images?v=1.0&imgsz=middle&rsz=8&q={0}"
@module.route(ur'^([가-힣a-zA-Z0-9\s]+)\s{0,}?사진\s{0,}?(구해|가져|찾아|검색|내놔)', re=True, prefix=False)
def search_photo(message, sessionm, pic_name, pic_command):
    resp_type = None
    resp_content = None
    try:
        url = SEARCH_PIC_URL.format(u(pic_name))
        data = urllib.urlopen(url).read()

        j = json.loads(data)
        if len(j['responseData']['results']) is 0:
            resp_type = ResultType.TEXT
            resp_content = u'검색결과가 없습니다.'

        d = random.choice(j['responseData']['results'])
        tmp = generate_temp_name()
        link = d['unescapedUrl']

        urllib.urlretrieve(link, tmp)

        resp_type = ResultType.IMAGE
        resp_content = tmp
    except Exception, e:
        resp_type = ResultType.TEXT
        resp_content = u'사진을 가져오지 못했습니다'

    return Result(type=resp_type, content=resp_content)