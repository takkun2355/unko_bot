import logging

logger = logging.getLogger(__name__)
import random

from discord.ext import commands

# 呪文のパーツ
PREFIXES = ["アブラカダ", "エクス", "インフェルノ", "ルミナス", "シャドウ", "アルケミ"]
SUFFIXES = ["リウス", "トロン", "フィカス", "マンドラ", "サリオン", "ボルテクス"]
ELEMENTS = ["🔥", "❄", "⚡", "🌪", "💧", "🌟"]


class MagicSpellBot(commands.Cog):
    """魔法詠唱Bot（発言で呪文生成）"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="cast")
    async def cast_spell(self, ctx, *, phrase: str):
        """ユーザーのフレーズを元に呪文を生成
        例: /cast 火をください
        """
        prefix = random.choice(PREFIXES)
        suffix = random.choice(SUFFIXES)
        element = random.choice(ELEMENTS)
        spell = f"{prefix}{suffix} {element}！"
        await ctx.send(f"💬 {ctx.author.name} が唱えた: 「{phrase}」\n 呪文生成: {spell}")


# CogをBotに登録
async def setup(bot):
    await bot.add_cog(MagicSpellBot(bot))
