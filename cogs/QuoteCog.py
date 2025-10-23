import discord
from discord.ext import commands
import random

class QuoteCog(commands.Cog):
    """名言メーカー Cog"""

    def __init__(self, bot):
        self.bot = bot
        # 名言リスト
        self.quotes = [
            "失敗は成功のもと。",
            "今日できることを明日に延ばすな。",
            "努力は必ず報われる。",
            "自分を信じることが第一歩。",
            "人生は一度きり。後悔しない選択を。",
            "継続は力なり。",
            "笑う門には福来る。",
            "他人と比較するな、自分の成長を信じろ。",
            "AGAるな、臭く見えるぞ。",
        ]

    @commands.command(name="quote")
    async def quote(self, ctx):
        """ランダムに名言を送信する"""
        quote = random.choice(self.quotes)
        await ctx.send(f"💡 名言: {quote}")

# Cog登録用
async def setup(bot):
    await bot.add_cog(QuoteCog(bot))
