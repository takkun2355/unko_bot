import discord
from discord.ext import commands
import json
import os

ACHIEVEMENT_FILE = "achievements.json"

# 発言数称号リスト（例: 25+1個）
MESSAGE_TITLES = [
    "初心者",
    "おしゃべりさん",
    "会話の達人",
    "雑談マスター",
    "社交家",
    "話題の中心",
    "チャットキング",
    "討論士",
    "文豪",
    "語彙の達人",
    "文才発揮",
    "伝説の話し手",
    "会話仙人",
    "雑談仙人",
    "神トーク",
    "チャット神",
    "語彙仙人",
    "文章魔術師",
    "会話魔神",
    "伝説の語り部",
    "無双トーカー",
    "話題製造機",
    "会話の鬼",
    "言葉の錬金術師",
    "チャットの神童",
    "秒速5チャット速度",
]

# リアクション称号リスト（例: 25+1個）
REACTION_TITLES = [
    "リアクション初心者",
    "リアクション名人",
    "リアクション達人",
    "リアクション仙人",
    "リアクション神",
    "Emojiマスター",
    "絵文字使い",
    "反応の達人",
    "リアクション魔神",
    "リアクションの鬼",
    "Emoji仙人",
    "反応仙人",
    "リアクション王",
    "絵文字王",
    "リアクション神童",
    "Emoji神童",
    "反応無双",
    "リアクション伝説",
    "絵文字伝説",
    "リアクション魔術師",
    "Emoji魔術師",
    "リアクション仙術師",
    "絵文字仙術師",
    "リアクション大神",
    "リアクション皇",
    "リアクションやりすぎ",
]


def get_triple_threshold(index):
    """指数的（3倍）で称号付与タイミングを計算"""
    return 3**index if index > 0 else 1


class Achievements(commands.Cog):
    """拡張実績システムCog（称号付与タイミング3倍）"""

    def __init__(self, bot):
        self.bot = bot
        if os.path.exists(ACHIEVEMENT_FILE):
            with open(ACHIEVEMENT_FILE, "r", encoding="utf-8") as f:
                self.data = json.load(f)
        else:
            self.data = {}

    async def save_data(self):
        with open(ACHIEVEMENT_FILE, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        user_id = str(message.author.id)
        self.data.setdefault(user_id, {"messages": 0, "reactions": 0, "titles": []})
        self.data[user_id]["messages"] += 1

        msg_count = self.data[user_id]["messages"]
        # 発言称号付与（3倍式）
        for i, title in enumerate(MESSAGE_TITLES):
            threshold = get_triple_threshold(i)
            if msg_count == threshold and title not in self.data[user_id]["titles"]:
                self.data[user_id]["titles"].append(title)
                await message.channel.send(
                    f"🏆 {message.author.name} に称号「{title}」を授与！"
                )
                break  # 1回の発言で1つだけ付与

        await self.save_data()

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if user.bot:
            return
        user_id = str(user.id)
        self.data.setdefault(user_id, {"messages": 0, "reactions": 0, "titles": []})
        self.data[user_id]["reactions"] += 1

        react_count = self.data[user_id]["reactions"]
        # リアクション称号付与（3倍式）
        for i, title in enumerate(REACTION_TITLES):
            threshold = get_triple_threshold(i)
            if react_count == threshold and title not in self.data[user_id]["titles"]:
                self.data[user_id]["titles"].append(title)
                await reaction.message.channel.send(
                    f"🏆 {user.name} に称号「{title}」を授与！"
                )
                break

        await self.save_data()

    @commands.command(name="titles")
    async def show_titles(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        user_id = str(member.id)
        titles = self.data.get(user_id, {}).get("titles", [])
        if titles:
            await ctx.send(f"🏅 {member.name} の称号↴ \n・{'\n・'.join(titles)}")
        else:
            await ctx.send(f"{member.name} はまだ称号を持っていません。")


# CogをBotに登録
async def setup(bot):
    await bot.add_cog(Achievements(bot))
