import random
import discord
from discord.ext import commands

class nameaga(commands.Cog):
    @commands.command(name="aganame")
    async def randname(self, ctx):
        """ランダム名前ジェネレーター"""
        prefixes = ["スーパー", "激辛", "最強口臭", "謎の", "爆裂", "臭い", "最恐", "伝説", "ド変態", "ニ”ニー服来た"]
        bases = ["🤗", "22", "ペブカック", "AGAり的", "full", "スーパー22人", "違法人", "ナナホシ", "有名人（笑）", "奇声虫"]
        suffixes = ["AGA", "あがり", "242", "あーさん", "smell体", "22", "AGAり", "男性型脱毛症", "にがり", "ナナホシ"]

        aganame = random.choice(prefixes) + random.choice(bases) + random.choice(suffixes)

        embed = discord.Embed(
            title="🎲 ランダム名前ジェネレーター",
            description=f"生成された名前: **{aganame}**",
            color=discord.Color.purple()
        )
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(nameaga(bot))