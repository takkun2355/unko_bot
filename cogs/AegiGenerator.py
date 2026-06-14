# cogs/AegiGenerator.py

from __future__ import annotations

import random
import json
from pathlib import Path

import aiosqlite
import discord
from discord.ext import commands

DB_PATH = "data/aegi.db"

MASTER_WORDS = {
    "normal": [
        "！？",
        "あ…ん",
        "あ",
        "ア",
        "アァ",
        "ああ",
        "あぁん",
        "あぅ",
        "あぇ",
        "あっあ",
        "あん",
        "い",
        "いぃい",
        "う",
        "うう",
        "うぐ",
        "うっ…んん",
        "え",
        "オ",
        "お",
        "おぉお",
        "く",
        "くぅ",
        "は",
        "はぁ",
        "はぁはぁ",
        "はう",
        "ひう",
        "ん",
        "ン",
        "んぁ",
        "んあ",
        "んう",
        "んぅう",
        "んはっ",
        "んん",
    ],
    "dakuten": [
        "あ゙",
        "あ゙ぁ",
        "あ゙ぁぁ",
        "あ゙あ゙あ゙",
        "あ゙あうあ",
        "あぁっあ゙",
        "あぁんん゙",
        "あ゙うぅ",
        "あ゙ぐ",
        "ア゙ッア゙ッア゙",
        "あ゙っあ゙っあ゙っあ゙",
        "あ゙んあ゙",
        "い゙ぅ",
        "い゙ゔ",
        "うぐ",
        "ゔっあ゙ぁ",
        "うっぐ",
        "ゔん゙ん",
        "え゙う",
        "お゙",
        "オ゙",
        "お゙あ",
        "お゙ぉお゙",
        "おぐ",
        "お゙ぐぅ゙",
        "お゙ッお゙ッお゙ッお゙",
        "お゙っお゙っお゙っオ゙ォ゙",
        "おっん゙",
        "お゙ん゙",
        "ギ",
        "ぐ",
        "ぐあ゙",
        "くそ、おお゙ぉ゙",
        "ぐる、じ",
        "ひぐ",
        "ふぎ",
        "ふぐ",
        "ふぐぅ",
        "ま゙",
        "ン゙",
        "ん゙ア゙ァ゙",
        "ん゙うぅうう",
        "んお゙",
        "んぎぃ",
        "ん゙ほぉ",
    ],
    "kairaku": [
        "あ、やば…",
        "いっぱいしてぇ",
        "お゙、かしぐな゙",
        "お゙がじぐな゙、あ゙",
        "おかしくな",
        "おかしくなりゅ",
        "きもちい",
        "きもちいぃ",
        "ぎも゙ぢいがらあぁ",
        "きもひい゙",
        "きも゙ひい",
        "こすれ、るぅ",
        "ごんごん突いて",
        "じぬ゙",
        "しぬぅ",
        "しゅき",
        "しゅきぃ",
        "しゅごいぃ",
        "しんじゃうぅ",
        "すご",
        "ずぽずぽしてぇ",
        "ずぽずぽ好き",
        "そこやばい",
        "それ好きぃ",
        "ちょうだい",
        "ほし、ほしい",
        "も、もういい、もういい",
        "も…っとぉ",
        "もういいからぁ",
        "もっと",
        "もっとしてぇ",
        "もっと奥ぅ゙",
        "もっと突いてぇ",
        "もっと欲しいぃい",
        "やばぃい",
        "ヤバっ",
        "壊れちゃ",
        "激し",
        "好き",
        "好きぃ",
        "突いて",
    ],
    "zeccho": [
        "い、ぐぅう",
        "イ゙",
        "イイ",
        "イき、そ",
        "イ゙ぎだい゙",
        "イきたくな",
        "イ゙ぎだくな",
        "イ゙ぎだくない゙ぃ",
        "いぐ…",
        "イクイクいぐい゙",
        "イ゙グぅ゙",
        "イクッ！",
        "いくっいく",
        "イくの、む゙り゙",
        "イくの、止まらなっ",
        "イっ",
        "イ゙った",
        "イ゙っちゃ",
        "いっちゃうぅ",
        "ぐっいぐイグぅう",
        "クる",
        "でちゃうぅ゙ゔ",
        "でるっでるでちゃ",
        "なんか、きちゃ",
        "なんか出ちゃ",
        "イぐのやだっ",
        "も、出る゙ぅ",
        "も…イぎだくな゙い゙っ",
        "もぉイけな",
        "出る゙",
    ],
    "teikou": [
        "い、いや",
        "イヤ゙ぁ゙あ゙ああぁ",
        "いやだ",
        "イヤ゙だぁあ゙",
        "いや゙っ、あ゙",
        "いや゙っ",
        "う…そ",
        "お゙ぐや゙ぁ゙っ",
        "お゙わって",
        "ぐちゃぐちゃや゙め゙",
        "こ、こわ",
        "こないで",
        "こないでぇえ",
        "ごめ゙、なさい゙ぃ",
        "こわい",
        "ずぽずぽや゙だぁ",
        "そこじゃな",
        "た、たす",
        "だ、め",
        "だずげでぇえ゙",
        "ちが",
        "ちがうちがうぅ",
        "な、なに",
        "なに、これ",
        "ぬ、ぬい、へ",
        "ぬいて",
        "ぬ゙いで",
        "はなじでぇ",
        "ヒ",
        "ヒィ",
        "も゙、だめ",
        "も゙、らめ",
        "もうだめ",
        "や、やだ",
        "や゙",
        "やだやだ",
        "や゙っあ゙ぁああ゙",
        "や゙め",
        "や゙めぇ",
        "やめでえ",
        "やめてくださ",
        "や゙らぁ",
        "奥だめ",
        "奥やだ",
        "止まってぇえ",
        "助け",
        "挿れちゃやだ",
        "挿れな…でぇ",
        "抜い…",
    ],
}


KANA_TO_VOWEL = {
    "あ": "あ",
    "か": "あ",
    "さ": "あ",
    "た": "あ",
    "な": "あ",
    "は": "あ",
    "ま": "あ",
    "や": "あ",
    "ら": "あ",
    "わ": "あ",
    "が": "あ",
    "ざ": "あ",
    "だ": "あ",
    "ば": "あ",
    "ぱ": "あ",
    "い": "い",
    "き": "い",
    "し": "い",
    "ち": "い",
    "に": "い",
    "ひ": "い",
    "み": "い",
    "り": "い",
    "ぎ": "い",
    "じ": "い",
    "ぢ": "い",
    "び": "い",
    "ぴ": "い",
    "う": "う",
    "く": "う",
    "す": "う",
    "つ": "う",
    "ぬ": "う",
    "ふ": "う",
    "む": "う",
    "ゆ": "う",
    "る": "う",
    "ぐ": "う",
    "ず": "う",
    "づ": "う",
    "ぶ": "う",
    "ぷ": "う",
    "え": "え",
    "け": "え",
    "せ": "え",
    "て": "え",
    "ね": "え",
    "へ": "え",
    "め": "え",
    "れ": "え",
    "げ": "え",
    "ぜ": "え",
    "で": "え",
    "べ": "え",
    "ぺ": "え",
    "お": "お",
    "こ": "お",
    "そ": "お",
    "と": "お",
    "の": "お",
    "ほ": "お",
    "も": "お",
    "よ": "お",
    "ろ": "お",
    "を": "お",
    "ご": "お",
    "ぞ": "お",
    "ど": "お",
    "ぼ": "お",
    "ぽ": "お",
}

SMALL_VOWELS = {"あ": "ぁ", "い": "ぃ", "う": "ぅ", "え": "ぇ", "お": "ぉ"}

DEFAULT_SETTINGS = {
    "insert_comma": True,
    "comma_prob": 50,
    "insert_dots": True,
    "dots_prob": 50,
    "insert_period": True,
    "period_prob": 50,
    "insert_heart": True,
    "heart_prob": 50,
    "insert_exclamation": True,
    "exclamation_prob": 50,
    "star_enabled": True,
    "star_prob": 50,
    "circle_enabled": True,
    "circle_prob": 50,
    "kana_enabled": True,
    "kana_prob": 50,
    "kana_count": 2,
    "sentence_count": 3,
    "output_separator": "newline",
}

SEPARATOR_MAP = {
    "newline": "\n",
    "space": " ",
    "none": "",
}

CATEGORY_ORDER = ["normal", "dakuten", "kairaku", "zeccho", "teikou", "custom"]

EMPTY_WORD_PLACEHOLDER = "__empty__"


def split_message(text: str, limit: int = 1900) -> list[str]:
    """
    メッセージを行単位で制限文字数に分割。
    改行がない場合は文字単位でフォールバック。
    """
    if "\n" not in text:
        chunks: list[str] = []
        while len(text) > limit:
            chunks.append(text[:limit])
            text = text[limit:]
        chunks.append(text)
        return chunks

    chunks = []
    current_chunk: list[str] = []
    current_length = 0

    for line in text.split("\n"):
        line_len = len(line) + 1

        if current_length + line_len > limit and current_chunk:
            chunks.append("\n".join(current_chunk))
            current_chunk = []
            current_length = 0

        current_chunk.append(line)
        current_length += line_len

    if current_chunk:
        chunks.append("\n".join(current_chunk))

    return chunks if chunks else [text]


class DatabaseManager:
    """データベース管理クラス"""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path

    async def initialize(self) -> None:
        """データベースの初期化"""
        Path("data").mkdir(exist_ok=True)

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
            CREATE TABLE IF NOT EXISTS guild_settings(
                guild_id INTEGER PRIMARY KEY,
                settings_json TEXT NOT NULL
            )
            """)

            await db.execute("""
            CREATE TABLE IF NOT EXISTS guild_custom_words(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                word TEXT NOT NULL,
                UNIQUE(guild_id, word)
            )
            """)

            await db.execute("""
            CREATE TABLE IF NOT EXISTS guild_disabled_words(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                word TEXT NOT NULL,
                UNIQUE(guild_id, word)
            )
            """)

            await db.commit()

    async def get_settings(self, guild_id: int) -> dict:
        """サーバー設定を取得"""
        async with aiosqlite.connect(self.db_path) as db:
            cur = await db.execute(
                "SELECT settings_json FROM guild_settings WHERE guild_id=?", (guild_id,)
            )
            row = await cur.fetchone()

            if row:
                return json.loads(row[0])

            await db.execute(
                "INSERT INTO guild_settings VALUES (?,?)",
                (guild_id, json.dumps(DEFAULT_SETTINGS)),
            )
            await db.commit()
            return DEFAULT_SETTINGS.copy()

    async def save_settings(self, guild_id: int, settings: dict) -> None:
        """サーバー設定を保存"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "REPLACE INTO guild_settings VALUES (?,?)",
                (guild_id, json.dumps(settings)),
            )
            await db.commit()

    async def add_custom_word(self, guild_id: int, word: str) -> None:
        """カスタム単語を追加（重複無視）"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT OR IGNORE INTO guild_custom_words (guild_id, word) VALUES (?,?)",
                (guild_id, word),
            )
            await db.commit()

    async def remove_custom_word(self, guild_id: int, word: str) -> None:
        """カスタム単語を削除"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "DELETE FROM guild_custom_words WHERE guild_id=? AND word=?",
                (guild_id, word),
            )
            await db.commit()

    async def get_custom_words(self, guild_id: int) -> list[str]:
        """カスタム単語一覧を取得"""
        async with aiosqlite.connect(self.db_path) as db:
            cur = await db.execute(
                "SELECT word FROM guild_custom_words WHERE guild_id=?", (guild_id,)
            )
            rows = await cur.fetchall()
            return [r[0] for r in rows]

    async def disable_word(self, guild_id: int, word: str) -> None:
        """単語を無効化（重複無視）"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT OR IGNORE INTO guild_disabled_words (guild_id, word) VALUES (?,?)",
                (guild_id, word),
            )
            await db.commit()

    async def enable_word(self, guild_id: int, word: str) -> None:
        """単語を有効化"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "DELETE FROM guild_disabled_words WHERE guild_id=? AND word=?",
                (guild_id, word),
            )
            await db.commit()

    async def get_disabled_words(self, guild_id: int) -> list[str]:
        """無効化単語一覧を取得"""
        async with aiosqlite.connect(self.db_path) as db:
            cur = await db.execute(
                "SELECT word FROM guild_disabled_words WHERE guild_id=?", (guild_id,)
            )
            rows = await cur.fetchall()
            return [r[0] for r in rows]

    async def reset_guild(self, guild_id: int) -> None:
        """サーバーの全データをリセット"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM guild_settings WHERE guild_id=?", (guild_id,))
            await db.execute(
                "DELETE FROM guild_custom_words WHERE guild_id=?", (guild_id,)
            )
            await db.execute(
                "DELETE FROM guild_disabled_words WHERE guild_id=?", (guild_id,)
            )
            await db.commit()


class GeneratorEngine:
    """文章生成エンジン"""

    @classmethod
    def add_kana_effect(cls, word: str, settings: dict) -> str:
        """単語内にかな文字効果を追加"""
        if not settings.get("kana_enabled", True):
            return word

        result = ""
        for ch in word:
            result += ch
            if ch in KANA_TO_VOWEL and random.randint(1, 100) <= settings.get(
                "kana_prob", 50
            ):
                vowel = KANA_TO_VOWEL[ch]
                for _ in range(settings.get("kana_count", 2)):
                    if random.random() < 0.5:
                        result += vowel
                    else:
                        result += SMALL_VOWELS[vowel]
        return result

    @classmethod
    def insert_inside_word(cls, word: str, settings: dict) -> str:
        """単語内部に記号を挿入"""
        result = ""
        for ch in word:
            result += ch
            if settings.get("star_enabled", True) and random.randint(
                1, 100
            ) <= settings.get("star_prob", 50):
                result += "っ"
            if settings.get("circle_enabled", True) and random.randint(
                1, 100
            ) <= settings.get("circle_prob", 50):
                result += "…"
        return result

    @classmethod
    def get_separator(cls, settings: dict) -> str:
        """区切り文字を解決"""
        separator_value = settings.get("output_separator", "newline")
        # 定義済みキーならマップから、それ以外はカスタム値としてそのまま使う
        return SEPARATOR_MAP.get(separator_value, separator_value)

    @classmethod
    def generate(cls, words: list[str], settings: dict) -> str:
        """メインの文章生成"""
        if not words:
            return "単語がありません"

        sentence_count = max(1, min(settings.get("sentence_count", 3), 10))
        separator = cls.get_separator(settings)

        results = []

        for _ in range(sentence_count):
            shuffled = words[:]
            random.shuffle(shuffled)

            sentence = ""

            for word in shuffled:
                word = cls.add_kana_effect(word, settings)
                word = cls.insert_inside_word(word, settings)

                sentence += word

                if settings.get("insert_comma", True) and random.randint(
                    1, 100
                ) <= settings.get("comma_prob", 50):
                    sentence += "、"

                if settings.get("insert_period", True) and random.randint(
                    1, 100
                ) <= settings.get("period_prob", 50):
                    sentence += "…"

                if settings.get("insert_dots", True) and random.randint(
                    1, 100
                ) <= settings.get("dots_prob", 50):
                    sentence += random.choice(["っ", "ッ"])

                if settings.get("insert_heart", True) and random.randint(
                    1, 100
                ) <= settings.get("heart_prob", 50):
                    sentence += "♥"

                if settings.get("insert_exclamation", True) and random.randint(
                    1, 100
                ) <= settings.get("exclamation_prob", 50):
                    sentence += "！"

            results.append(sentence)

        return separator.join(results)


class CustomSession:
    """(guild_id, user_id) ごとのカスタム単語セッション"""

    def __init__(self):
        self.words: list[str] = []

    def add(self, word: str) -> None:
        if word not in self.words:
            self.words.append(word)

    def remove(self, word: str) -> None:
        if word in self.words:
            self.words.remove(word)

    def clear(self) -> None:
        self.words.clear()


# ---------- 単語取得 ----------


async def get_category_words_async(
    guild_id: int, category: str, db: DatabaseManager
) -> list[str]:
    """カテゴリに応じた単語リストを非同期で返す"""
    if category == "custom":
        return await db.get_custom_words(guild_id)
    return MASTER_WORDS.get(category, [])


async def get_all_category_words_with_meta(
    guild_id: int, db: DatabaseManager
) -> dict[str, list[str]]:
    """全カテゴリの単語を {category: [words]} で返す"""
    result: dict[str, list[str]] = {}
    for cat in CATEGORY_ORDER:
        result[cat] = await get_category_words_async(guild_id, cat, db)
    return result


# ---------- UI Components ----------


class BackButton(discord.ui.Button):
    """戻るボタン（汎用）"""

    def __init__(self, target_view: discord.ui.View):
        super().__init__(label="戻る", style=discord.ButtonStyle.gray)
        self.target_view = target_view

    async def callback(self, interaction: discord.Interaction) -> None:
        await interaction.response.edit_message(view=self.target_view)


class GenerateButton(discord.ui.Button):
    """生成ボタン"""

    def __init__(self, guild_id: int, user_id: int):
        super().__init__(label="生成", style=discord.ButtonStyle.green)
        self.guild_id = guild_id
        self.user_id = user_id

    async def callback(self, interaction: discord.Interaction) -> None:
        cog = interaction.client.get_cog("AegiGenerator")
        if not cog:
            return

        session = cog.get_custom_session(self.guild_id, self.user_id)
        if not session.words:
            await interaction.response.send_message(
                "単語を選択してください", ephemeral=True
            )
            return

        settings = await cog.db.get_settings(self.guild_id)
        result = GeneratorEngine.generate(session.words, settings)

        chunks = split_message(result)
        await interaction.response.send_message(chunks[0], ephemeral=True)
        for chunk in chunks[1:]:
            await interaction.followup.send(chunk, ephemeral=True)


class ClearButton(discord.ui.Button):
    """リセットボタン"""

    def __init__(self, guild_id: int, user_id: int):
        super().__init__(label="リセット", style=discord.ButtonStyle.red)
        self.guild_id = guild_id
        self.user_id = user_id

    async def callback(self, interaction: discord.Interaction) -> None:
        cog = interaction.client.get_cog("AegiGenerator")
        if cog:
            session = cog.get_custom_session(self.guild_id, self.user_id)
            session.clear()
        await interaction.response.send_message("リセットしました", ephemeral=True)


class WordSelectBase(discord.ui.Select):
    """単語選択の基底クラス"""

    def __init__(self, words: list[str], page: int, placeholder: str):
        self.page = page

        start = page * 5
        end = start + 5
        page_words = words[start:end]

        if page_words:
            options = [discord.SelectOption(label=w[:100], value=w) for w in page_words]
        else:
            options = [
                discord.SelectOption(label="単語なし", value=EMPTY_WORD_PLACEHOLDER)
            ]

        super().__init__(placeholder=placeholder, options=options)


class DisableWordSelect(WordSelectBase):
    """無効化/有効化用の単語選択"""

    def __init__(
        self,
        guild_id: int,
        category: str,
        page: int,
        disable_mode: bool,
        words: list[str],
    ):
        super().__init__(words, page, "単語選択")
        self.guild_id = guild_id
        self.category = category
        self.disable_mode = disable_mode

    async def callback(self, interaction: discord.Interaction) -> None:
        word = self.values[0]
        if word == EMPTY_WORD_PLACEHOLDER:
            await interaction.response.send_message("単語がありません", ephemeral=True)
            return

        cog = interaction.client.get_cog("AegiGenerator")
        if not cog:
            return

        if self.disable_mode:
            await cog.db.disable_word(self.guild_id, word)
            msg = f"無効化: {word}"
        else:
            await cog.db.enable_word(self.guild_id, word)
            msg = f"有効化: {word}"

        await interaction.response.send_message(msg, ephemeral=True)


class CustomWordSelect(WordSelectBase):
    """カスタムセッション用の単語選択"""

    def __init__(
        self, guild_id: int, user_id: int, category: str, page: int, words: list[str]
    ):
        super().__init__(words, page, "単語追加")
        self.guild_id = guild_id
        self.user_id = user_id
        self.category = category

    async def callback(self, interaction: discord.Interaction) -> None:
        word = self.values[0]
        if word == EMPTY_WORD_PLACEHOLDER:
            await interaction.response.send_message("単語がありません", ephemeral=True)
            return

        cog = interaction.client.get_cog("AegiGenerator")
        if not cog:
            return

        session = cog.get_custom_session(self.guild_id, self.user_id)
        session.add(word)
        await interaction.response.send_message(f"追加: {word}", ephemeral=True)


class DisablePageButton(discord.ui.Button):
    """無効化/有効化モード用ページボタン"""

    def __init__(
        self,
        guild_id: int,
        category: str,
        disable_mode: bool,
        page: int,
        direction: int,
    ):
        label = "▶" if direction > 0 else "◀"
        super().__init__(label=label, style=discord.ButtonStyle.blurple)
        self.guild_id = guild_id
        self.category = category
        self.disable_mode = disable_mode
        self.page = page
        self.direction = direction

    async def callback(self, interaction: discord.Interaction) -> None:
        cog = interaction.client.get_cog("AegiGenerator")
        if not cog:
            return

        words = await get_category_words_async(self.guild_id, self.category, cog.db)
        new_page = max(0, self.page + self.direction)
        view = await DisableWordView.create(
            self.guild_id, self.category, self.disable_mode, new_page, cog.db
        )
        await interaction.response.edit_message(view=view)


class CustomPageButton(discord.ui.Button):
    """カスタムセッション用ページボタン"""

    def __init__(
        self, guild_id: int, user_id: int, category: str, page: int, direction: int
    ):
        label = "▶" if direction > 0 else "◀"
        super().__init__(label=label, style=discord.ButtonStyle.blurple)
        self.guild_id = guild_id
        self.user_id = user_id
        self.category = category
        self.page = page
        self.direction = direction

    async def callback(self, interaction: discord.Interaction) -> None:
        cog = interaction.client.get_cog("AegiGenerator")
        if not cog:
            return

        words = await get_category_words_async(self.guild_id, self.category, cog.db)
        new_page = max(0, self.page + self.direction)
        view = await CustomWordView.create(
            self.guild_id, self.user_id, self.category, new_page, cog.db
        )
        await interaction.response.edit_message(view=view)


class CategorySelectBase(discord.ui.Select):
    """カテゴリ選択の基底クラス"""

    def __init__(self, placeholder: str, all_words: dict[str, list[str]]):
        options = []
        for cat in CATEGORY_ORDER:
            count = len(all_words.get(cat, []))
            if cat == "custom":
                label = f"custom ({count})"
            else:
                label = f"{cat} ({count})"
            options.append(discord.SelectOption(label=label, value=cat))

        super().__init__(placeholder=placeholder, options=options)


class DisableCategorySelect(CategorySelectBase):
    """無効化/有効化モード用カテゴリ選択"""

    def __init__(
        self, guild_id: int, disable_mode: bool, all_words: dict[str, list[str]]
    ):
        super().__init__("カテゴリ選択", all_words)
        self.guild_id = guild_id
        self.disable_mode = disable_mode
        self.all_words = all_words

    async def callback(self, interaction: discord.Interaction) -> None:
        cog = interaction.client.get_cog("AegiGenerator")
        if not cog:
            return

        category = self.values[0]
        words = await get_category_words_async(self.guild_id, category, cog.db)
        view = await DisableWordView.create(
            self.guild_id, category, self.disable_mode, 0, cog.db
        )
        await interaction.response.edit_message(content=f"{category}", view=view)


class CustomCategorySelect(CategorySelectBase):
    """カスタムセッション用カテゴリ選択"""

    def __init__(self, guild_id: int, user_id: int, all_words: dict[str, list[str]]):
        super().__init__("カテゴリ", all_words)
        self.guild_id = guild_id
        self.user_id = user_id
        self.all_words = all_words

    async def callback(self, interaction: discord.Interaction) -> None:
        cog = interaction.client.get_cog("AegiGenerator")
        if not cog:
            return

        category = self.values[0]
        words = await get_category_words_async(self.guild_id, category, cog.db)
        view = await CustomWordView.create(
            self.guild_id, self.user_id, category, 0, cog.db
        )
        await interaction.response.edit_message(
            content=f"カテゴリ: {category}", view=view
        )


class DisableWordView(discord.ui.View):
    """無効化/有効化モードの単語選択ビュー"""

    def __init__(
        self,
        guild_id: int,
        category: str,
        disable_mode: bool,
        page: int,
        words: list[str],
        db: DatabaseManager,
    ):
        super().__init__(timeout=300)
        self.guild_id = guild_id
        self.category = category
        self.disable_mode = disable_mode
        self.page = page
        self.words = words
        self._db = db

        self.add_item(DisableWordSelect(guild_id, category, page, disable_mode, words))

        max_page = (len(words) - 1) // 5

        if page > 0:
            self.add_item(DisablePageButton(guild_id, category, disable_mode, page, -1))
        if page < max_page:
            self.add_item(DisablePageButton(guild_id, category, disable_mode, page, 1))

    async def _build_back_view(self) -> discord.ui.View:
        return await DisableCategoryView.create(
            self.guild_id, self.disable_mode, self._db
        )

    async def add_back_button(self) -> None:
        back_view = await self._build_back_view()
        self.add_item(BackButton(back_view))

    @classmethod
    async def create(
        cls,
        guild_id: int,
        category: str,
        disable_mode: bool,
        page: int,
        db: DatabaseManager,
    ) -> "DisableWordView":
        words = await get_category_words_async(guild_id, category, db)
        view = cls(guild_id, category, disable_mode, page, words, db)
        await view.add_back_button()
        return view


class DisableCategoryView(discord.ui.View):
    """無効化/有効化モードのカテゴリ選択ビュー"""

    def __init__(
        self, guild_id: int, disable_mode: bool, all_words: dict[str, list[str]]
    ):
        super().__init__(timeout=300)
        self.add_item(DisableCategorySelect(guild_id, disable_mode, all_words))

    @classmethod
    async def create(
        cls, guild_id: int, disable_mode: bool, db: DatabaseManager
    ) -> "DisableCategoryView":
        all_words = await get_all_category_words_with_meta(guild_id, db)
        return cls(guild_id, disable_mode, all_words)


class CustomWordView(discord.ui.View):
    """カスタムセッションの単語選択ビュー"""

    def __init__(
        self, guild_id: int, user_id: int, category: str, page: int, words: list[str]
    ):
        super().__init__(timeout=300)

        self.add_item(CustomWordSelect(guild_id, user_id, category, page, words))

        max_page = (len(words) - 1) // 5

        if page > 0:
            self.add_item(CustomPageButton(guild_id, user_id, category, page, -1))
        if page < max_page:
            self.add_item(CustomPageButton(guild_id, user_id, category, page, 1))

        self.add_item(GenerateButton(guild_id, user_id))
        self.add_item(ClearButton(guild_id, user_id))

    async def add_back_button(
        self, guild_id: int, user_id: int, db: DatabaseManager
    ) -> None:
        back_view = await CustomCategoryView.create(guild_id, user_id, db)
        self.add_item(BackButton(back_view))

    @classmethod
    async def create(
        cls, guild_id: int, user_id: int, category: str, page: int, db: DatabaseManager
    ) -> "CustomWordView":
        words = await get_category_words_async(guild_id, category, db)
        view = cls(guild_id, user_id, category, page, words)
        await view.add_back_button(guild_id, user_id, db)
        return view


class CustomCategoryView(discord.ui.View):
    """カスタムセッションのカテゴリ選択ビュー"""

    def __init__(self, guild_id: int, user_id: int, all_words: dict[str, list[str]]):
        super().__init__(timeout=300)
        self.add_item(CustomCategorySelect(guild_id, user_id, all_words))
        self.add_item(GenerateButton(guild_id, user_id))
        self.add_item(ClearButton(guild_id, user_id))

    @classmethod
    async def create(
        cls, guild_id: int, user_id: int, db: DatabaseManager
    ) -> "CustomCategoryView":
        all_words = await get_all_category_words_with_meta(guild_id, db)
        return cls(guild_id, user_id, all_words)


# ---------- Setting UI ----------


class ToggleButton(discord.ui.Button):
    """ON/OFF 切り替えボタン"""

    def __init__(
        self, guild_id: int, key: str, current_value: bool, db: DatabaseManager
    ):
        self.guild_id = guild_id
        self.key = key
        self.db = db

        label = f"{key}: {'ON' if current_value else 'OFF'}"
        style = discord.ButtonStyle.green if current_value else discord.ButtonStyle.red
        super().__init__(label=label, style=style)

    async def callback(self, interaction: discord.Interaction) -> None:
        settings = await self.db.get_settings(self.guild_id)
        settings[self.key] = not settings.get(self.key, True)
        await self.db.save_settings(self.guild_id, settings)

        view = await SettingView.create(self.guild_id, self.db)
        await interaction.response.edit_message(view=view)


class ProbModal(discord.ui.Modal, title="確率設定"):
    """確率入力用モーダル (0-100)"""

    value = discord.ui.TextInput(label="確率 (0-100)", required=True)

    def __init__(self, guild_id: int, key: str, db: DatabaseManager):
        super().__init__()
        self.guild_id = guild_id
        self.key = key
        self.db = db

    async def on_submit(self, interaction: discord.Interaction) -> None:
        try:
            value = int(str(self.value))
            value = max(0, min(value, 100))
        except ValueError:
            await interaction.response.send_message(
                "0〜100の数字を入力してください", ephemeral=True
            )
            return

        settings = await self.db.get_settings(self.guild_id)
        settings[self.key] = value
        await self.db.save_settings(self.guild_id, settings)

        view = await SettingView.create(self.guild_id, self.db)
        await interaction.response.edit_message(view=view)


class KanaCountModal(discord.ui.Modal, title="かな文字連続数"):
    """kana_count 専用モーダル (1-6)"""

    value = discord.ui.TextInput(label="連続数 (1-6)", required=True)

    def __init__(self, guild_id: int, key: str, db: DatabaseManager):
        super().__init__()
        self.guild_id = guild_id
        self.key = key
        self.db = db

    async def on_submit(self, interaction: discord.Interaction) -> None:
        try:
            value = int(str(self.value))
            value = max(1, min(value, 6))
        except ValueError:
            await interaction.response.send_message(
                "1〜6の数字を入力してください", ephemeral=True
            )
            return

        settings = await self.db.get_settings(self.guild_id)
        settings[self.key] = value
        await self.db.save_settings(self.guild_id, settings)

        view = await SettingView.create(self.guild_id, self.db)
        await interaction.response.edit_message(view=view)


class SentenceCountModal(discord.ui.Modal, title="生成行数"):
    """sentence_count 専用モーダル (1-10)"""

    value = discord.ui.TextInput(label="行数 (1-10)", required=True)

    def __init__(self, guild_id: int, key: str, db: DatabaseManager):
        super().__init__()
        self.guild_id = guild_id
        self.key = key
        self.db = db

    async def on_submit(self, interaction: discord.Interaction) -> None:
        try:
            value = int(str(self.value))
            value = max(1, min(value, 10))
        except ValueError:
            await interaction.response.send_message(
                "1〜10の数字を入力してください", ephemeral=True
            )
            return

        settings = await self.db.get_settings(self.guild_id)
        settings[self.key] = value
        await self.db.save_settings(self.guild_id, settings)

        view = await SettingView.create(self.guild_id, self.db)
        await interaction.response.edit_message(view=view)


class ProbButton(discord.ui.Button):
    """数値設定ボタン"""

    def __init__(
        self, guild_id: int, key: str, current_value: int | str, db: DatabaseManager
    ):
        self.guild_id = guild_id
        self.key = key
        self.db = db

        label = f"{key}: {current_value}"
        super().__init__(label=label, style=discord.ButtonStyle.blurple)

    async def callback(self, interaction: discord.Interaction) -> None:
        if self.key == "kana_count":
            modal = KanaCountModal(self.guild_id, self.key, self.db)
        elif self.key == "sentence_count":
            modal = SentenceCountModal(self.guild_id, self.key, self.db)
        else:
            modal = ProbModal(self.guild_id, self.key, self.db)
        await interaction.response.send_modal(modal)


class SeparatorSelect(discord.ui.Select):
    """出力区切り文字選択"""

    def __init__(self, guild_id: int, current_value: str, db: DatabaseManager):
        self.guild_id = guild_id
        self.db = db

        is_custom = current_value not in SEPARATOR_MAP

        options = [
            discord.SelectOption(
                label="改行 (newline)",
                value="newline",
                default=(current_value == "newline"),
            ),
            discord.SelectOption(
                label="スペース (space)",
                value="space",
                default=(current_value == "space"),
            ),
            discord.SelectOption(
                label="なし (none)", value="none", default=(current_value == "none")
            ),
            discord.SelectOption(
                label=f"カスタム: {current_value}"
                if is_custom
                else "カスタム (custom)",
                value="__custom__",
                default=is_custom,
            ),
        ]

        super().__init__(placeholder=f"区切り: {current_value}", options=options)

    async def callback(self, interaction: discord.Interaction) -> None:
        value = self.values[0]

        if value == "__custom__":
            modal = CustomSeparatorModal(self.guild_id, self.db)
            await interaction.response.send_modal(modal)
        else:
            settings = await self.db.get_settings(self.guild_id)
            settings["output_separator"] = value
            await self.db.save_settings(self.guild_id, settings)

            view = await SettingView.create(self.guild_id, self.db)
            await interaction.response.edit_message(view=view)


class CustomSeparatorModal(discord.ui.Modal, title="カスタム区切り文字"):
    """カスタム区切り文字入力"""

    value = discord.ui.TextInput(label="区切り文字", required=True, max_length=10)

    def __init__(self, guild_id: int, db: DatabaseManager):
        super().__init__()
        self.guild_id = guild_id
        self.db = db

    async def on_submit(self, interaction: discord.Interaction) -> None:
        custom_sep = str(self.value)

        settings = await self.db.get_settings(self.guild_id)
        settings["output_separator"] = custom_sep
        await self.db.save_settings(self.guild_id, settings)

        view = await SettingView.create(self.guild_id, self.db)
        await interaction.response.edit_message(view=view)


class SettingView(discord.ui.View):
    """設定変更ビュー"""

    TOGGLE_KEYS = [
        "insert_comma",
        "insert_dots",
        "insert_period",
        "insert_heart",
        "insert_exclamation",
        "star_enabled",
        "circle_enabled",
        "kana_enabled",
    ]

    PROB_KEYS = [
        "comma_prob",
        "dots_prob",
        "period_prob",
        "heart_prob",
        "exclamation_prob",
        "star_prob",
        "circle_prob",
        "kana_prob",
    ]

    def __init__(self, guild_id: int, db: DatabaseManager, settings: dict):
        super().__init__(timeout=300)
        self.guild_id = guild_id
        self.db = db

        for key in self.TOGGLE_KEYS:
            self.add_item(ToggleButton(guild_id, key, settings.get(key, True), db))

        for key in self.PROB_KEYS:
            self.add_item(ProbButton(guild_id, key, settings.get(key, 50), db))

        self.add_item(
            ProbButton(guild_id, "kana_count", settings.get("kana_count", 2), db)
        )
        self.add_item(
            ProbButton(
                guild_id, "sentence_count", settings.get("sentence_count", 3), db
            )
        )

        sep_value = settings.get("output_separator", "newline")
        self.add_item(SeparatorSelect(guild_id, sep_value, db))

    @classmethod
    async def create(cls, guild_id: int, db: DatabaseManager) -> "SettingView":
        settings = await db.get_settings(guild_id)
        return cls(guild_id, db, settings)


# ---------- Main Cog ----------


class AegiGenerator(commands.Cog):
    """あえぎ声生成 Cog"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = DatabaseManager()
        self.custom_sessions: dict[tuple[int, int], CustomSession] = {}

    async def cog_load(self) -> None:
        """Cog読み込み時にDB初期化"""
        await self.db.initialize()
        print("[AegiGenerator] Ready")

    def get_custom_session(self, guild_id: int, user_id: int) -> CustomSession:
        """(guild_id, user_id) でカスタムセッションを取得"""
        key = (guild_id, user_id)
        if key not in self.custom_sessions:
            self.custom_sessions[key] = CustomSession()
        return self.custom_sessions[key]

    async def build_word_pool(self, guild_id: int) -> list[str]:
        """有効な全単語を取得"""
        words = [word for category in MASTER_WORDS.values() for word in category]

        custom_words = await self.db.get_custom_words(guild_id)
        disabled_words = await self.db.get_disabled_words(guild_id)

        words.extend(custom_words)

        disabled = set(disabled_words)
        words = [w for w in words if w not in disabled]
        return words

    @commands.group(name="aegi", invoke_without_command=True)
    async def aegi(self, ctx: commands.Context) -> None:
        """デフォルトの文章生成"""
        if ctx.guild is None:
            await ctx.send("サーバー内のみ対応")
            return

        settings = await self.db.get_settings(ctx.guild.id)
        words = await self.build_word_pool(ctx.guild.id)
        result = GeneratorEngine.generate(words, settings)

        for chunk in split_message(result):
            await ctx.send(chunk)

    @aegi.command(name="all")
    async def aegi_all(self, ctx: commands.Context, mode: str | None = None) -> None:
        """全単語表示 - カテゴリを選択して表示"""
        if mode == "code":
            all_words = await get_all_category_words_with_meta(ctx.guild.id, self.db)
            lines = []
            for category in CATEGORY_ORDER:
                lines.append(f"[{category}]")
                lines.extend(all_words.get(category, []))
                lines.append("")
            text = "\n".join(lines) or "空"
            payload = f"```txt\n{text}\n```"
            for chunk in split_message(payload):
                await ctx.send(chunk)
        else:
            # UIでカテゴリ選択 → ページ分割表示
            view = await AllWordsCategoryView.create(ctx.guild.id, self.db)
            await ctx.send("カテゴリを選択してください", view=view)

    @aegi.command(name="random")
    async def aegi_random(self, ctx: commands.Context) -> None:
        """ランダムな単語数(3〜25)を選び、3通りの並び順で生成"""
        if ctx.guild is None:
            await ctx.send("サーバー内のみ対応")
            return

        settings = await self.db.get_settings(ctx.guild.id)
        words = await self.build_word_pool(ctx.guild.id)

        if not words:
            await ctx.send("単語がありません")
            return

        # ランダムな単語数を決定（最大でも全単語数まで、最低3）
        max_count = max(3, min(random.randint(3, 25), len(words)))
        selected = random.sample(words, max_count)

        # 3通りの並び順で生成
        results = []
        for _ in range(3):
            shuffled = selected[:]
            random.shuffle(shuffled)

            # sentence_count=1 で1行ずつ、区切りは設定通り
            temp_settings = dict(settings)
            temp_settings["sentence_count"] = 1

            line = GeneratorEngine.generate(shuffled, temp_settings)
            results.append(line)

        # 3メッセージに分けて送信
        for result in results:
            await ctx.send(result)

    @aegi.command(name="category")
    async def aegi_category(
        self, ctx: commands.Context, category: str | None = None
    ) -> None:
        """カテゴリ別単語表示"""
        if category is None:
            embed = discord.Embed(title="カテゴリ一覧")
            all_words = await get_all_category_words_with_meta(ctx.guild.id, self.db)
            for cat in CATEGORY_ORDER:
                count = len(all_words.get(cat, []))
                embed.add_field(name=f"{cat} ({count})", value=" ", inline=False)
            await ctx.send(embed=embed)
            return

        category = category.lower()
        if category not in CATEGORY_ORDER:
            await ctx.send("存在しないカテゴリ")
            return

        words = await get_category_words_async(ctx.guild.id, category, self.db)
        text = "\n".join(words) or "空"
        for chunk in split_message(text):
            await ctx.send(chunk)

    @aegi.command(name="add")
    @commands.has_guild_permissions(manage_guild=True)
    async def aegi_add(self, ctx: commands.Context, *, word: str) -> None:
        """カスタム単語追加"""
        word = word.strip()
        if not word:
            await ctx.send("単語が空")
            return

        await self.db.add_custom_word(ctx.guild.id, word)
        await ctx.send(f"追加しました: {word}")

    @aegi.command(name="remove")
    @commands.has_guild_permissions(manage_guild=True)
    async def aegi_remove(self, ctx: commands.Context, *, word: str) -> None:
        """カスタム単語削除"""
        await self.db.remove_custom_word(ctx.guild.id, word)
        await ctx.send(f"削除しました: {word}")

    @aegi.command(name="mywords")
    async def aegi_mywords(self, ctx: commands.Context) -> None:
        """追加単語一覧"""
        words = await self.db.get_custom_words(ctx.guild.id)
        if not words:
            await ctx.send("追加単語なし")
            return

        text = "\n".join(words)
        for chunk in split_message(text):
            await ctx.send(chunk)

    @aegi.command(name="reset")
    @commands.has_guild_permissions(manage_guild=True)
    async def aegi_reset(self, ctx: commands.Context) -> None:
        """設定リセット"""
        await self.db.reset_guild(ctx.guild.id)
        await ctx.send("設定をリセットしました")

    @aegi.command(name="disable")
    async def aegi_disable(self, ctx: commands.Context) -> None:
        """単語を無効化"""
        view = await DisableCategoryView.create(ctx.guild.id, True, self.db)
        await ctx.send("無効化する単語を選択", view=view)

    @aegi.command(name="enable")
    async def aegi_enable(self, ctx: commands.Context) -> None:
        """単語を有効化"""
        view = await DisableCategoryView.create(ctx.guild.id, False, self.db)
        await ctx.send("有効化する単語を選択", view=view)

    @aegi.command(name="custom")
    async def aegi_custom(self, ctx: commands.Context) -> None:
        """カスタムセッションで生成"""
        view = await CustomCategoryView.create(ctx.guild.id, ctx.author.id, self.db)
        await ctx.send("カテゴリ選択", view=view)

    @aegi.command(name="setting")
    async def aegi_setting(self, ctx: commands.Context) -> None:
        """設定変更"""
        view = await SettingView.create(ctx.guild.id, self.db)
        await ctx.send("設定変更", view=view)


# ---------- All Words Paged View ----------


class AllWordsPageButton(discord.ui.Button):
    """単語一覧ページ送りボタン"""

    def __init__(
        self,
        guild_id: int,
        category: str,
        page: int,
        direction: int,
        db: DatabaseManager,
    ):
        label = "▶" if direction > 0 else "◀"
        super().__init__(label=label, style=discord.ButtonStyle.blurple)
        self.guild_id = guild_id
        self.category = category
        self.page = page
        self.direction = direction
        self.db = db

    async def callback(self, interaction: discord.Interaction) -> None:
        new_page = max(0, self.page + self.direction)
        view = await AllWordsView.create(
            self.guild_id, self.category, new_page, self.db
        )
        await interaction.response.edit_message(view=view)


class AllWordsView(discord.ui.View):
    """ページ分割された単語一覧ビュー"""

    WORDS_PER_PAGE = 100

    def __init__(
        self,
        guild_id: int,
        category: str,
        page: int,
        words: list[str],
        db: DatabaseManager,
    ):
        super().__init__(timeout=300)
        self.guild_id = guild_id
        self.category = category
        self.page = page
        self.words = words
        self._db = db

        total_pages = max(1, (len(words) - 1) // self.WORDS_PER_PAGE + 1)

        if page > 0:
            self.add_item(AllWordsPageButton(guild_id, category, page, -1, db))
        if page < total_pages - 1:
            self.add_item(AllWordsPageButton(guild_id, category, page, 1, db))

    async def add_back_button(self) -> None:
        back_view = await AllWordsCategoryView.create(self.guild_id, self._db)
        self.add_item(BackButton(back_view))

    @classmethod
    async def create(
        cls, guild_id: int, category: str, page: int, db: DatabaseManager
    ) -> "AllWordsView":
        words = await get_category_words_async(guild_id, category, db)
        view = cls(guild_id, category, page, words, db)
        await view.add_back_button()
        return view

    async def format_content(self) -> str:
        """現在のページの内容をフォーマット"""
        start = self.page * self.WORDS_PER_PAGE
        end = start + self.WORDS_PER_PAGE
        page_words = self.words[start:end]

        total_pages = max(1, (len(self.words) - 1) // self.WORDS_PER_PAGE + 1)

        lines = [
            f"【{self.category}】 ({len(self.words)}単語) ページ {self.page + 1}/{total_pages}",
            "─" * 30,
        ]
        lines.extend(page_words)

        return "\n".join(lines) if page_words else f"【{self.category}】\n単語なし"


class AllWordsCategorySelect(discord.ui.Select):
    """単語一覧用カテゴリ選択"""

    def __init__(
        self, guild_id: int, all_words: dict[str, list[str]], db: DatabaseManager
    ):
        self.guild_id = guild_id
        self._db = db

        options = []
        for cat in CATEGORY_ORDER:
            count = len(all_words.get(cat, []))
            if cat == "custom":
                label = f"custom ({count})"
            else:
                label = f"{cat} ({count})"
            options.append(discord.SelectOption(label=label, value=cat))

        super().__init__(placeholder="カテゴリを選択", options=options)

    async def callback(self, interaction: discord.Interaction) -> None:
        category = self.values[0]
        view = await AllWordsView.create(self.guild_id, category, 0, self._db)
        content = await view.format_content()
        await interaction.response.edit_message(content=content, view=view)


class AllWordsCategoryView(discord.ui.View):
    """単語一覧カテゴリ選択ビュー"""

    def __init__(
        self, guild_id: int, all_words: dict[str, list[str]], db: DatabaseManager
    ):
        super().__init__(timeout=300)
        self.add_item(AllWordsCategorySelect(guild_id, all_words, db))

    @classmethod
    async def create(cls, guild_id: int, db: DatabaseManager) -> "AllWordsCategoryView":
        all_words = await get_all_category_words_with_meta(guild_id, db)
        return cls(guild_id, all_words, db)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(AegiGenerator(bot))
