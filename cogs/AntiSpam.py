import time
from collections import defaultdict, deque

from discord.ext import commands

# 設定
SPAM_LIMIT = 20  # 発言回数
TIME_WINDOW = 15  # 秒数（短時間の定義）


class AntiSpam(commands.Cog):
    """自動荒らし検知Cog（厳格版: 15秒以内20回）"""

    def __init__(self, bot):
        self.bot = bot
        self.user_messages = defaultdict(lambda: deque(maxlen=SPAM_LIMIT))

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        now = time.time()
        user_id = message.author.id

        # 発言履歴に追加
        self.user_messages[user_id].append(now)

        # SPAM_LIMIT回以上の発言がTIME_WINDOW秒以内かチェック
        timestamps = self.user_messages[user_id]
        if len(timestamps) == SPAM_LIMIT and (timestamps[-1] - timestamps[0]) <= TIME_WINDOW:
            await message.channel.send(f"⚠️ {message.author.mention} さん、15秒以内に20回発言しています！荒らし注意！")
            # 二重警告防止のため履歴をリセット
            self.user_messages[user_id].clear()


# CogをBotに登録
async def setup(bot):
    await bot.add_cog(AntiSpam(bot))
