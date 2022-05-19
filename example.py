from core.bot import Bot, MessageContext
from config import appid, token

bot = Bot()

@bot.command("测试")
def introduce_handler(ctx: MessageContext):
    ctx.reply(f"测试")

if __name__ == "__main__":
    bot.run(f"{appid}.{token}")