import logging

logger = logging.getLogger(__name__)
import discord
from discord.ext import commands


class Server(commands.Cog):
    """サーバーステータス関連"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="serverstatus")
    async def serverstatus(self, ctx):
        """サーバーステータスを表示"""
        guild = ctx.guild
        members = guild.member_count
        bots = len([m for m in guild.members if m.bot])
        humans = members - bots

        embed = discord.Embed(title=f"📊 サーバーステータス: {guild.name}", color=discord.Color.green())
        embed.add_field(name="👥 メンバー", value=humans)
        embed.add_field(name="🤖 BOT", value=bots)
        embed.add_field(name="合計", value=members, inline=False)
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Server(bot))
