import logging

logger = logging.getLogger(__name__)
import asyncio
import json
import pathlib
import random

from discord.ext import commands

CUSTOM_WORD_FILE = "custom_words.txt"
ROOM_FILE = "rooms.json"
RANK_FILE = "rankings.json"


def load_words():
    if not pathlib.Path(CUSTOM_WORD_FILE).exists():
        raise FileNotFoundError(f"{CUSTOM_WORD_FILE} が見つかりません。作成してください。")
    with pathlib.Path(CUSTOM_WORD_FILE).open(encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


def save_json(path, data):
    with pathlib.Path(path).open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_json(path):
    if not pathlib.Path(path).exists():
        return {}
    with pathlib.Path(path).open(encoding="utf-8") as f:
        return json.load(f)


class Shiritori(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.words = load_words()
        self.rooms = load_json(ROOM_FILE)
        self.rankings = load_json(RANK_FILE)

    @commands.command()
    async def create(self, ctx, room_name: str, password: str):
        if room_name in self.rooms:
            await ctx.send("その部屋名は既に存在します。")
            return
        self.rooms[room_name] = {"password": password, "players": [], "used_words": []}
        save_json(ROOM_FILE, self.rooms)
        await ctx.send(f"部屋 {room_name} を作成しました。パスワードを控えておいてください。")

    @commands.command()
    async def join(self, ctx, room_name: str, password: str):
        if room_name not in self.rooms:
            await ctx.send("その部屋は存在しません。")
            return
        if self.rooms[room_name]["password"] != password:
            await ctx.send("パスワードが違います。")
            return
        if ctx.author.name in self.rooms[room_name]["players"]:
            await ctx.send("既に参加済みです。")
            return
        self.rooms[room_name]["players"].append(ctx.author.name)
        save_json(ROOM_FILE, self.rooms)
        await ctx.send(f"{ctx.author.name} が {room_name} に参加しました。")

    @commands.command()
    async def leave(self, ctx, room_name: str):
        if room_name not in self.rooms:
            await ctx.send("その部屋は存在しません。")
            return
        if ctx.author.name not in self.rooms[room_name]["players"]:
            await ctx.send("あなたはその部屋に参加していません。")
            return
        self.rooms[room_name]["players"].remove(ctx.author.name)
        save_json(ROOM_FILE, self.rooms)
        await ctx.send(f"{ctx.author.name} が {room_name} から退出しました。")

    @commands.command()
    async def start(self, ctx, room_name: str, word_mode: str = "custom", bot_mode: str = None):
        if room_name not in self.rooms:
            await ctx.send("その部屋は存在しません。")
            return
        room = self.rooms[room_name]
        players = room["players"].copy()
        if bot_mode == "bot":
            players.append("Bot")

        if not players:
            await ctx.send("プレイヤーがいません。")
            return

        used_words = room.get("used_words", [])
        await ctx.send(f"しりとり開始！単語モード: {word_mode} | プレイヤー: {', '.join(players)}")
        await self.run_game(ctx, room_name, players, used_words, word_mode)

    async def run_game(self, ctx, room_name, players, used_words, word_mode):
        turn_index = 0
        last_char = random.choice(self.words)[0]
        await ctx.send(f"初手文字: {last_char}")

        while True:
            current_player = players[turn_index % len(players)]
            await ctx.send(f"現在のターン: {current_player}")

            if current_player == "Bot":
                candidate_words = [w for w in self.words if w[0] == last_char and w not in used_words]
                if not candidate_words:
                    await ctx.send("Botは単語が出せず負け！")
                    self.update_rank(room_name, "Bot", False)
                    break
                word = random.choice(candidate_words)
                await asyncio.sleep(0.5)
                await ctx.send(f"Bot: {word}")
            else:

                def check(m):
                    return m.author.name == current_player and m.channel == ctx.channel

                try:
                    msg = await self.bot.wait_for("message", check=check, timeout=60)
                    word = msg.content.strip()
                except TimeoutError:
                    await ctx.send(f"{current_player} が時間切れで負け！")
                    self.update_rank(room_name, current_player, False)
                    break

            if word[-1] == "ん":
                await ctx.send(f"{current_player} が「ん」で終了、負け！")
                self.update_rank(room_name, current_player, False)
                break

            used_words.append(word)
            last_char = word[-1]
            turn_index += 1
            self.rooms[room_name]["used_words"] = used_words
            save_json(ROOM_FILE, self.rooms)

    def update_rank(self, room_name, player_name, win=True):
        key = f"{room_name}_{player_name}"
        if key not in self.rankings:
            self.rankings[key] = {"win": 0, "lose": 0}
        if win:
            self.rankings[key]["win"] += 1
        else:
            self.rankings[key]["lose"] += 1
        save_json(RANK_FILE, self.rankings)

    @commands.command()
    async def rank(self, ctx, room_name: str):
        ranking_list = []
        for key, record in self.rankings.items():
            room, player = key.split("_", 1)
            if room != room_name:
                continue
            total = record["win"] + record["lose"]
            winrate = record["win"] / total if total > 0 else 0
            ranking_list.append((player, record["win"], record["lose"], winrate))
        ranking_list.sort(key=lambda x: x[3], reverse=True)
        msg = f"🏆 {room_name} ランキングTOP5 🏆\n"
        for i, (player, w, l, rate) in enumerate(ranking_list[:5], 1):
            msg += f"{i}. {player} : {w}勝{l}敗 (勝率 {rate:.2f})\n"
        await ctx.send(msg)


# async setup に統一
async def setup(bot):
    await bot.add_cog(Shiritori(bot))
