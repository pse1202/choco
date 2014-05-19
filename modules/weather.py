#-*- coding: utf-8 -*-
import urllib
from xml.etree import ElementTree as ET
from choco.utils.unicode import u
from modules import module
from choco.contrib.constants import ContentType
from choco.kakao.response import KakaoResponse

WEATHER_URL = "http://weather.service.msn.com/data.aspx?weadergreetype=C&culture=ko-kr&weasearchstr={0}"
@module.route(ur'^([가-힣]+)\s{0,}?날씨', re=True, prefix=False)
def forecast(request, place):
    text = u''
    try:
        str_place = u(place)
        xml = urllib.urlopen(WEATHER_URL.format(str_place)).read()
        doc = ET.fromstring(xml)
        current = doc[0][0].attrib

        text = u"[{0} 날씨]\r\n".format(place)
        text += u"기준: {0} {1}\r\n".format(current['date'], current['observationtime'])
        text += u"{0}\r\n".format(current['skytext'])
        text += u"온도: {0}℃\r\n".format(current['temperature'])
        text += u"습도: {0}%".format(current['humidity'])
    except Exception, e:
        text = u"날씨 데이터를 가져오지 못했습니다."

    return KakaoResponse(text)
