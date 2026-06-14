# cogs/agari_logger.py

from pathlib import Path

from discord.ext import commands

CHANNEL_ID = 1118799600816492626
LOG_FILE = "AGARI.log"


class AgariLogger(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        if getattr(self.bot, "_agari_logged", False):
            return

        self.bot._agari_logged = True

        channel = self.bot.get_channel(CHANNEL_ID)

        if channel is None:
            print(f"チャンネル取得失敗: {CHANNEL_ID}")
            return

        print("ログ取得開始")

        log_path = Path(LOG_FILE)

        with log_path.open("w", encoding="utf-8") as f:
            async for msg in channel.history(limit=None, oldest_first=True):
                content = msg.content.replace("\n", "\\n")

                f.write(f"[{msg.created_at}] {msg.author} ({msg.author.id}) : {content}\n")

        print(f"保存完了: {LOG_FILE}")


async def setup(bot):
    await bot.add_cog(AgariLogger(bot))
