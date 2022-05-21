# -*- coding: utf-8 -*-

import json
import threading
import websocket
import traceback
from enum import Enum

from core.utils import get_logger
logger = get_logger()


"""websocket长链接
1. connect -> 连接到 Gateway: 利用 /gateway 获取到的网关地址，将返回心跳周期
2. identify -> 鉴权连接：传入token、intents、shard (分片)
3. 启动心跳线程（设置为守护线程）
4. 处理事件（消息事件）
"""


""" 监听@消息事件 """
INTENT_PUBLIC_GUILD_MESSAGES = 1 << 30  # // 消息事件，此为公域的消息事件
#   - AT_MESSAGE_CREATE                   // 当收到@机器人的消息，或者回复机器人消息时
#   - PUBLIC_MESSAGE_DELETE               // 当频道的消息被删除时

""" 监听所有消息事件 """
INTENT_GUILD_MESSAGES = 1 << 9    # // 消息事件，仅 *私域* 机器人能够设置此 intents。
#   - MESSAGE_CREATE                // 发送消息事件，代表频道内的全部消息，而不只是 at 机器人的消息。内容与 AT_MESSAGE_CREATE 相同
#   - MESSAGE_DELETE                // 删除（撤回）消息事件


class OpCode(Enum):
    """
    CODE	名称	客户端操作	描述
    0	Dispatch	Receive	服务端进行消息推送
    1	Heartbeat	Send/Receive	客户端或服务端发送心跳
    2	Identify	Send	客户端发送鉴权
    6	Resume	Send	客户端恢复连接
    7	Reconnect	Receive	服务端通知客户端重新连接
    9	Invalid Session	Receive	当identify或resume的时候，如果参数有错，服务端会返回该消息
    10	Hello	Receive	当客户端与网关建立ws连接之后，网关下发的第一条消息
    11	Heartbeat ACK	Receive	当发送心跳成功之后，就会收到该消息
    """
    WS_DISPATCH_EVENT = 0
    WS_HEARTBEAT = 1
    WS_IDENTITY = 2
    WS_RESUME = 6
    WS_RECONNECT = 7
    WS_INVALID_SESSION = 9
    WS_HELLO = 10
    WS_HEARTBEAT_ACK = 11


class Client:
    def __init__(self, token, url, dispatcher):
        self.token = token
        self.ws_url = url
        self.ws_conn = None
        self.heartbeat_interval = 30
        self.heartbeat_thread = None
        self.event_seq = None  # 事件序列号，发送消息需要携带，第一次连接传null
        self.ws_app = None
        self.dispatcher = dispatcher

    def connect(self):
        """
        websocket向服务器端发起链接，并定时发送心跳
        """
        if self.ws_url == "":
            raise Exception("url is none")

        def on_close(ws, close_status_code, close_msg):
            logger.info(
                "[ws连接]关闭, 返回码: %s" % close_status_code + ", 返回信息:%s" % close_msg
            )
            # 关闭心跳包线程
            self.ws_conn = None

        def on_message(ws, message):
            logger.debug("on_message: %s" % message)
            message_event = json.loads(message)
            if self._is_system_event(message_event, ws):
                return
            if "t" in message_event.keys():
                event_seq = message_event["s"]
                if event_seq > 0:
                    self.event_seq = event_seq

                if message_event["t"] == "READY": #鉴权事件
                    logger.info("[ws连接]鉴权成功")
                    self._ready_handler(message_event)
                    logger.info("[ws连接]程序启动成功！")
                    return

                self.dispatcher(message_event['d'])  # dispatch message

                
        def on_error(ws, exception=Exception):
            traceback.print_exc()

        def on_open(ws):
            logger.debug("on_open: %s" % ws)

        ws_app = websocket.WebSocketApp(
            self.ws_url,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close,
            on_open=on_open,
        )
        self.ws_app = ws_app

        self.heartbeat_thread = threading.Thread(
            target=self._send_heartbeat, args=(self.heartbeat_interval, threading.Event())
        )
        self.heartbeat_thread.daemon = True
        self.heartbeat_thread.start()

        ws_app.run_forever()

    def identify(self):
        """
        websocket鉴权
        """
        logger.info("[ws连接]鉴权中...")
        identify_event = {
            "op": OpCode.WS_IDENTITY.value,
            "d": {
                "token": self.token,
                "intents": INTENT_PUBLIC_GUILD_MESSAGES,
                "shard": []
            }
        }
        self.send_msg(identify_event)

    def reconnect(self):
        ...

    def send_msg(self, event_json):
        """
        websocket发送消息
        :param event_json:
        """
        send_msg = json.dumps(event_json)
        logger.debug("send_msg: %s" % send_msg)
        self.ws_conn.send(data=send_msg)

    def disconnect(self):
        self.ws_app.close()
        self.ws_conn = None

    def _ready_handler(self, message_event):
        data = message_event["d"]
        self.version = data["version"]
        self.session_id = data["session_id"]
        self.shard_id = data["shard"][0]
        self.shard_count = data["shard"][1]
        self.user = data["user"]

    def _is_system_event(self, message_event, ws):
        """
        系统事件
        :param message_event:消息
        :param ws:websocket
        :return:
        """
        event_op = message_event["op"]
        if event_op == OpCode.WS_HELLO.value:
            logger.info("[ws连接]连接成功，开始鉴权")
            self.ws_conn = ws
            # 连接成功，设置心跳周期，然后鉴权
            self.heartbeat_interval = message_event["d"]["heartbeat_interval"] * 1000  # 单位设置为秒
            self.identify()
            return True
        if event_op == OpCode.WS_HEARTBEAT.value:
            return True
        if event_op == OpCode.WS_RECONNECT.value:
            self.reconnect()
            return True
        return False

    def _send_heartbeat(self, interval, thread_event):
        """
        心跳包
        :param interval: 间隔时间
        :param thread_event: 线程
        """
        while not thread_event.wait(interval):
            heartbeat_event = {
                "op": OpCode.WS_HEARTBEAT.value,
                "d": self.event_seq
            }
            if self.ws_conn is None:
                self.heartbeat_thread.stopped = True
            else:
                self.send_msg(heartbeat_event)

