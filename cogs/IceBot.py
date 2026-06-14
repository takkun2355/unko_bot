from discord.ext import commands
import random

# 氷化演出用絵文字
ICE_EMOJIS = ["❄️", "🧊", "🌨️"]


class IceBot(commands.Cog):
    """氷Bot（発言を凍らせる演出）"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="freeze")
    async def freeze_message(self, ctx, *, message: str):
        """
        ユーザーの発言を“凍らせた”形で返す
        例: /freeze Hello world
        """
        ice = random.choice(ICE_EMOJIS)
        frozen = " ".join([char + ice for char in message])
        await ctx.send(f"🧊 {ctx.author.name} の発言が凍結！\n{frozen}")


# CogをBotに登録
async def setup(bot):
    await bot.add_cog(IceBot(bot))
