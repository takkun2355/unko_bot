import random

import discord
from discord.ext import commands

# 固定結果にするユーザーIDの辞書
FIXED_RESULTS = {
    1118799600816492626: {  # 特定ユーザーのDiscord ID
        "omikuji": "あがり\n今日一日口が臭くなるでしょう",
        "fortune": "-931ランク :face_vomiting: :face_vomiting: :face_vomiting: :thumbsdown: :skull:",
    },
    # 他のユーザーも追加可能
}


class FunGames(commands.Cog):
    """サイコロ、コイン、おみくじ、占いなどの楽しいコマンド"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="dice")
    async def dice(self, ctx, sides: int = 6):
        if sides < 2:
            await ctx.send("❌ サイコロの面数は2以上にしてください！")
            return
        result = random.randint(1, sides)
        embed = discord.Embed(
            title="🎲 サイコロ振り",
            description=f"{ctx.author.mention} さんが {sides} 面のサイコロを振りました！\n結果: **{result}**",
            color=discord.Color.blue(),
        )
        await ctx.send(embed=embed)

    @commands.command(name="coin")
    async def coin(self, ctx):
        result = random.choice(["表", "裏"])
        embed = discord.Embed(
            title="🪙 コイン投げ",
            description=f"{ctx.author.mention} さんがコインを投げました！\n結果: **{result}**",
            color=discord.Color.gold(),
        )
        await ctx.send(embed=embed)

    @commands.command(name="omikuji")
    async def omikuji(self, ctx, member: discord.Member = None):
        """おみくじ（任意のメンション可能）"""
        target = member or ctx.author
        fortunes = [
            "大大大吉",
            "大大吉",
            "大吉",
            "中吉",
            "小吉",
            "末吉",
            "凶",
            "大凶",
            "大大凶",
            "アガり",
        ]

        if target.id in FIXED_RESULTS:
            result = FIXED_RESULTS[target.id]["omikuji"]
        else:
            result = random.choice(fortunes)

        embed = discord.Embed(
            title="🎋 おみくじ",
            description=f"{target.mention} さんのおみくじの結果は…\n**{result}**",
            color=discord.Color.purple(),
        )
        await ctx.send(embed=embed)

    @commands.command(name="fortune")
    async def fortune(self, ctx, member: discord.Member = None):
        """占い（任意のメンション可能）"""
        target = member or ctx.author
        ranks = [
            "SSS+ランク ⭐⭐⭐",
            "SSSランク ⭐⭐⭐",
            "SSS-ランク ⭐⭐⭐",
            "SS+ランク ⭐⭐",
            "SSランク ⭐⭐",
            "SS-ランク ⭐⭐",
            "S+ランク ⭐",
            "Sランク ⭐",
            "S-ランク ⭐",
            "A+ランク⚡⚡⚡",
            "Aランク ⚡⚡⚡",
            "A-ランク⚡⚡⚡",
            "B+ランク ⚡⚡",
            "Bランク ⚡⚡",
            "B-ランク ⚡⚡",
            "C+ランク ⚡",
            "Cランク⚡",
            "C-ランク⚡",
        ]

        if target.id in FIXED_RESULTS:
            result = FIXED_RESULTS[target.id]["fortune"]
        else:
            result = random.choice(ranks)

        embed = discord.Embed(
            title="🔮 今日の運勢",
            description=f"{target.mention} さんの今日の運勢は\n**{result}**",
            color=discord.Color.green(),
        )
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(FunGames(bot))
