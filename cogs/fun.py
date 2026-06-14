import random
import discord
from discord.ext import commands


class Fun(commands.Cog):
    """チーム分け・ランダム名前など遊び系"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="team")
    async def team(self, ctx, team_size: int, *members: discord.Member):
        """
        チーム分け
        例: ^^team 2 @A @B @C @D
        """
        if not members:
            await ctx.send("❌ メンバーを指定してください！")
            return

        random.shuffle(members)
        teams = [members[i : i + team_size] for i in range(0, len(members), team_size)]

        result = ""
        for i, t in enumerate(teams, start=1):
            names = ", ".join(m.mention for m in t)
            result += f"**チーム {i}:** {names}\n"

        embed = discord.Embed(title="⚔ チーム分け結果", description=result, color=discord.Color.orange())
        await ctx.send(embed=embed)

    @commands.command(name="randname")
    async def randname(self, ctx):
        """ランダム名前ジェネレーター"""
        prefixes = [
            "スーパー",
            "激辛",
            "最強",
            "謎の",
            "爆裂",
            "臭い",
            "最恐",
            "伝説",
            "ド変態",
            "go to hell",
        ]
        bases = [
            "犬",
            "ネコ",
            "ドラゴン",
            "忍者",
            "unkoman",
            "aga",
            "akikueko",
            "らむ",
            "永藤 英機",
            "MilkT",
        ]
        suffixes = [
            "マスター",
            "キング",
            "丸",
            "先輩",
            "ちゃん",
            "ロール",
            "きゃん",
            "ちょんちょんﾊﾟｰ",
            "くん",
            "しね！！",
            "育♡",
        ]

        name = random.choice(prefixes) + random.choice(bases) + random.choice(suffixes)

        embed = discord.Embed(
            title="🎲 ランダム名前ジェネレーター",
            description=f"生成された名前: **{name}**",
            color=discord.Color.purple(),
        )
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Fun(bot))
