# -*- coding: utf-8 -*-

class ClientError(RuntimeError):
    def __init__(self, msg):
        self.msgs = msg

    def __str__(self):
        return self.msgs


class NotFoundError(RuntimeError):
    def __init__(self, msg):
        self.msgs = msg

    def __str__(self):
        return self.msgs


class ServerError(RuntimeError):
    def __init__(self, msg):
        self.msgs = msg

    def __str__(self):
        return self.msgs
