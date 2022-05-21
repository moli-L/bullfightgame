# -*- coding: utf-8 -*-

import json
import re
from threading import Thread
from multiprocessing import Queue

from core.model import Message, MessageSendResponse
from core.ws_client import Client
from core.api import WebsocketAPI, MessageAPI

from core.utils import get_logger
logger = get_logger()


"""use example:
bot = Bot()

@bot.command("开始游戏")
def start_handler(ctx: MessageContext, num_player=2):
    ctx.reply(f"已创建{num_player}人房间，等待玩家进入")

# 对应指令：开始游戏 or 开始游戏 2
"""


class MessageContext(Message):
    """每次消息会话上下文，继承消息类多了消息api类调用实例，封装回复消息行为"""

    def __init__(self, message: Message, msg_api: MessageAPI):
        super().__init__(message.__dict__)
        self.msg_api = msg_api

    def reply(self, resp):
        send = MessageSendResponse(resp, self.id)
        return self.msg_api.post_message(self.channel_id, send)
    
    def reply_send(self, send: MessageSendResponse):
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


def _parse_AT_content(content: str) -> str:
    return re.sub(r"<@![0-9]*?>", '', content).strip()


class Handler:
    """事件处理器"""

    def __init__(self):
        # 指令事件分派器与处理器通过消息队列传送message
        self.q_msg = Queue()

    # dispatcher过滤非指令消息，发送指令事件
    def dispatcher(self, message):
        content = _parse_AT_content(message['content'])
        message['content'] = content
        logger.debug("Message content: " + content)
        bot = Bot() #单例
        if not content.startswith(bot.command_prefix): #指令事件过滤
            return
        self.q_msg.put(message)
        
    # handler使用子线程异步处理指令事件
    def handler(self):
        while True:
            try:
                message = self.q_msg.get()
                logger.debug(f"handler recv msg")
            except:
                ...
            message: Message = json.loads(json.dumps(message), object_hook=Message)
            bot = Bot() #单例
            sp = message.content.split()
            command, params = sp[0], _parse_params(sp[1:])
            command = command.replace(bot.command_prefix, '', 1)
            logger.info(f"command: {command}, params: {params}")
            ctx = MessageContext(message, bot.msg_api)
            bot.exec_handler(command, ctx, *params)
    
    def start(self):
        # 事件处理线程启动
        logger.info("[事件处理器]事件处理后台线程启动...")
        thread = Thread(target=self.handler, daemon=True)
        thread.start()


class Bot:
    _inst = False # 单例
    command_prefix = ""

    def __init__(self, command_prefix=None):
        if command_prefix is not None:
            self.command_prefix = command_prefix
    
    def __new__(cls, *args, **kw):
        if not cls._inst:
            cls._inst = object.__new__(cls)
            cls.handle_func = {}
            cls.msg_api = None
        return cls._inst

    def command(self, cmd):
        """
        指令回调注册装饰器：cmd=指令
        """
        def decorate(func):
            assert cmd not in self.handle_func, f"指令{cmd}注册了多个处理函数"
            self.handle_func[cmd] = func
            def wrapper(*args, **kw):
                func(*args, **kw)
            return wrapper
        return decorate
    
    def exec_handler(self, cmd, ctx, *args, **kw):
        if cmd in self.handle_func:
            self.handle_func[cmd](ctx, *args, **kw)
        else:
            # 处理无效指令
            ctx.reply(f"无效指令[{cmd}]")
        
    def run(self, token):
        logger.info("[Bot]程序启动...")
        # 通过api获取websocket链接
        ws_api = WebsocketAPI(token)
        ws_ap = ws_api.ws()
        # 事件处理器
        handler = Handler()
        handler.start()
        # 消息回复类
        self.msg_api = MessageAPI(token)
        # 监听机器人事件ws客户端
        ws_client = Client(token, ws_ap['url'], handler.dispatcher)
        try:
            logger.info("[ws连接]开始ws连接")
            ws_client.connect()
        except KeyboardInterrupt as e:
            logger.info("[ws连接]关闭连接")
            ws_client.disconnect()
            logger.info("程序结束...")

