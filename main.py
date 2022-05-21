# -*- coding: utf-8 -*-

import time
from core.bot import Bot, MessageContext
from core.model import MessageSendResponse, MessageEmbed
from game import GameManager, BullGame, GameStatus, Player

from config import appid, token
from core.utils import get_logger

logger = get_logger()

bot = Bot()
gm = GameManager()


WAITING_JOIN_TIMEOUT = 60  #sec
WAITING_BET_TIMEOUT = 60


def _invalid_command(ctx: MessageContext):
    if not gm.has_room(ctx.channel_id):
        ctx.reply(f"游戏还未开始噢~")
        return True


@bot.command("游戏介绍")
def introduce_handler(ctx: MessageContext):
    ctx.reply(f"这里有一大段游戏说明，但是因为违法原因不便展示。")

@bot.command("游戏指令")
def show_command_handler(ctx: MessageContext):
    resp = f", ".join([bot.command_prefix+c for c in bot.handle_func.keys()])
    logger.info("游戏指令："+resp)
    ctx.reply(resp)

@bot.command("游戏规则")
def show_command_handler(ctx: MessageContext):
    ctx.reply("受敏感词汇限制，请查看文档")


def _handle_waiting_join_timeout(ctx: MessageContext):
    # 等待玩家加入时间截止，人数不够结束游戏
    # 先检查人数
    room = gm.get_room(ctx.channel_id)
    if room is not None and room.status == GameStatus.WAITING_JOIN.value:
        ctx.reply("等待玩家加入时间截止，玩家人数不足，游戏自动结束~")
        if gm.has_room(ctx.channel_id):
            gm.stop_game(ctx.channel_id)


@bot.command("开始游戏")
def start_handler(ctx: MessageContext, num_player=2):
    success, resp = gm.start_game(ctx.channel_id, num_player)
    if success:
        room = gm.get_room(ctx.channel_id)
        room.add_player(Player(ctx.author.id, ctx.author.username, ctx.author.avatar))
        # 超时2min自动关闭房间
        gm.async_event_on_timeout(WAITING_JOIN_TIMEOUT, _handle_waiting_join_timeout, ctx)

    ctx.reply(resp)


def _check_game_end(ctx: MessageContext, room: BullGame):
    if not room.is_game_end():
        time.sleep(10)
        ctx.reply(room.get_round_announcement())
    else:
        # 结果统计 -> embed 卡片方式展示
        for p in room.players:
            profit = p.points - p.default_points
            fields = [{"name": f"最终积分: {p.points}"}, {"name": f"最终收益: {profit}"}, {"name": "🥳干得不错！" if profit>0 else "😁再接再厉!" if profit<0 else "😏压分大佬？"}]
            thumbnail = {"url": p.avater}
            embed = MessageEmbed(p.user_name, "玩家结算", thumbnail=thumbnail, fields=fields)
            send = MessageSendResponse(embed=embed)
            ctx.reply_send(send)
        stop_handler(ctx)


def _handle_waiting_bet_timeout(ctx: MessageContext, round):
    # 下注时间截止，未下注玩家使用默认下注: 1
    # 先检查是否仍处于下注阶段以及当前回合
    room = gm.get_room(ctx.channel_id)
    if room is not None and room.status == GameStatus.WAITING_BET.value and round == room.current_round():
        ctx.reply("投入积分计时时间到，未投入玩家默认投入1积分，开始游戏...\n回合结算中...")
        report = room.loop_round()
        ctx.reply(report)
        _check_game_end(ctx, room)


@bot.command("加入游戏")
def join_handler(ctx: MessageContext):
    if _invalid_command(ctx): return

    room = gm.get_room(ctx.channel_id)
    if room.status != GameStatus.WAITING_JOIN.value:
        ctx.reply(f"游戏中途不能加入噢~")
        return

    if room.add_player(Player(ctx.author.id, ctx.author.username, ctx.author.avatar)):
        remain = room.get_remain_seats()
        ctx.reply(f"玩家[{ctx.author.username}]加入游戏，当前剩余席位: {remain}")
        if remain == 0:
            ctx.reply(f"玩家集结完毕，初始积分为100，游戏正式开始！\n"+room.get_round_announcement())
            # 开启1min计时器: message 过期时间5min，因此可以复用
            gm.async_event_on_timeout(WAITING_BET_TIMEOUT, _handle_waiting_bet_timeout, ctx, room.current_round())
    else:
        ctx.reply("加入失败，房间满啦或者你已经在房间里啦！")


@bot.command("bet")
def bet_handler(ctx: MessageContext, chips=None):
    if _invalid_command(ctx): return
    
    if chips == None:
        ctx.reply("投入失败，请设置积分")
        return

    p = gm.find_player(ctx.channel_id, ctx.author.id)
    if p is not None and not gm.is_player_banker(ctx.channel_id, p):
        resp = p.bet_chips(chips)
        ctx.reply(resp or f"[{ctx.author.username}] 成功投入 {chips} 积分")
        room = gm.get_room(ctx.channel_id)
        if room.is_all_bet():
            ctx.reply("全部玩家投入完成，开始游戏...\n回合结算中...")
            report = room.loop_round()
            ctx.reply(report)
            _check_game_end(ctx, room)


@bot.command("查看积分")
def view_points_handler(ctx: MessageContext):
    if _invalid_command(ctx): return

    p = gm.find_player(ctx.channel_id, ctx.author.id)
    if p:
        ctx.reply(f"[{ctx.author.username}]当前积分为 {p.points}")
    else:
        ctx.reply(f"[{ctx.author.username}]未在游戏中~")


@bot.command("玩家列表")
def view_players_handler(ctx: MessageContext):
    if _invalid_command(ctx): return
    p_names = gm.get_all_players_name(ctx.channel_id)
    ctx.reply('\n'.join(p_names))


@bot.command("结束游戏")
def stop_handler(ctx: MessageContext):
    if gm.has_room(ctx.channel_id):
        gm.stop_game(ctx.channel_id)
        ctx.reply(f"游戏结束~")


if __name__ == "__main__":
    bot.run(f"{appid}.{token}")

