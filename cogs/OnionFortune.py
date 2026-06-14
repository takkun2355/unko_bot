import logging

logger = logging.getLogger(__name__)
import random

from discord.ext import commands


class OnionFortune(commands.Cog):
    """玉ねぎ占いCog"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="onion")
    async def onion_fortune(self, ctx):
        """今日の皮むき度をランダムで表示
        """
        fortunes = [
            "🧅 今日の皮むき度: 0%…安全日です",
            "🧅 今日の皮むき度: 10%…ほんの少し皮がむけそう",
            "🧅 今日の皮むき度: 25%…軽くむけるかも",
            "🧅 今日の皮むき度: 50%…中くらいの皮むき日",
            "🧅 今日の皮むき度: 75%…結構むけそう！",
            "🧅 今日の皮むき度: 90%…むけまくり注意！",
            "🧅 今日の皮むき度: 100%…フルでむける！玉ねぎ注意",
        ]
        fortune = random.choice(fortunes)
        await ctx.send(fortune)


# CogをBotに登録
async def setup(bot):
    await bot.add_cog(OnionFortune(bot))
