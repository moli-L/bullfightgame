# -*- coding: utf-8 -*-

import json

from core.model import Message, MessageSendResponse
from core.ws_client import Client
from core.api import WebsocketAPI, MessageAPI

from core.utils import get_logger
logger = get_logger()


"""use example:
bot = Bot()

@bot.command("开始游戏")
def start_handler(ctx: MessageContext, num_player=2):
    send = MessageSendRequest(f"已创建{num_player}人房间，等待玩家进入", ctx.id)
    ctx.reply(send)

# 对应指令：/开始游戏 or /开始游戏 2
"""


class MessageContext(Message):
    """当次消息会话上下文"""

    def __init__(self, message: Message, msg_api: MessageAPI):
        super().__init__(message.__dict__)
        self.msg_api = msg_api

    def reply(self, resp):
        send = MessageSendResponse(resp, self.id)
        return self.msg_api.post_message(self.channel_id, send)
    
    def reply_embed(self, send: MessageSendResponse):
        send.msg_id = self.id
        return self.msg_api.post_message(self.channel_id, send)


def _parse_params(params):
    def parse_number(s: str):
        try:
            return int(s)
        except ValueError:
            pass
        try:
            return float(s)
        except ValueError:
            pass
        try:
            import unicodedata
            return unicodedata.numeric(s)
        except (TypeError, ValueError):
            pass
        return s

    return [parse_number(p) for p in params]


def dispatch_command(message, token=None):
    bot = Bot()  #单例实例
    if not message['content'].startswith(bot.command_prefix): #指令事件过滤
        return
    message: Message = json.loads(json.dumps(message), object_hook=Message)
    sp = message.content.split()
    command, params = sp[0][1:], _parse_params(sp[1:])
    logger.info(f"command: {command}, params: {params}")
    ctx = MessageContext(message, bot.msg_api or MessageAPI(token))
    bot.exec_handler(command, ctx, *params)


def handle_invalid_command(ctx: MessageContext, cmd):
    ctx.reply(f"无效指令[{cmd}]")


class Bot:
    _inst = False # 单例
    command_prefix = "/"

    def __init__(self, command_prefix=None):
        if command_prefix is not None:
            self.command_prefix = command_prefix
    
    def __new__(cls, *args, **kw):
        if not cls._inst:
            cls._inst = object.__new__(cls)
            cls.handlers = {}
            cls.msg_api = None
        return cls._inst

    def command(self, cmd):
        """
        指令回调注册装饰器：cmd=指令
        """
        def decorate(func):
            assert cmd not in self.handlers, f"指令{cmd}注册了多个处理函数"
            self.handlers[cmd] = func
            def wrapper(*args, **kw):
                func(*args, **kw)
            return wrapper
        return decorate
    
    def exec_handler(self, cmd, ctx, *args, **kw):
        if cmd in self.handlers:
            self.handlers[cmd](ctx, *args, **kw)
        else:
            handle_invalid_command(ctx, cmd)
        
    def run(self, token):
        logger.info("程序启动...")
        # 通过api获取websocket链接
        ws_api = WebsocketAPI(token)
        ws_ap = ws_api.ws()
        # 新建和注册监听事件
        ws_client = Client(token, ws_ap['url'], dispatch_command)
        self.msg_api = MessageAPI(token)
        try:
            logger.info("[ws连接]开始ws连接")
            ws_client.connect()
        except KeyboardInterrupt as e:
            logger.info("[ws连接]关闭连接")
            ws_client.disconnect()
            logger.info("程序结束...")

