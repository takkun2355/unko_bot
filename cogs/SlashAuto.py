# cogs/SlashAuto.py
import discord
from discord.ext import commands
from discord import app_commands
import inspect
from typing import get_type_hints

DISCORD_TYPES = {
    str: str,
    int: int,
    float: float,
    bool: bool,
    discord.Member: discord.Member,
    discord.TextChannel: discord.TextChannel,
    discord.VoiceChannel: discord.VoiceChannel,
    discord.Role: discord.Role,
}


class SlashAuto(commands.Cog):
    """既存のCogコマンドを自動でスラッシュ化するCog"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.bot.loop.create_task(self.register_slash_commands())

    async def register_slash_commands(self):
        await self.bot.wait_until_ready()

        for cog_name, cog in self.bot.cogs.items():
            if cog_name == self.__class__.__name__:
                continue

            for command in cog.get_commands():
                if isinstance(command, app_commands.Command):
                    continue

                sig = inspect.signature(command.callback)
                type_hints = get_type_hints(command.callback)
                params = list(sig.parameters.items())[1:]  # selfを飛ばす

                # クロージャで固定
                def make_slash_callback(command, cog, params):
                    async def slash_cmd(interaction: discord.Interaction, **kwargs):
                        class DummyCtx:
                            def __init__(self, interaction):
                                self.bot = interaction.client
                                self.message = getattr(interaction, "message", None)
                                self.author = interaction.user
                                self.channel = interaction.channel
                                self.guild = interaction.guild

                            async def send(self, *args, **send_kwargs):
                                if not interaction.response.is_done():
                                    return await interaction.response.send_message(
                                        *args, **send_kwargs
                                    )
                                else:
                                    return await interaction.followup.send(
                                        *args, **send_kwargs
                                    )

                        ctx = DummyCtx(interaction)
                        await command.callback(cog, ctx, **kwargs)

                    return slash_cmd

                callback = make_slash_callback(command, cog, params)

                try:
                    self.bot.tree.add_command(
                        app_commands.Command(
                            name=command.name,
                            description=command.help or "No description",
                            callback=callback,
                        )
                    )
                except Exception as e:
                    print(f"[SlashAuto] {command.name} 登録失敗: {e}")


async def setup(bot: commands.Bot):
    await bot.add_cog(SlashAuto(bot))
