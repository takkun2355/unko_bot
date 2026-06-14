import discord
from discord.ext import commands
import random

# IQが下がる名言サンプル
QUOTES = [
    "人生は一度きり。寝ろ。",
    "明日やろうは馬鹿やろう。",
    "考えるな、感じろ。",
    "そのうち天才になれるさ。",
    "努力は裏切らない…かも。",
    "君の未来は猫次第。",
    "それは相当やばいね、どうにか思い出せない？ アンタの名前は...\n私はunkoman!!。",
    "知らぬが仏。忘れろ。",
]


class IQDownQuotes(commands.Cog):
    """IQが下がる名言Bot"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="iqquote")
    async def iqquote(self, ctx):
        """ランダムでIQが下がる名言を表示"""
        quote = random.choice(QUOTES)
        await ctx.send(f"🧠💤 IQが下がる名言: {quote}")


# CogをBotに登録
async def setup(bot):
    await bot.add_cog(IQDownQuotes(bot))
