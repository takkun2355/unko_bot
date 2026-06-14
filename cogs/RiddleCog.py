import discord
from discord.ext import commands
import random


class RiddleCog(commands.Cog):
    """なぞなぞ / IQテスト Cog"""

    def __init__(self, bot):
        self.bot = bot
        # なぞなぞのリスト（質問:答え）
        self.riddles = [
            {
                "question": "私は何でしょう？朝は4本足、昼は2本足、夜は3本足。",
                "answer": "人間",
            },
            {"question": "頭は青く、体は緑、歩くと赤いものは？", "answer": "信号"},
            {"question": "何を取っても増えるものは？", "answer": "穴"},
            {
                "question": "パンはパンでも食べられないパンとは？",
                "answer": "フライパン",
            },
        ]

    @commands.command(name="riddle")
    async def riddle(self, ctx):
        """ランダムななぞなぞを出題する"""
        riddle = random.choice(self.riddles)
        await ctx.send(f"🧩 なぞなぞ: {riddle['question']}")

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        try:
            msg = await self.bot.wait_for("message", timeout=30.0, check=check)
            if riddle["answer"] in msg.content:
                await ctx.send("🎉 正解です！")
            else:
                await ctx.send(
                    f"❌ 残念、不正解です。答えは `{riddle['answer']}` でした。"
                )
        except:
            await ctx.send(f"⏰ 時間切れ！答えは `{riddle['answer']}` です。")


# Cog登録用
async def setup(bot):
    await bot.add_cog(RiddleCog(bot))
