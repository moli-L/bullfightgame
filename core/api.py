# -*- coding: utf-8 -*-

import json

from core.http import Http
from core.url import get_url, APIConstant
from core.model import MessageSendResponse, Message, User


class BaseAPI:
    def __init__(self, token, timeout: int = 5):
        """
        API初始化信息

        :param token: "appid.token"
        :param timeout: 设置超时时间
        """
        self.token = token
        self.http = Http(token, timeout)


class WebsocketAPI(BaseAPI):
    """WebsocketAPI: 获取通用 WSS 接入点"""
    '''
        { "url": "wss://api.sgroup.qq.com/websocket/" }
    '''
    def ws(self):
        url = get_url(APIConstant.gatewayURI)
        response = self.http.get(url)
        websocket_ap = json.loads(response.content)
        return websocket_ap


class WebsocketBotAPI(BaseAPI):
    """WebsocketBotAPI: 获取带分片 WSS 接入点"""
    '''
        {
            "url": "wss://api.sgroup.qq.com/websocket/",
            "shards": 9,
            "session_start_limit": {
                "total": 1000,
                "remaining": 999,
                "reset_after": 14400000,
                "max_concurrency": 1
            }
        }
    '''
    def ws(self):
        url = get_url(APIConstant.gatewayBotURI)
        response = self.http.get(url)
        websocket_ap = json.loads(response.content)
        return websocket_ap


class MessageAPI(BaseAPI):
    """消息"""

    def post_message(self, channel_id: str, message_send: MessageSendResponse) -> Message:
        """
        发送消息

        要求操作人在该子频道具有发送消息的权限。
        发送成功之后，会触发一个创建消息的事件。
        被动回复消息有效期为 5 分钟
        主动推送消息每日每个子频道限 2 条
        发送消息接口要求机器人接口需要链接到websocket gateway 上保持在线状态

        :param channel_id: 子频道ID
        :param message_send: MessageSendRequest对象
        :return: Message对象
        """

        url = get_url(APIConstant.messagesURI).format(channel_id=channel_id)
        request_json = {}
        request_json.update(message_send.__dict__)
        response = self.http.post(url, request_json)
        return json.loads(response.content, object_hook=Message)


class UserAPI(BaseAPI):
    """用户相关接口"""

    def me(self) -> User:
        """
        :return:使用当前用户信息填充的 User 对象
        """
        url = get_url(APIConstant.userMeURI)
        response = self.http.get(url)
        return json.loads(response.content, object_hook=User)

