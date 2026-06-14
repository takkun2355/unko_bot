import discord
from discord.ext import commands
from typing import List
import os
import traceback


class Reload(commands.Cog):
    """Cog管理Cog"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ------------------------------
    # Utility
    # ------------------------------

    def _get_cog_files(self) -> List[str]:
        """cogsフォルダ内のCog一覧取得"""
        cog_dir = "cogs"

        if not os.path.isdir(cog_dir):
            return []

        return [
            f"{cog_dir}.{f[:-3]}"
            for f in os.listdir(cog_dir)
            if f.endswith(".py") and not f.startswith("_")
        ]

    def _parse_cogs(self, cog_names: str):
        """
        all または
        weather, admin
        を処理
        """

        if cog_names.lower() == "all":
            return "all"

        cogs = []

        for cog in cog_names.split(","):
            cog = cog.strip()

            if not cog:
                continue

            if not cog.startswith("cogs."):
                cog = f"cogs.{cog}"

            cogs.append(cog)

        return cogs

    async def _send_results(self, ctx, results):
        """Discord文字数対策"""
        message = "\n".join(results)

        if len(message) <= 1900:
            await ctx.send(message)
            return

        for i in range(0, len(message), 1900):
            await ctx.send(message[i : i + 1900])

    # ------------------------------
    # Reload
    # ------------------------------

    @commands.command(name="reload", aliases=["re"])
    @commands.is_owner()
    async def reload_cmd(self, ctx, *, cog_names: str):
        """
        ^^reload all
        ^^reload weather
        ^^reload weather, admin
        """

        parsed = self._parse_cogs(cog_names)

        if parsed == "all":
            cogs = self._get_cog_files()
        else:
            cogs = parsed

        results = []

        if parsed == "all":
            print("[RELOAD-LOG] All cogs reloaded.")
        else:
            targets = [cog.replace("cogs.", "") for cog in cogs]

            print(f"[RELOAD-LOG] {', '.join(targets)} cog reload.")

        print("[RELOAD-LOG] --- reload cogs ---")

        for cog in cogs:
            cog_name = cog.replace("cogs.", "")

            try:
                if cog in self.bot.extensions:
                    await self.bot.reload_extension(cog)
                    results.append(f"✅ {cog}")
                    print(f"[RELOAD-LOG] - {cog_name}.py reload Success")

                else:
                    await self.bot.load_extension(cog)
                    results.append(f"📦 {cog} (新規ロード)")
                    print(f"[RELOAD-LOG] - {cog_name}.py load Success")

            except commands.ExtensionNotFound:
                results.append(f"❌ {cog} (見つかりません)")
                print(f"[RELOAD-LOG] - {cog_name}.py reload Failure")

            except Exception as e:
                results.append(f"❌ {cog}\n{e}")
                print(f"[RELOAD-LOG] - {cog_name}.py reload Failure")

        print("[RELOAD-LOG] --------------------")

        await self._send_results(ctx, results)

    # ------------------------------
    # Load
    # ------------------------------

    @commands.command(name="load")
    @commands.is_owner()
    async def load_cmd(self, ctx, *, cog_names: str):
        """
        ^^load all
        ^^load weather
        ^^load weather, admin
        """

        parsed = self._parse_cogs(cog_names)

        if parsed == "all":
            cogs = self._get_cog_files()
        else:
            cogs = parsed

        results = []

        for cog in cogs:
            try:
                await self.bot.load_extension(cog)
                results.append(f"📦 {cog}")

            except commands.ExtensionAlreadyLoaded:
                results.append(f"⚠️ {cog} (既にロード済み)")

            except commands.ExtensionNotFound:
                results.append(f"❌ {cog} (見つかりません)")

            except Exception as e:
                results.append(f"❌ {cog}\n{e}")

        await self._send_results(ctx, results)

    # ------------------------------
    # Unload
    # ------------------------------

    @commands.command(name="unload", aliases=["un"])
    @commands.is_owner()
    async def unload_cmd(self, ctx, *, cog_names: str):
        """
        ^^unload all
        ^^unload weather
        ^^unload weather, admin
        """

        parsed = self._parse_cogs(cog_names)

        if parsed == "all":
            cogs = [
                cog
                for cog in self.bot.extensions.keys()
                if cog.lower() != "cogs.reload"
            ]
        else:
            cogs = parsed

        results = []

        for cog in cogs:
            if cog.lower() == "cogs.reload":
                results.append("⚠️ cogs.reload は保護されています")
                continue

            try:
                await self.bot.unload_extension(cog)
                results.append(f"🗑️ {cog}")

            except commands.ExtensionNotLoaded:
                results.append(f"⚠️ {cog} (未ロード)")

            except Exception as e:
                results.append(f"❌ {cog}\n{e}")

        await self._send_results(ctx, results)

    # ------------------------------
    # List
    # ------------------------------

    @commands.command(name="cogs")
    @commands.is_owner()
    async def list_cogs(self, ctx):
        """Cog一覧"""

        cog_files = set(self._get_cog_files())
        loaded = set(self.bot.extensions.keys())

        loaded_cogs = cog_files & loaded
        unloaded_cogs = cog_files - loaded

        lines = ["📋 Cog一覧"]

        if loaded_cogs:
            lines.append("\n✅ ロード済み")
            lines.extend(f"・{cog}" for cog in sorted(loaded_cogs))

        if unloaded_cogs:
            lines.append("\n⬜ 未ロード")
            lines.extend(f"・{cog}" for cog in sorted(unloaded_cogs))

        await self._send_results(ctx, lines)

    # ------------------------------
    # Error Handler
    # ------------------------------

    @reload_cmd.error
    @load_cmd.error
    @unload_cmd.error
    @list_cogs.error
    async def command_error(self, ctx, error):

        if isinstance(error, commands.NotOwner):
            return

        tb = traceback.format_exc()

        if len(tb) > 1500:
            tb = tb[:1500] + "\n...(省略)"

        await ctx.send(f"❌ エラー発生\n```py\n{tb}\n```")


async def setup(bot):
    await bot.add_cog(Reload(bot))
