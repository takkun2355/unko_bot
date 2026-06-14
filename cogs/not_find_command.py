# cogs/not_find_command.py
from discord.ext import commands

class CommandCheckerCog(commands.Cog):
    """未登録コマンド検知Cog"""

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            await self.not_find_command(ctx)
        else:
            # 他のエラーは通常通り表示
            raise error

    async def not_find_command(self, ctx):
        """
        未登録コマンドが使われたときに呼ばれる処理
        """
        # 入力されたコマンド名を取得（接頭辞 ^^ を除去）
        cmd_name = ctx.message.content.lstrip(ctx.prefix).split()[0]
        await ctx.send(
            f"そんなコマンドロードされてねーよ😅 (`{cmd_name}`)\n"
            f"`^^help` で使えるコマンドを確認してね！\n"
            f"あっ、でも見てもわかんないよね！\n"
            f"残念^^"
        )

# CogをBotに追加する関数
async def setup(bot):
    await bot.add_cog(CommandCheckerCog(bot))
