# -*- coding: utf-8 -*-

from threading import Timer
from .bullgame import BullGame, Player


MIN_NUM_PLAYERS = 2
MAX_NUM_PLAYERS = 5

class GameManager:
    """游戏管理器，负责游戏全流程管理"""

    def __init__(self):
        self.game_room = {} #一个频道最多同时对应一个游戏房间

    def start_game(self, channel_id, num_player=MIN_NUM_PLAYERS):
        if num_player < MIN_NUM_PLAYERS or num_player > MAX_NUM_PLAYERS:
            return False, f"房间创建失败，游戏人数应为 {MIN_NUM_PLAYERS}-{MAX_NUM_PLAYERS} 人"
        elif self.has_room(channel_id):
            return False, "游戏正在进行中..."
        else:
            self.game_room[channel_id] = BullGame(channel_id, num_player)
            return True, f"开始牛牛游戏，已创建{num_player}人房间，剩余{num_player-1}个席位，赶快加入吧！"
    
    def has_room(self, channel_id):
        return channel_id in self.game_room

    def get_room(self, channel_id) -> BullGame:
        return self.game_room.get(channel_id)
    
    def find_player(self, channel_id, user_id) -> Player:
        return self.get_room(channel_id).find_player_by_id(user_id)
    
    def is_player_banker(self, channel_id, player: Player):
        return player.user_id == self.get_room(channel_id).get_banker().user_id
        
    def get_all_players_name(self, channel_id):
        return [p.user_name for p in self.get_room(channel_id).players]

    def stop_game(self, channel_id):
        del self.game_room[channel_id]

    def async_event_on_timeout(self, secs, callback, ctx, *args, **kw):
        timer = Timer(secs, callback, (ctx, *args), kw)
        timer.start()
        return timer