from discord.ext import commands
import random

# 返答パターン（無関係・予想外の返事）
RESPONSES = [
    "それより今日の天気はどう？☀️",
    "おっと、それは秘密だね🤫",
    "にゃんこが好きなんだね🐱",
    "今それ考えてる暇はないよ😎",
    "え、それは…宇宙の秘密かな🪐",
    "さあ、誰かに聞いてみたら？🤔",
    "ピザ食べた？🍕",
    "突然だけど、ダンスしよう💃🕺",
    "それは未来の自分に任せよう！🕰️",
    "急にだけど、口あg((( 終焉の残り香がするよ。",
    "残念、魔法が効かなかった！✨",
]


class WishBot(commands.Cog):
    """願い事Bot（全く違う返事を返す）"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="wish")
    async def make_wish(self, ctx, *, wish: str):
        """ユーザーの願いに対して全く違う返事を返す"""
        response = random.choice(RESPONSES)
        await ctx.send(f"💭 {ctx.author.name} の願い: 「{wish}」\n🎲 願いの結果: {response}")


# CogをBotに登録
async def setup(bot):
    await bot.add_cog(WishBot(bot))
