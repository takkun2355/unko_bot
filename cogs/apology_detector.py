# cogs/apology_detector.py

import discord
import re
import random
from discord.ext import commands


class ApologyDetector(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.chen_gifs = [
            "https://tenor.com/view/endfield-endfield-meme-endfield-chen-chen-chen-qianyu-gif-280722021857689086",
            "https://tenor.com/view/freaky-chen-arknights-endfield-arknights-endfield-gif-5344401584532729035",
            "https://tenor.com/view/chen-arknights-chen-qianyu-gif-649413829682882746",
            "https://tenor.com/view/chen-qianyu-gif-16353210392492534692",
        ]

        # 検知ワード
        self.misu = [
            r"ミス",
            r"バグ",
            r"エラー",
            r"不具合",
            r"問題",
            r"壊れ",
            r"故障",
            r"間違",
            r"違う",
            r"違って",
            r"おかしい",
            r"ズレ",
            r"動かない",
            r"反応しない",
            r"反映されない",
            r"表示されない",
            r"開けない",
            r"使えない",
            r"送れない",
            r"読み込めない",
            r"落ちた",
            r"クラッシュ",
            r"止まった",
            r"固まった",
            r"変わってる",
            r"変わった",
            r"変更されてる",
            r"変更された",
            r"bug",
            r"error",
            r"wrong",
            r"broken",
            r"issue",
            r"problem",
            r"crash",
            r"failed",
            r"fail",
            r"invalid",
            r"not work",
        ]

        self.gokai = [
            r"誤解",
            r"勘違い",
            r"誤認",
            r"誤読",
            r"思い込み",
            r"早合点",
            r"錯覚",
            r"誤判断",
            r"誤謬",
            r"失策",
            r"失念",
            r"見落とし",
            r"認識違い",
            r"取り違え",
            r"履き違え",
            r"先入観",
            r"独断",
            r"曲解",
            r"誤算",
            r"軽率",
            r"misconception",
            r"misunderstanding",
            r"misinterpretation",
            r"oversight",
            r"blunder",
            r"mistake",
            r"fallacy",
            r"confusion",
            r"assumption",
            r"misjudgment",
            r"miscalculation",
            r"misbelief",
            r"misreading",
            r"slipup",
            r"fauxpas",
            r"lapse",
            r"inaccuracy",
            r"misconceptional",
            r"erroneous",
            r"mistaken",
        ]

        target = (
            r"(?:"
            r"らむ(?:ちゃん|さん|様|さま|氏|くん|君|殿|先輩|先生)?|"
            r"<@1093434352026800139>(?:ちゃん|さん|様|さま|氏|くん|君|殿|先輩|先生)?"
            r")"
        )

        question = (
            r"(?:"
            r"何(?:を)?\s*(?:してる|してんの|してます|しています|"
            r"やってる|やってんの|やってます|やっています)"
            r"|"
            r"(?:忙しい|ひま|暇)"
            r"|"
            r"(?:してる|してんの|やってる|やってんの)\s*[？?]+"
            r")"
        )

        self.whatramdoing = [rf"{target}[\s\S]*?{question}"]

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        content = message.content.lower()

        # ミス系
        for pattern in self.misu:
            if re.search(pattern, content):
                await message.channel.send("あっちゃー、ごめんなさい！完全に私のミスです。")
                return

        # 勘違い系
        for pattern in self.gokai:
            if re.search(pattern, content):
                await message.channel.send(
                    "うわっと、これは私の大失誤（とんでもない勘違い）です！！大反省しています......！"
                )
                return

        # らむ何してる系
        for pattern in self.whatramdoing:
            if re.search(pattern, content):
                await message.channel.send(
                    f"らむは現在らムラムラしてしまい\n"
                    f"らむのらむをコシコシしてらむのらむからSirosiroさんを出しているんですね\n"
                    f"ん？ 名前をいっぱい入れてるだけで何の意味もないですよ？\n"
                    f"チェンセンユーも振り向きポーズしてるよ？\n"
                    f"{random.choice(self.chen_gifs)}"
                )
                return

    @commands.command(name="chen")
    async def chen(self, ctx):
        await ctx.send(f"{random.choice(self.chen_gifs)}")


async def setup(bot):
    await bot.add_cog(ApologyDetector(bot))
