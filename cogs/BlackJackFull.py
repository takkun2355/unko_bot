import discord
from discord.ext import commands
import random

SUITS = ["♠", "♥", "♦", "♣"]
RANKS = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]


def draw_card():
    return f"{random.choice(SUITS)}{random.choice(RANKS)}"


def card_value(card):
    rank = card[1:]  # ♠A → A
    if rank in ["J", "Q", "K", "10"]:
        return 10
    if rank == "A":
        return 11
    return int(rank)


def hand_value(cards):
    """手札の合計値計算（Aは11か1で最適化）"""
    total = sum(card_value(c) for c in cards)
    aces = sum(1 for c in cards if c[1:] == "A")
    while total > 21 and aces:
        total -= 10  # Aを11→1に変換
        aces -= 1
    return total


def get_game_type(number: int = None):
    if number is None:
        return 21
    return int(f"{number}1")


class BlackJackFull(commands.Cog):
    """本格ブラックジャックCog"""

    def __init__(self, bot):
        self.bot = bot
        self.games = {}  # {user_id: [cards]}

    @commands.command(name="blackjack")
    async def blackjack(self, ctx, number: int = None):
        user = ctx.author
        game_type = get_game_type(number)

        # 初めての場合は2枚配る
        if user.id not in self.games:
            self.games[user.id] = [draw_card(), draw_card()]
        else:
            # 既存ゲームなら1枚追加（ヒット）
            self.games[user.id].append(draw_card())

        hand = self.games[user.id]
        total = hand_value(hand)

        # DMで手札と合計表示
        try:
            await user.send(f"🃏 ブラックジャック [{game_type}] 現在の手札: {', '.join(hand)}\n合計値: {total}")
        except discord.Forbidden:
            await ctx.send(f"⚠️ {user.mention} にDMを送れません。DMを許可してください。")
            return

        # サーバーには進行状況だけ
        await ctx.send(
            f"🎲 {user.mention} さんがカードを引きました。 現在 {len(hand)} 枚目。種類: {game_type} 合計値非表示"
        )

        # バースト判定
        if total > 21:
            await ctx.send(f"💥 {user.mention} さんがバーストしました！手札: {len(hand)} 枚")
            del self.games[user.id]

    @commands.command(name="blackjack_reset")
    async def blackjack_reset(self, ctx):
        """ゲームをリセット"""
        user = ctx.author
        if user.id in self.games:
            del self.games[user.id]
        await ctx.send(f"{user.mention} さんのブラックジャックゲームをリセットしました。")


# Cog登録
async def setup(bot):
    await bot.add_cog(BlackJackFull(bot))
