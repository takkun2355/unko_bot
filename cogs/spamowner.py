import asyncio
import discord
from discord.ext import commands


class SpamOwnerCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        name="spam1",
        help="指定したユーザーに指定した回数メンションを送信します。(ボットオーナー専用)",
    )
    @commands.is_owner()
    async def spam1(
        self,
        ctx: commands.Context,
        member: discord.Member,
        count: int = 10,
        delay: float = 1.0,
    ):
        if not isinstance(member, discord.Member):
            await ctx.send("有効なユーザーを指定してください。")
            return

        await ctx.send(f"{member.mention} へのメンションを {count} 回開始します。")

        for i in range(count):
            try:
                await ctx.send(f"({i + 1}/{count}) {member.mention}")
                await asyncio.sleep(delay)
            except discord.errors.HTTPException as e:
                await ctx.send(f"エラーが発生しました: {e}")
                break

        await ctx.send("メンションが完了しました。")

    @spam1.error
    async def spam_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("使用法: `^^spam @ユーザー名 [回数] [遅延]`")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("指定されたユーザーが見つかりません。")
        elif isinstance(error, commands.NotOwner):
            await ctx.send("このコマンドはボットオーナー専用です。")
        else:
            await ctx.send(f"予期せぬエラーが発生しました: {error}")

    @commands.command(
        name="flood1",
        help="指定ユーザーのメンションを1メッセージに詰め込みます。(ボットオーナー専用)",
    )
    @commands.is_owner()
    async def flood1(self, ctx: commands.Context, member: discord.Member, total: int = 1000000000):
        message_content = ""
        i = 1
        limit = 2000

        while True:
            line = f"({i}/{total}) {member.mention}\n"
            if len(message_content) + len(line) > limit:
                break
            message_content += line
            i += 1

        if not message_content:
            await ctx.send("メッセージを生成できませんでした。")
            return

        try:
            await ctx.send(message_content)
        except discord.errors.HTTPException as e:
            await ctx.send(f"メッセージの送信に失敗しました: {e}")

    @flood1.error
    async def flood_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("使用法: `^^flood @ユーザー名 [表示用の合計数]`")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("指定されたユーザーが見つかりません。")
        elif isinstance(error, commands.NotOwner):
            await ctx.send("このコマンドはボットオーナー専用です。")
        else:
            await ctx.send(f"予期せぬエラーが発生しました: {error}")

    @commands.command(
        name="countup1",
        help="指定回数、指定時間ごとに数字をカウントアップして送信します。(ボットオーナー専用)",
    )
    @commands.is_owner()
    async def countup1(self, ctx: commands.Context, count: int, delay: float = 1.0):
        if count <= 0:
            await ctx.send("回数は1以上の整数で指定してください。")
            return

        delay = max(0.5, delay)

        for i in range(1, count + 1):
            try:
                await ctx.send(str(i))
                await asyncio.sleep(delay)
            except discord.errors.HTTPException as e:
                await ctx.send(f"エラーが発生しました: {e}")
                break

    @countup1.error
    async def countup_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("使用法: `^^countup <回数> [遅延(秒)]`")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("回数には有効な整数を指定してください。")
        elif isinstance(error, commands.NotOwner):
            await ctx.send("このコマンドはボットオーナー専用です。")
        else:
            await ctx.send(f"予期せぬエラーが発生しました: {error}")


async def setup(bot):
    await bot.add_cog(SpamOwnerCog(bot))
