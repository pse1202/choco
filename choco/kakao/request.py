#-*- coding: utf-8 -*-

class KakaoRequest(object):
    def __init__(self, room, session, message, attachment=None):
        self.room = room
        self.session = session
        self.message = message
        self.attachment = attachment
