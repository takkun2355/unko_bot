import asyncio
import discord
from discord.ext import commands


class SpamCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        name="spam",
        help="指定したユーザーに指定した回数メンションを送信します。(管理者権限が必要です)",
    )
    @commands.has_permissions(administrator=False)
    async def spam(
        self,
        ctx: commands.Context,
        member: discord.Member,
        count: int = 10,
        delay: float = 1.0,
    ):
        """
        指定したユーザーに繰り返しメンションを送信します。

        使用法: ^^spam @ユーザー名 [回数] [遅延(秒)]
        例: ^^spam @User 20 0.5

        パラメータ:
        - member: メンションするユーザー (必須)
        - count: メンションを繰り返す回数 (デフォルト: 10, 最大: 100)
        - delay: 各メッセージ間の遅延（秒） (デフォルト: 1.0, 最小: 0.5)
        """
        if not isinstance(member, discord.Member):
            await ctx.send("有効なユーザーを指定してください。")
            return

        # パラメータのバリデーション
        # count = max(1, min(count, 100))  # 1回から100回まで
        # delay = max(0.5, delay)  # 最低0.5秒の遅延

        await ctx.send(f"{member.mention} へのメンションを {count} 回開始します。")

        for i in range(count):
            try:
                await ctx.send(f"({i + 1}/{count}) {member.mention}")
                await asyncio.sleep(delay)
            except discord.errors.HTTPException as e:
                await ctx.send(f"エラーが発生しました: {e}")
                break

        await ctx.send("メンションが完了しました。")

    @spam.error
    async def spam_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("使用法: `^^spam @ユーザー名 [回数] [遅延]`")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("指定されたユーザーが見つかりません。")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("このコマンドを使用するには管理者権限が必要です。")
        else:
            await ctx.send(f"予期せぬエラーが発生しました: {error}")

    @commands.command(
        name="flood",
        help="指定ユーザーのメンションを1メッセージに詰め込みます。(管理者権限が必要です)",
    )
    @commands.has_permissions(administrator=False)
    async def flood(self, ctx: commands.Context, member: discord.Member, total: int = 1000000000):
        """指定したユーザーのメンションを、1つのメッセージに文字数制限いっぱいまで詰め込みます。"""
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

    @flood.error
    async def flood_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("使用法: `^^flood @ユーザー名 [表示用の合計数]`")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("指定されたユーザーが見つかりません。")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("このコマンドを使用するには管理者権限が必要です。")
        else:
            await ctx.send(f"予期せぬエラーが発生しました: {error}")

    @commands.command(
        name="countup",
        help="指定回数、指定時間ごとに数字をカウントアップして送信します。(管理者権限が必要です)",
    )
    @commands.has_permissions(administrator=False)
    async def countup(self, ctx: commands.Context, count: int, delay: float = 1.0):
        """指定回数、指定時間ごとに数字をカウントアップして送信します。"""
        if count <= 0:
            await ctx.send("回数は1以上の整数で指定してください。")
            return

        delay = max(0.5, delay)  # 安全のため最低遅延を設ける

        for i in range(1, count + 1):
            try:
                await ctx.send(str(i))
                await asyncio.sleep(delay)
            except discord.errors.HTTPException as e:
                await ctx.send(f"エラーが発生しました: {e}")
                break

    @countup.error
    async def countup_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("使用法: `^^countup <回数> [遅延(秒)]`")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("回数には有効な整数を指定してください。")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("このコマンドを使用するには管理者権限が必要です。")
        else:
            await ctx.send(f"予期せぬエラーが発生しました: {error}")


async def setup(bot):
    await bot.add_cog(SpamCog(bot))
