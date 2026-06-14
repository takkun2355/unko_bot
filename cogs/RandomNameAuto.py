import logging

logger = logging.getLogger(__name__)
import random

import discord
from discord.ext import commands, tasks


class RandomNameAuto(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.change_name_loop.start()  # ループ開始

    def cog_unload(self):
        self.change_name_loop.cancel()  # Cogアンロード時に停止

    @commands.Cog.listener()
    async def on_ready(self):
        logger.info(" Bot起動完了。ランダムネーム変更タスクを起動します。")
        await self.change_name_once()  # 起動時にも1回実行

    @tasks.loop(hours=1)
    async def change_name_loop(self):
        """1時間ごとにランダムで名前変更"""
        await self.change_name_once()

    @commands.command()
    async def name(self, ctx):
        await self.change_name_once()
        await ctx.send(" ニックネームを変更しました。")

    async def change_name_once(self):
        """実際の変更処理"""
        # ===== 設定ここ =====
        guild_id = 1312457053708484609  # ← サーバーID
        user_id = 1118799600816492626  # ← 対象ユーザーID
        # ===================

        prefixes = [
            "スーパー",
            "激辛",
            "最強口臭",
            "謎の",
            "爆裂",
            "臭い",
            "最恐",
            "伝説",
            "ド変態",
            "ニ”ニー服来た",
        ]
        bases = [
            ":hugging:",
            "22",
            "ペブカック",
            "AGAり的",
            "full",
            "スーパー22人",
            "違法人",
            "ナナホシ",
            "有名人（笑）",
            "奇声虫",
        ]
        suffixes = [
            "AGA",
            "あがり",
            "242",
            "あーさん",
            "smell体",
            "22",
            "AGAり",
            "男性型脱毛症",
            "にがり",
            "ナナホシ",
        ]

        new_name = random.choice(prefixes) + random.choice(bases) + random.choice(suffixes)

        guild = self.bot.get_guild(guild_id)
        if not guild:
            logger.info("none! サーバーが見つかりません。guild_idを確認してください。")
            return

        member = guild.get_member(user_id)
        if not member:
            logger.info("none! メンバーが見つかりません。user_idを確認してください。")
            return

        try:
            await member.edit(nick=new_name)
            logger.info(f" {member.name} のニックネームを「{new_name}」に変更しました。")
        except discord.Forbidden:
            logger.info("[Warning] : 権限不足。ニックネームを変更できません。")
        except Exception as e:
            logger.info(f"[Warning] : {e}")


async def setup(bot):
    await bot.add_cog(RandomNameAuto(bot))
