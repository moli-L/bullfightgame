# -*- coding: utf-8 -*-

import time
from core.bot import Bot, MessageContext
from game_manager import GameManager
from bullgame import GameStatus, Player

from config import appid, token
from core.utils import get_logger

logger = get_logger()

bot = Bot()
gm = GameManager()


def invalid_command(ctx: MessageContext):
    if not gm.has_room(ctx.channel_id):
        ctx.reply(f"游戏还未开始噢~")
        return True


@bot.command("游戏介绍")
def introduce_handler(ctx: MessageContext):
    ctx.reply(f"这里有一大段游戏说明，但是因为违法原因不便展示。")

@bot.command("游戏指令")
def show_command_handler(ctx: MessageContext):
    resp = f", ".join(['/'+c for c in bot.handlers.keys()])
    logger.info("游戏指令：", resp)
    ctx.reply(resp)


@bot.command("开始游戏")
def start_handler(ctx: MessageContext, num_player=2):
    success, resp = gm.start_game(ctx.channel_id, num_player)
    if success:
        room = gm.get_room(ctx.channel_id)
        room.add_player(Player(ctx.author.id, ctx.author.username))

    ctx.reply(resp)


@bot.command("加入游戏")
def join_handler(ctx: MessageContext):
    if invalid_command(ctx): return

    room = gm.get_room(ctx.channel_id)
    if room.status != GameStatus.WAITING_JOIN.value:
        ctx.reply(f"游戏中途不能加入噢~")
        return

    if room.add_player(Player(ctx.author.id, ctx.author.username)):
        remain = room.get_remain_seats()
        ctx.reply(f"玩家[{ctx.author.username}]加入游戏，当前剩余席位: {remain}")
        if remain == 0:
            ctx.reply(f"玩家集结完毕，初始积分为100，游戏正式开始！\n"+room.get_round_announcement())
    else:
        ctx.reply("加入失败，房间满啦或者你已经在房间里啦！")


@bot.command("bet")
def bet_handler(ctx: MessageContext, chips=None):
    if invalid_command(ctx): return
    
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
            if not room.is_game_end():
                time.sleep(10)
                ctx.reply(room.get_round_announcement())
            else:
                stop_handler(ctx)


@bot.command("查看积分")
def view_points_handler(ctx: MessageContext):
    if invalid_command(ctx): return

    p = gm.find_player(ctx.channel_id, ctx.author.id)
    if p:
        ctx.reply(f"[{ctx.author.username}]当前积分为 {p.points}")
    else:
        ctx.reply(f"[{ctx.author.username}]未在游戏中~")


@bot.command("结束游戏")
def stop_handler(ctx: MessageContext):
    if gm.has_room(ctx.channel_id):
        gm.stop_game(ctx.channel_id)
        ctx.reply(f"游戏结束~")


if __name__ == "__main__":
    bot.run(f"{appid}.{token}")
