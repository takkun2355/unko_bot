import discord
from discord.ext import commands
import random
from datetime import date

class HentaiRank(commands.Cog):
    """サーバー民ランキング「今日の変態度」Cog"""

    def __init__(self, bot):
        self.bot = bot
        self.daily_ranks = {}  # {date: {user_id: score}}

    @commands.command(name="hentai_rank")
    async def hentai_rank(self, ctx):
        """
        今日のサーバー民ランキング「変態度」をランダムで生成
        """
        today_str = str(date.today())
        members = [m for m in ctx.guild.members if not m.bot]

        # 今日のランクがまだ生成されていなければ生成
        if today_str not in self.daily_ranks:
            self.daily_ranks[today_str] = {}
            for member in members:
                # 0～100のランダムスコア
                self.daily_ranks[today_str][member.id] = random.randint(0, 100)

        # スコア順にソート
        sorted_members = sorted(
            self.daily_ranks[today_str].items(),
            key=lambda x: x[1],
            reverse=True
        )

        # 上位5名表示
        description = ""
        for rank, (user_id, score) in enumerate(sorted_members[:5], start=1):
            member = ctx.guild.get_member(user_id)
            if member:
                description += f"{rank}. {member.name} → 変態度: {score}%\n"

        await ctx.send(f"🌟 **今日の変態度ランキング** 🌟\n{description}")

# CogをBotに登録
async def setup(bot):
    await bot.add_cog(HentaiRank(bot))
