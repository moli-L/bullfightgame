# -*- coding: utf-8 -*-

from typing import List


class User:
    def __init__(self, data=None):
        self.id: str = ""
        self.username: str = ""
        self.avatar: str = ""
        self.bot: bool = False
        self.union_openid: str = ""
        self.union_user_account: str = ""
        if data is not None:
            self.__dict__ = data


class Member:
    def __init__(self, data=None):
        self.user: User = User()
        self.nick: str = ""
        self.roles = [""]
        self.joined_at: str = ""
        if data is not None:
            self.__dict__ = data


class MessageEmbed:
    def __init__(
        self,
        title: str = "",
        prompt: str = "",
        thumbnail = None,
        fields = None,
        data=None,
    ):
        # 标题
        self.title = title
        # 消息弹窗内容
        self.prompt = prompt
        # 缩略图
        self.thumbnail = thumbnail
        # 消息创建时间
        self.fields = fields
        if data:
            self.__dict__ = data


class Message:
    def __init__(self, data=None):
        self.id: str = ""
        self.channel_id: str = ""
        self.guild_id: str = ""
        self.content: str = ""
        self.timestamp: str = ""
        self.edited_timestamp: str = ""
        self.mention_everyone: str = ""
        self.author: User = User()
        self.attachments = []
        self.embeds: List[MessageEmbed] = [MessageEmbed()]
        self.mentions: List[User] = [User()]
        self.member: Member = Member()
        self.ark = None
        self.seq: int = 0
        self.seq_in_channel = ""
        self.message_reference = None
        self.src_guild_id = ""
        if data:
            self.__dict__ = data


class MessageSendResponse:
    def __init__(
        self,
        content: str = "",
        msg_id: str = None,
        embed: MessageEmbed = None,
        ark = None,
        image: str = "",
        message_reference = None,
        markdown = None,
    ):
        """
        机器人发送消息时所传的数据对象

        :param content: 消息内容，文本内容，支持内嵌格式
        :param msg_id: 要回复的消息id(Message.id), 在 AT_CREATE_MESSAGE 事件中获取。带了 msg_id 视为被动回复消息，否则视为主动推送消息
        :param embed: embed 消息，一种特殊的 ark
        :param ark: ark 消息
        :param image: 图片url地址
        :param message_reference: 引用消息
        """

        self.content = content
        self.embed = embed
        self.ark = ark
        self.image = image
        self.msg_id = msg_id
        self.message_reference = message_reference
        self.markdown = markdown

