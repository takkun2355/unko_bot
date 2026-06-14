import logging

logger = logging.getLogger(__name__)
import discord
from discord.ext import commands


class EventCog(commands.Cog):
    """Bot起動時イベント"""

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        logger.info(f"{self.bot.user} でログイン完了！")
        channel = self.bot.get_channel(1416694818339291147)
        if channel and isinstance(channel, discord.TextChannel):
            await channel.send("Botを起動しました！")


async def setup(bot):
    await bot.add_cog(EventCog(bot))
