from discord.ext import commands
import asyncio
import random


# ReactionGameCog.py
class ReactionGameCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Cog の初期化

    @commands.command(name="reactiongame")
    async def reaction_game(self, ctx):
        """リアクションタイミング勝負を開始する"""
        emojis = ["⚡", "🔥", "💥", "🎯", "⭐"]
        chosen_emoji = random.choice(emojis)
        await ctx.send(
            f"⚠️ 準備完了！リアクション `{chosen_emoji}` が出たらすぐにリアクションを押してください！\n3秒後に開始…"
        )

        # 少し待つ（準備時間）
        await asyncio.sleep(3)
        msg = await ctx.send(f"💡 さあ！リアクションして！ `{chosen_emoji}`")

        # リアクション追加
        await msg.add_reaction(chosen_emoji)

        def check(reaction, user):
            return user != self.bot.user and str(reaction.emoji) == chosen_emoji and reaction.message.id == msg.id

        try:
            # 最初にリアクションしたユーザーを待つ
            reaction, user = await self.bot.wait_for("reaction_add", timeout=2.5, check=check)
            await ctx.send(f"🏆 {user.mention} が一番乗り！おめでとう！")
        except asyncio.TimeoutError:
            await ctx.send("⏰ 誰もリアクションできませんでした。もう一度挑戦してね！")


# Cog登録用
async def setup(bot):
    await bot.add_cog(ReactionGameCog(bot))
