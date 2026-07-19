import logging

logger = logging.getLogger(__name__)
import json
import pathlib
from datetime import datetime

from discord.ext import commands, tasks

BIRTHDAY_FILE = "birthdays.json"


class BirthdayManager(commands.Cog):
    """サーバー誕生日イベント＋一覧ページCog"""

    def __init__(self, bot):
        self.bot = bot
        self.bot = bot
        # 誕生日データ読み込み
        if pathlib.Path(BIRTHDAY_FILE).exists():
            with pathlib.Path(BIRTHDAY_FILE).open(encoding="utf-8") as f:
                self.birthdays = json.load(f)
        else:
            self.birthdays = {}

        # 起動時チェック
        bot.loop.create_task(self.check_birthdays_on_startup())
        # 毎日0時チェック
        self.check_birthdays.start()

    async def check_birthdays_on_startup(self):
        """起動時に今日の誕生日メンバーを祝う"""
        await self.bot.wait_until_ready()
        today = datetime.now().strftime("%m-%d")
        for guild in self.bot.guilds:
            for user_id, bday in self.birthdays.items():
                if bday == today:
                    member = guild.get_member(int(user_id))
                    if member:
                        channel = guild.system_channel or next(
                            (c for c in guild.text_channels if c.permissions_for(guild.me).send_messages),
                            None,
                        )
                        if channel:
                            await channel.send(
                                f"🎉 {member.mention} さん、お誕生日おめでとうございます！🎂（起動時チェック）"
                            )

    def cog_unload(self):
        self.check_birthdays.cancel()

    @tasks.loop(hours=24)
    async def check_birthdays(self):
        """毎日0時に誕生日チェック"""
        today = datetime.now().strftime("%m-%d")
        for guild in self.bot.guilds:
            for user_id, bday in self.birthdays.items():
                if bday == today:
                    member = guild.get_member(int(user_id))
                    if member:
                        channel = guild.system_channel or next(
                            (c for c in guild.text_channels if c.permissions_for(guild.me).send_messages),
                            None,
                        )
                        if channel:
                            await channel.send(f"🎉 {member.mention} さん、お誕生日おめでとうございます！🎂")

    @commands.command(name="set_birthday")
    async def set_birthday(self, ctx, month: int, day: int):
        """自分の誕生日を登録"""
        if month < 1 or month > 12 or day < 1 or day > 31:
            await ctx.send(" 無効な日付です。例: /set_birthday 10 13")
            return
        self.birthdays[str(ctx.author.id)] = f"{month:02d}-{day:02d}"
        with pathlib.Path(BIRTHDAY_FILE).open("w", encoding="utf-8") as f:
            json.dump(self.birthdays, f, ensure_ascii=False, indent=2)
        await ctx.send(f" {ctx.author.name} の誕生日を {month}月{day}日 に登録しました。")

    @commands.command(name="birthday_list")
    async def birthday_list(self, ctx):
        """全メンバーの誕生日一覧を表示"""
        if not self.birthdays:
            await ctx.send("📋 まだ登録された誕生日はありません。")
            return

        lines = []
        for user_id, bday in self.birthdays.items():
            member = ctx.guild.get_member(int(user_id))
            name = member.name if member else f"Unknown({user_id})"
            lines.append(f"{name} → {bday}")

        # Discordの文字数制限（約2000文字）に収まるよう分割
        message = "📋 **メンバー誕生日一覧** 📋\n" + "\n".join(lines)
        if len(message) > 1900:
            # 複数分割して送信
            chunks = [lines[i : i + 20] for i in range(0, len(lines), 20)]
            for chunk in chunks:
                await ctx.send("📋 **メンバー誕生日一覧** 📋\n" + "\n".join(chunk))
        else:
            await ctx.send(message)


# CogをBotに登録
async def setup(bot):
    await bot.add_cog(BirthdayManager(bot))
