from discord.ext import commands

# ====== 設定 =======
guild_id = 1312457053708484609
# ===================

class test(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="newname")
    async def newname(self, ctx, name: str = None, userid: int = 1118799600816492626):
        guild = self.bot.get_guild(guild_id)
        member = guild.get_member(userid)
        
        if name is None:
            await member.edit(nick=None)
        else:
            await member.edit(nick=name)
            await ctx.send(f" <@{userid}> のニックネームを「{name}」に変更しました。")

async def setup(bot):
    await bot.add_cog(test(bot))
