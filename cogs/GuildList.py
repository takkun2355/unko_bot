import discord
from discord.ext import commands


class GuildList(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="guilds")
    async def send_guild_list(self, ctx):
        # DMで送る。失敗したら人間の設定ミス
        try:
            lines = []
            for guild in self.bot.guilds:
                lines.append(f"サーバー名: {guild.name} | サーバーID: {guild.id}")

            if not lines:
                await ctx.author.send("サーバー情報なし。つまりどこにも居ない。")
                return

            message = "\n".join(lines)
            await ctx.author.send(message)

        except discord.Forbidden:
            await ctx.send("not DM!!\n設定確認しろや。")


class InviteFromGuildID(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="invite_from_id")
    async def invite_from_id(self, ctx, guild_id: int):
        """
        サーバーIDを指定すると、そのサーバーの招待リンクを生成して送信する
        """
        guild = self.bot.get_guild(guild_id)

        if guild is None:
            await ctx.send("そのIDのサーバーには入ってない。つまり無理。")
            return

        # 招待を作れるチャンネルを探す
        channel = None
        for ch in guild.text_channels:
            perms = ch.permissions_for(guild.me)
            if perms.create_instant_invite:
                channel = ch
                break

        if channel is None:
            await ctx.send("招待を作れるチャンネルが存在しない。権限の敗北。")
            return

        try:
            invite = await channel.create_invite(
                max_age=0,  # 無期限
                max_uses=0,  # 無制限
                unique=True,
                reason=f"Requested by {ctx.author}",
            )
        except discord.Forbidden:
            await ctx.send("権限が足りない。Botの人生は常にこれ。")
            return
        except discord.HTTPException:
            await ctx.send("Discord APIが死んだ。たまにある。")
            return

        await ctx.send(f"サーバー名: **{guild.name}**\n招待リンク:\n{invite.url}")


class InviteFactory(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="invite_clone")
    async def invite_clone(self, ctx, invite_url: str, amount: int = 3):
        # 安全装置。暴走防止。
        if amount < 1 or amount > 10:
            await ctx.send("量産数は1〜10。無限増殖は神の仕事。")
            return

        try:
            invite = await self.bot.fetch_invite(invite_url)
        except discord.NotFound:
            await ctx.send("その招待、存在しない。幻想だった可能性が高い。")
            return
        except discord.Forbidden:
            await ctx.send("招待を見る権限がない。扉の前で立ち尽くすBot。")
            return

        guild = invite.guild
        if guild is None:
            await ctx.send("サーバーが特定できない。闇が深い。")
            return

        # Botが入ってるか確認
        target_guild = self.bot.get_guild(guild.id)
        if target_guild is None:
            await ctx.send("Botはそのサーバーにいない。瞬間移動は未実装。")
            return

        # 招待を作れるチャンネル探し
        channel = next(
            (
                c
                for c in target_guild.text_channels
                if c.permissions_for(target_guild.me).create_instant_invite
            ),
            None,
        )

        if channel is None:
            await ctx.send("招待を作れるチャンネルがない。権限不足。")
            return

        invites = []
        for _ in range(amount):
            inv = await channel.create_invite(
                max_age=0,  # 無期限
                max_uses=0,  # 無制限
                unique=True,
            )
            invites.append(inv.url)

        await ctx.send("量産完了。\n" + "\n".join(invites))


async def setup(bot):
    await bot.add_cog(GuildList(bot))
    await bot.add_cog(InviteFromGuildID(bot))
    await bot.add_cog(InviteFactory(bot))
