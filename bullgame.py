# -*- coding: utf-8 -*-

import random
from enum import Enum
from typing import List


class Player:
    def __init__(self, user_id, user_name, defult_points=100):
        self.user_id = user_id
        self.user_name = user_name
        self.points = defult_points
        self.chips = 1  #下注
        self.bet = False
        self.cards = []

    def get_points(self):
        return self.points
    
    def add_points(self, points):
        self.points += points
    
    def sub_points(self, points):
        # # 积分不足有多少扣多少
        # sub = points if points <= self.points else self.points
        # self.points -= sub
        # return sub

        # 先不考虑积分不足情况，即积分可为负
        self.points -= points
    
    def bet_chips(self, chips):
        if 1 <= chips:
            self.chips = chips
            self.bet = True
        else:
            return f"投入积分应大于1"
    
    def reset_chips(self):
        self.chips = 1
        self.bet = False

    def set_cards(self, cards):
        self.cards = cards

    def get_cards_str(self):
        return ','.join([str(c) for c in self.cards])


card_point = {
    2: 2,
    3: 3,
    4: 4,
    5: 5,
    6: 6,
    7: 7,
    8: 8,
    9: 9,
    10: 10,
    'J': 10,
    'Q': 10,
    'K': 10,
    'A': 1
}

card_value = {
    2: 2,
    3: 3,
    4: 4,
    5: 5,
    6: 6,
    7: 7,
    8: 8,
    9: 9,
    10: 10,
    'J': 11,
    'Q': 12,
    'K': 13,
    'A': 1
}


class BullResult:
    def __init__(self):
        self.level = 0      #等级：默认0=无牛 options: (无牛，牛X，牛牛，大牛牛)
        self.max = 1        #最大牌型, 或牛X的X
        self.times = 1      #计算积分时的倍数


class Poker:
    def __init__(self):
        self.cards = [2,3,4,5,6,7,8,9,10,'J','Q','K','A']*4
        self.shuffle_cards()
    
    def shuffle_cards(self):
        random.shuffle(self.cards)
    
    def deal_cards(self, num_player):
        res = []
        r = num_player * 5
        for i in range(num_player):
            res.append(self.cards[i:r:num_player])
        return res
    
    @classmethod
    def compute_bull(cls, cards) -> BullResult:
        res = BullResult()
        cps = [card_point[c] for c in cards]
        bull = cls.find_triple_bull(cps)
        if bull == False: #无牛
            res.max = cls.max_card_value(cards)
            res.times = 1
        else:
            a_i, b_i = [i for i in range(5) if i not in bull]
            a, b = cps[a_i], cps[b_i]
            if (a + b) % 10 != 0:
                res.level = 1 #牛X
                res.max = (a + b) % 10
                res.times = 2 if res.max >= 7 else 1
            elif sum(cps) == 50:
                res.level = 3 #大牛牛: 所有牌全是10分
                res.times = 4
            else:
                res.level = 2 #牛牛
                res.times = 3
        return res

    @classmethod
    def find_triple_bull(cls, cps):
        for i in range(3):
            for j in range(i+1, 4):
                for k in range(j+1, 5):
                    if (cps[i] + cps[j] + cps[k]) % 10 == 0:
                        return [i, j, k]
        return False

    @classmethod
    def max_card_value(cls, card):
        return max([card_value[c] for c in card])


class GameStatus(Enum):
    """
    WAITING_JOIN = 0    # 等待玩家加入游戏
    WAITING_BET = 1     # 等待玩家下注
    GAMING = 2          # 进行中
    """
    WAITING_JOIN = 0
    WAITING_BET = 1
    GAMING = 2

class BullGame:
    def __init__(self, channel_id, num_player=2):
        self.channel_id = channel_id  # 每个频道同时只能一场游戏
        self.num_player = num_player
        self.players: List[Player] = []
        self.banker = 0  #庄家索引
        self.poker = Poker()
        self.status = GameStatus.WAITING_JOIN.value
    
    def add_player(self, player: Player):
        if len(self.players) >= self.num_player:
            return False

        for p in self.players:
            if p.user_id == player.user_id:
                return False

        self.players.append(player)
        if len(self.players) == self.num_player:
            self.status = GameStatus.WAITING_BET.value
        return True
    
    def get_banker(self) -> Player:
        return self.players[self.banker]

    def loop_round(self):
        self.status = GameStatus.GAMING.value
        cards_list = self.poker.deal_cards(self.num_player)  #发牌
        cards_res = []
        for i, cards in enumerate(cards_list):
            self.players[i].set_cards(cards)
            cards_res.append(Poker.compute_bull(cards))
        settlement = self.compute_settlement(cards_res)
        report = self.generate_report(settlement)
        self.reset_players_chips()
        self.reset_players_cards()
        self.banker += 1
        return report

    def _compare_result(self, res1: BullResult, res2: BullResult):
        # 先比较level，再比较最大牌，全部相同庄家胜
        if res1.level > res2.level:
            return True
        elif res1.level == res2.level and res1.max >= res2.max:
            return True
        else:
            return False

    def compute_settlement(self, cards_res):
        banker: Player = self.get_banker()
        b_res: BullResult = cards_res[self.banker]
        settlement = { banker: 0 }  #本局胜负总积分
        for i in range(self.num_player):
            if i == self.banker:
                continue
            player: Player = self.players[i]
            p_res: BullResult = cards_res[i]
            # 计算胜负关系
            if self._compare_result(b_res, p_res): 
                #庄家胜
                total_points = player.chips * b_res.times
                banker.add_points(total_points)
                player.sub_points(total_points)
                settlement[banker] += total_points
                settlement[player] = -total_points
            else:
                #闲家胜
                total_points = player.chips * p_res.times
                player.add_points(total_points)
                banker.sub_points(total_points)
                settlement[player] = total_points
                settlement[banker] -= total_points
        return settlement

    def generate_report(self, settlement):
        report = f"## 第{self.banker+1}回合结算报告 ##"
        # 庄家
        banker: Player = self.get_banker()
        report += f"\n\n[庄] {banker.user_name}\n卡组: {banker.get_cards_str()}\n总收益: {settlement[banker]}\n积分余额: {banker.get_points()}"
        # 闲家
        for i in range(self.num_player):
            if i == self.banker:
                continue
            player: Player = self.players[i]
            report += f"\n\n[闲] {player.user_name}\n卡组: {player.get_cards_str()}\n总收益: {settlement[player]}\n积分余额: {player.get_points()}"

        return report

    def reset_players_chips(self):
        for player in self.players:
            player.reset_chips()

    def reset_players_cards(self):
        for player in self.players:
            player.set_cards([])

    def get_remain_seats(self):
        return self.num_player - len(self.players)

    def get_round_announcement(self): 
        #每回合要做的第一件事
        banker = self.get_banker()
        self.status = GameStatus.WAITING_BET.value
        return f"第 {self.banker+1} 回合，庄 [{banker.user_name}]，请其他玩家投入（计时1min，可重复投入）"

    def find_player_by_id(self, user_id):
        for p in self.players:
            if user_id == p.user_id:
                return p

    def is_all_bet(self):
        for i, player in enumerate(self.players):
            if i != self.banker and not player.bet:
                return False
        return True

    def is_game_end(self):
        return self.banker == self.num_player

    def current_round(self):
        return self.banker + 1
