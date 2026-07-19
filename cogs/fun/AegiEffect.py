# cogs/AegiEffect.py
import logging

logger = logging.getLogger(__name__)

import random

import discord
from discord.ext import commands

# 濁点（結合文字）: U+3099
COMBINING_DAKUTEN = "\u3099"

# 濁点を付ける対象
DAKUTEN_TARGETS = set(
    "あいうえおかきくけこさしすせそたちつてとはひふへほまみむめもやゆよらりるれろわをんぁぃぅぇぉゃゅょっゕㇰヶゎー"
)

# 文字重ねマッピング
KANA_TO_DOUBLE = {
    "あ": "ああ",
    "い": "いい",
    "う": "うう",
    "え": "ええ",
    "お": "おお",
    "か": "かか",
    "き": "きき",
    "く": "くく",
    "け": "けけ",
    "こ": "ここ",
    "さ": "ささ",
    "し": "しし",
    "す": "すす",
    "せ": "せせ",
    "そ": "そそ",
    "た": "たた",
    "ち": "ちち",
    "つ": "つつ",
    "て": "てて",
    "と": "とと",
    "な": "なな",
    "に": "にに",
    "ぬ": "ぬぬ",
    "ね": "ねね",
    "の": "のの",
    "は": "はは",
    "ひ": "ひひ",
    "ふ": "ふふ",
    "へ": "へへ",
    "ほ": "ほほ",
    "ま": "まま",
    "み": "みみ",
    "む": "むむ",
    "め": "めめ",
    "も": "もも",
    "や": "やや",
    "ゆ": "ゆゆ",
    "よ": "よよ",
    "ら": "らら",
    "り": "りり",
    "る": "るる",
    "れ": "れれ",
    "ろ": "ろろ",
    "わ": "わわ",
    "を": "をを",
    "ん": "んん",
    "が": "がが",
    "ぎ": "ぎぎ",
    "ぐ": "ぐぐ",
    "げ": "げげ",
    "ご": "ごご",
    "ざ": "ざざ",
    "じ": "じじ",
    "ず": "ずず",
    "ぜ": "ぜぜ",
    "ぞ": "ぞぞ",
    "だ": "だだ",
    "ぢ": "ぢぢ",
    "づ": "づづ",
    "で": "でで",
    "ど": "どど",
    "ば": "ばば",
    "び": "びび",
    "ぶ": "ぶぶ",
    "べ": "べべ",
    "ぼ": "ぼぼ",
    "ぱ": "ぱぱ",
    "ぴ": "ぴぴ",
    "ぷ": "ぷぷ",
    "ぺ": "ぺぺ",
    "ぽ": "ぽぽ",
    "ぁ": "ぁぁ",
    "ぃ": "ぃぃ",
    "ぅ": "ぅぅ",
    "ぇ": "ぇぇ",
    "ぉ": "ぉぉ",
    "ゃ": "ゃゃ",
    "ゅ": "ゅゅ",
    "ょ": "ょょ",
    "っ": "っっ",
    "ッ": "ッッ",
    "ゕ": "ゕゕ",
    "ㇰ": "ㇰㇰ",
    "ヶ": "ヶヶ",
    "ゎ": "ゎゎ",
    "ー": "ーー",
    "…": "……",
    "、": "、、",
    "！": "！！",
    "♥": "♥♥",
}

# 小文字マッピング
KANA_TO_SMALL = {
    "あ": "ぁ",
    "い": "ぃ",
    "う": "ぅ",
    "え": "ぇ",
    "お": "ぉ",
    "か": "ゕ",
    "く": "ㇰ",
    "け": "ヶ",
    "つ": "っ",
    "や": "ゃ",
    "ゆ": "ゅ",
    "よ": "ょ",
    "わ": "ゎ",
    "ぁ": "ぁ",
    "ぃ": "ぃ",
    "ぅ": "ぅ",
    "ぇ": "ぇ",
    "ぉ": "ぉ",
    "ゃ": "ゃ",
    "ゅ": "ゅ",
    "ょ": "ょ",
    "っ": "っ",
}

# 「っ」挿入可能な文字
TSU_TARGETS = set(
    "あいうえおかきくけこさしすせそたちつてとなにぬねの"
    "はひふへほまみむめもやゆよらりるれろわをん"
    "がぎぐげござじずぜぞだぢづでどばびぶべぼぱぴぷぺぽ"
    "ぁぃぅぇぉゃゅょっゕㇰヶゎー"
)


def apply_effect_19(text: str) -> str:
    """1パスで全エフェクトを適用:
    文字重ね(15-40%) + 小文字化(30-50%) + 「っ」挿入(10-25%) + 濁点(100%) + 行末♥
    """
    prob_double = random.randint(15, 40)
    prob_small = random.randint(30, 50)
    prob_tsu = random.randint(10, 25)

    lines = []
    for line in text.split("\n"):
        if not line.strip():
            lines.append(line)
            continue

        result_chars = []

        for ch in line:
            c = ch

            # 1. 文字重ね
            if c in KANA_TO_DOUBLE and random.randint(1, 100) <= prob_double:
                c = KANA_TO_DOUBLE[c]

            # 2. 小文字化（文字重ねた後の1文字目だけ対象）
            first_char = c[0]
            if first_char in KANA_TO_SMALL and random.randint(1, 100) <= prob_small:
                c = KANA_TO_SMALL[first_char] + c[1:] if len(c) > 1 else KANA_TO_SMALL[first_char]

            # 3. 濁点（結合文字として付与）
            c_with_daku = ""
            for cc in c:
                c_with_daku += cc
                if cc in DAKUTEN_TARGETS:
                    c_with_daku += COMBINING_DAKUTEN
            c = c_with_daku

            # 4. 「っ」挿入
            if c and c[0] in TSU_TARGETS and random.randint(1, 100) <= prob_tsu:
                c = c + "っ"

            result_chars.append(c)

        # 5. 行末♥
        line_result = "".join(result_chars).rstrip() + "♥"

        lines.append(line_result)

    return "\n".join(lines)


async def get_aegi_random_text(bot: commands.Bot, guild_id: int) -> str | None:
    """AegiGenerator から random 生成結果を取得"""
    cog = bot.get_cog("AegiGenerator")
    if not cog:
        return None

    try:
        from cogs.fun.AegiGenerator import GeneratorEngine

        settings = await cog.db.get_settings(guild_id)
        words = await cog.build_word_pool(guild_id)
    except Exception:
        return None

    if not words:
        return None

    max_count = max(3, min(random.randint(3, 25), len(words)))
    selected = random.sample(words, max_count)

    results = []
    for _ in range(3):
        shuffled = selected[:]
        random.shuffle(shuffled)
        temp_settings = dict(settings)
        temp_settings["sentence_count"] = 1
        line = GeneratorEngine.generate(shuffled, temp_settings)
        results.append(line)

    return "\n".join(results)


class AegiEffect(commands.Cog):
    """Bot発言にエフェクトをかける Cog"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.active_sessions: dict[int, set[str]] = {}
        self._skip_ids: set[int] = set()  # 加工しないメッセージID

    @commands.group(name="aegieffect", invoke_without_command=True)
    async def aegieffect(self, ctx: commands.Context) -> None:
        """エフェクト状態を表示"""
        if not ctx.guild:
            return

        effects = self.active_sessions.get(ctx.guild.id)
        if not effects:
            msg = await ctx.send("エフェクト: オフ")
        else:
            names = []
            if "19" in effects:
                names.append("19")
            if "3099" in effects:
                names.append("3099")
            msg = await ctx.send(f"エフェクト: オン ({', '.join(names)})")

        self._skip_ids.add(msg.id)  # このメッセージは加工しない

    @aegieffect.command(name="start")
    async def aegieffect_start(self, ctx: commands.Context, effect_type: str = "19") -> None:
        """エフェクト開始 (19 / 1919 / 3099)"""
        if not ctx.guild:
            return

        if effect_type in ("19", "1919"):
            key = "19"
            name = "19"
        elif effect_type == "3099":
            key = "3099"
            name = "3099"
        else:
            msg = await ctx.send(f"不明なエフェクト: {effect_type}\n使えるのは: 19, 1919, 3099")
            self._skip_ids.add(msg.id)
            return

        if ctx.guild.id not in self.active_sessions:
            self.active_sessions[ctx.guild.id] = set()

        self.active_sessions[ctx.guild.id].add(key)
        msg = await ctx.send(f"エフェクト開始: {name}")
        self._skip_ids.add(msg.id)

    @aegieffect.command(name="stop")
    async def aegieffect_stop(self, ctx: commands.Context, effect_type: str | None = None) -> None:
        """エフェクト停止（指定なしで全停止）"""
        if not ctx.guild:
            return

        if effect_type:
            if effect_type in ("19", "1919"):
                key = "19"
            elif effect_type == "3099":
                key = "3099"
            else:
                msg = await ctx.send(f"不明なエフェクト: {effect_type}")
                self._skip_ids.add(msg.id)
                return

            if ctx.guild.id in self.active_sessions:
                self.active_sessions[ctx.guild.id].discard(key)
                if not self.active_sessions[ctx.guild.id]:
                    del self.active_sessions[ctx.guild.id]
            msg = await ctx.send(f"エフェクト停止: {effect_type}")
        else:
            self.active_sessions.pop(ctx.guild.id, None)
            msg = await ctx.send("すべてのエフェクトを停止しました")

        self._skip_ids.add(msg.id)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """Botのメッセージをエフェクト加工"""
        if message.author != self.bot.user:
            return
        if not message.guild:
            return

        # スキップ対象
        if message.id in self._skip_ids:
            self._skip_ids.discard(message.id)
            return

        if message.guild.id not in self.active_sessions:
            return

        effects = self.active_sessions[message.guild.id]
        if not effects:
            return

        new_text = message.content

        is_embed = False
        if not new_text and message.embeds:
            embed = message.embeds[0]
            new_text = embed.description or ""
            is_embed = True

        if not new_text:
            return

        if "19" in effects:
            new_text = apply_effect_19(new_text)

        if "3099" in effects:
            aegi_text = await get_aegi_random_text(self.bot, message.guild.id)
            if aegi_text:
                new_text = new_text + "\n" + aegi_text

        try:
            if is_embed:
                embed = message.embeds[0]
                embed.description = new_text
                await message.edit(embed=embed)
            else:
                await message.edit(content=new_text)
        except (discord.HTTPException, discord.Forbidden):
            pass


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(AegiEffect(bot))
