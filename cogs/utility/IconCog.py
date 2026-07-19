"""Discord.py Cog: /icon, /servericon および ^^icon, ^^servericon の両方を提供します。
使い方:
  - cogs フォルダに置いて bot 側で `bot.load_extension('cogs.icon_cog')` または
    `await bot.load_extension('cogs.icon_cog')` でロードしてください。

ファイル名例: cogs/icon_cog.py
"""

import logging

logger = logging.getLogger(__name__)

import aiohttp
import discord
from discord import app_commands
from discord.ext import commands

# --- 設定 ---
# テスト用ギルドID。グローバルで登録したい場合は None にする。
GUILD_ID: int | None = None


def make_hd_url(asset_url: str, size: int = 1024) -> str:
    """CDNのURLにsizeクエリを付与します（既にクエリがある場合は &size=... にします）。"""
    if "?" in asset_url:
        return f"{asset_url}&size={size}"
    return f"{asset_url}?size={size}"


class IconCog(commands.Cog):
    """アイコン関連のSlash＋テキストコマンドをまとめたCog"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.guild_obj = discord.Object(id=GUILD_ID) if GUILD_ID else None

    # =============================
    #       通常コマンド版
    # =============================
    @commands.command(name="icon", help="指定したユーザーのアイコンを表示します（未指定で実行者）")
    async def icon(self, ctx: commands.Context, member: discord.Member | None = None):
        member = member or ctx.author
        avatar_url = member.display_avatar.url
        avatar_url_hd = make_hd_url(avatar_url, size=1024)

        embed = discord.Embed(
            title=f"{member}",
            description=f"ID: {member.id}",
            color=discord.Color.blurple(),
        )
        embed.set_image(url=avatar_url_hd)
        embed.set_footer(text="サイズ=1024 を指定しています。アニメアイコンはGIFで返ります。")

        await ctx.send(embed=embed)

    @commands.command(name="servericon", help="サーバーのアイコンを表示します（URLまたはID対応）")
    async def servericon(self, ctx: commands.Context, target: str | None = None):
        if not target:
            guild = ctx.guild
            if not guild or not guild.icon:
                await ctx.send("このサーバーにはアイコンが設定されていません。")
                return
            icon_url_hd = make_hd_url(guild.icon.url)
            embed = discord.Embed(title=f"{guild.name} のサーバーアイコン").set_image(url=icon_url_hd)
            await ctx.send(embed=embed)
            return

        # --- サーバーID指定 ---
        if target.isdigit():
            guild = self.bot.get_guild(int(target))
            if guild and guild.icon:
                icon_url_hd = make_hd_url(guild.icon.url)
                embed = discord.Embed(title=f"{guild.name} のサーバーアイコン").set_image(url=icon_url_hd)
                await ctx.send(embed=embed)
            else:
                await ctx.send("サーバー情報を取得できないか、アイコンが設定されていません。")
            return

        # --- 招待リンク指定 ---
        if "discord.gg" in target:
            invite_code = target.split("discord.gg/")[-1].split("/")[0]
            async with aiohttp.ClientSession() as session:
                async with session.get(f"https://discord.com/api/v10/invites/{invite_code}?with_counts=false") as resp:
                    if resp.status != 200:
                        await ctx.send("招待リンクが無効か、情報を取得できません。")
                        return
                    data = await resp.json()
                    guild_data = data.get("guild")
                    if guild_data and guild_data.get("icon"):
                        guild_icon = (
                            f"https://cdn.discordapp.com/icons/{guild_data['id']}/{guild_data['icon']}.png?size=1024"
                        )
                        embed = discord.Embed(title=f"{guild_data['name']} のサーバーアイコン").set_image(
                            url=guild_icon
                        )
                        await ctx.send(embed=embed)
                    else:
                        await ctx.send("このサーバーにはアイコンが設定されていません。")
            return

        await ctx.send("サーバーを特定できませんでした。")

    # =============================
    #       Slashコマンド版
    # =============================
    @app_commands.command(
        name="icon",
        description="指定したユーザーのアイコンを表示します（未指定で実行者）",
    )
    @app_commands.describe(member="アイコンを見たいユーザー（省略可）")
    async def slash_icon(self, interaction: discord.Interaction, member: discord.Member | None = None):
        member = member or interaction.user
        avatar_url_hd = make_hd_url(member.display_avatar.url)
        embed = discord.Embed(
            title=f"{member}",
            description=f"ID: {member.id}",
            color=discord.Color.blurple(),
        )
        embed.set_image(url=avatar_url_hd)
        embed.set_footer(text="サイズ=1024 を指定しています。アニメアイコンはGIFで返ります。")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(
        name="servericon",
        description="サーバーのアイコンを表示します（URLまたはID対応）",
    )
    @app_commands.describe(target="省略で現在のサーバー、または discord.gg/リンク またはサーバーID")
    async def slash_servericon(self, interaction: discord.Interaction, target: str | None = None):
        if not target:
            guild = interaction.guild
            if not guild or not guild.icon:
                await interaction.response.send_message(
                    "このサーバーにはアイコンが設定されていません。", ephemeral=True
                )
                return
            icon_url_hd = make_hd_url(guild.icon.url)
            embed = discord.Embed(title=f"{guild.name} のサーバーアイコン").set_image(url=icon_url_hd)
            await interaction.response.send_message(embed=embed)
            return

        # --- ID指定 ---
        if target.isdigit():
            guild = interaction.client.get_guild(int(target))
            if guild and guild.icon:
                icon_url_hd = make_hd_url(guild.icon.url)
                embed = discord.Embed(title=f"{guild.name} のサーバーアイコン").set_image(url=icon_url_hd)
                await interaction.response.send_message(embed=embed)
            else:
                await interaction.response.send_message(
                    "サーバー情報を取得できないか、アイコンが設定されていません。",
                    ephemeral=True,
                )
            return

        # --- 招待リンク指定 ---
        if "discord.gg" in target:
            invite_code = target.split("discord.gg/")[-1].split("/")[0]
            async with aiohttp.ClientSession() as session:
                async with session.get(f"https://discord.com/api/v10/invites/{invite_code}?with_counts=false") as resp:
                    if resp.status != 200:
                        await interaction.response.send_message(
                            "招待リンクが無効か、情報を取得できません。", ephemeral=True
                        )
                        return
                    data = await resp.json()
                    guild_data = data.get("guild")
                    if guild_data and guild_data.get("icon"):
                        guild_icon = (
                            f"https://cdn.discordapp.com/icons/{guild_data['id']}/{guild_data['icon']}.png?size=1024"
                        )
                        embed = discord.Embed(title=f"{guild_data['name']} のサーバーアイコン").set_image(
                            url=guild_icon
                        )
                        await interaction.response.send_message(embed=embed)
                    else:
                        await interaction.response.send_message(
                            "このサーバーにはアイコンが設定されていません。",
                            ephemeral=True,
                        )
            return

        await interaction.response.send_message("サーバーを特定できませんでした。", ephemeral=True)

    # Cogロード時にslashを同期
    async def cog_load(self):
        try:
            if self.guild_obj:
                await self.bot.tree.sync(guild=self.guild_obj)
                logger.info(f"[IconCog] Synced commands to guild {self.guild_obj.id}")
        except Exception as e:
            logger.info("[IconCog] Command sync failed:", e)


# --- setup for extension loader ---
async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(IconCog(bot))
