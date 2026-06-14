# rpg_cog_full.py
from discord.ext import commands
import json
import os
import random
import asyncio

RPG_FOLDER = "rpg_data"

MONSTERS_NORMAL = [
    "スライム",
    "ゴブリン",
    "コボルト",
    "オーク",
    "ウルフ",
    "バット",
    "ゾンビ",
    "クモ",
    "サソリ",
    "カエル",
]
MONSTERS_RARE = ["ドラゴン", "ミノタウロス", "リッチ", "ワイバーン", "ヒドラ"]
MONSTERS_EPIC = ["古代ゴーレム", "大魔王"]

QUESTS = [
    "村の魔物を退治せよ",
    "森の盗賊を撃退せよ",
    "古代ゴーレム討伐",
    "鍋が踊りだした…止めよ",
    "空から降るパンを避けろ",
    "街を覆うスライム掃除",
    "町の噴水を元に戻せ",
    "迷子の子猫を救え",
    "巨大カボチャ退治",
    "港で海賊討伐",
    "森の狼を狩れ",
    "山賊のアジトを壊滅せよ",
    "火山のドラゴン討伐",
    "暴走する魔法の靴を止めよ",
    "呪われた森の探索",
    "王城の守衛を助けろ",
    "湖の怪物退治",
    "洞窟のゴブリン掃討",
    "砂漠の盗賊討伐",
    "幽霊船を撃退せよ",
]

SHOP_ITEMS = {
    "回復薬": {"効果": "HP10回復", "価格": 50},
    "大回復薬": {"効果": "HP全回復", "価格": 200},
    "攻撃強化薬": {"効果": "攻撃力+3", "価格": 100},
    "防御強化薬": {"効果": "防御力+3", "価格": 100},
    "魔法の巻物": {"効果": "ランダム効果", "価格": 150},
}


class RPGCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_battles = {}  # 通常戦闘中
        self.active_pvp = {}  # PvP戦闘待機

    # ----------------------
    # ユーザーフォルダ/セーブ
    # ----------------------
    def get_user_folder(self, user_id):
        folder = os.path.join(RPG_FOLDER, str(user_id))
        os.makedirs(folder, exist_ok=True)
        return folder

    def save_user(self, user_id, data):
        folder = self.get_user_folder(user_id)
        path = os.path.join(folder, "player.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def load_user(self, user_id):
        folder = self.get_user_folder(user_id)
        path = os.path.join(folder, "player.json")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return None

    # ----------------------
    # RPG開始/終了
    # ----------------------
    @commands.command(name="RPG開始")
    async def start_rpg(self, ctx):
        user_data = self.load_user(ctx.author.id)
        if not user_data:
            await ctx.send("キャラクターが存在しません。名前を入力してください:")

            def check(m):
                return m.author == ctx.author and m.channel == ctx.channel

            try:
                msg = await self.bot.wait_for("message", check=check, timeout=60)
                name = msg.content.strip()
                user_data = {
                    "name": name,
                    "level": 1,
                    "exp": 0,
                    "hp": 10,
                    "max_hp": 10,
                    "attack": 2,
                    "defense": 1,
                    "gold": 100,
                    "items": [],
                    "equipment": {},
                }
                self.save_user(ctx.author.id, user_data)
                await ctx.send(f"{name} を作成しました！")
            except:
                await ctx.send("時間切れです。もう一度RPG開始してください。")
                return
        else:
            await ctx.send(f"{user_data['name']} のデータを読み込みました！")
        await self.send_available_commands(ctx)

    @commands.command(name="RPG終了")
    async def end_rpg(self, ctx):
        user_data = self.load_user(ctx.author.id)
        if user_data:
            self.save_user(ctx.author.id, user_data)
        await ctx.send("ゲームを終了しました。セーブ済みです。")

    # ----------------------
    # 行動可能コマンド
    # ----------------------
    async def send_available_commands(self, ctx):
        cmds = (
            "次にできること:\n"
            "- ステータス\n- 所持品\n- 装備\n- クエスト\n"
            "- 攻撃\n- 防御\n- アイテム使用 <アイテム名>\n- 逃げる\n"
            "- 自動戦闘\n- ショップ\n- リセット\n- PVP開始 @相手"
        )
        await ctx.send(cmds)

    # ----------------------
    # 通常戦闘開始
    # ----------------------
    @commands.command(name="クエスト")
    async def start_quest(self, ctx):
        user_data = self.load_user(ctx.author.id)
        if not user_data:
            await ctx.send("キャラクターを作成してください。")
            return

        quest_text = random.choice(QUESTS)
        monster_name = random.choice(MONSTERS_NORMAL + MONSTERS_RARE + MONSTERS_EPIC)
        monster_level = max(1, user_data["level"] + random.randint(-5, 5))
        monster_hp = int(monster_level * 7.5)
        monster_attack = round((monster_level**3.5) / 2)
        monster_defense = round((monster_level**3) / 2)
        monster_exp = monster_level * 5
        monster_gold = monster_level * 2 + random.randint(0, 15)

        self.active_battles[ctx.author.id] = {
            "monster_name": monster_name,
            "monster_level": monster_level,
            "monster_hp": monster_hp,
            "monster_attack": monster_attack,
            "monster_defense": monster_defense,
            "monster_exp": monster_exp,
            "monster_gold": monster_gold,
            "user_hp": user_data["hp"],
        }

        await ctx.send(
            f"🗡️ クエスト: {quest_text}\nモンスター: {monster_name} (Lv{monster_level}) が出現！挑戦しますか？ yes/no"
        )

        def check(m):
            return (
                m.author == ctx.author
                and m.channel == ctx.channel
                and m.content.lower() in ["yes", "no"]
            )

        try:
            msg = await self.bot.wait_for("message", check=check, timeout=30)
            if msg.content.lower() == "yes":
                await ctx.send(f"{monster_name} に挑戦します！")
                await self.send_available_commands(ctx)
            else:
                await ctx.send("クエストをキャンセルしました。")
                self.active_battles.pop(ctx.author.id, None)
        except:
            await ctx.send("時間切れでクエストをキャンセルしました。")
            self.active_battles.pop(ctx.author.id, None)

    # ----------------------
    # ダメージ計算
    # ----------------------
    def calc_damage(self, attacker, defender):
        damage = max(0, attacker["attack"] - defender["defense"])
        return damage

    # ----------------------
    # プレイヤー攻撃
    # ----------------------
    @commands.command(name="攻撃")
    async def attack(self, ctx):
        if ctx.author.id not in self.active_battles:
            await ctx.send("現在戦闘中ではありません。")
            return

        battle = self.active_battles[ctx.author.id]
        user_data = self.load_user(ctx.author.id)

        # プレイヤー攻撃
        dmg_to_monster = max(0, user_data["attack"] - battle["monster_defense"])
        battle["monster_hp"] -= dmg_to_monster

        msg = f"{user_data['name']} の攻撃！{battle['monster_name']} に {dmg_to_monster} ダメージ！\n"

        # モンスター攻撃
        if battle["monster_hp"] > 0:
            dmg_to_player = max(0, battle["monster_attack"] - user_data["defense"])
            battle["user_hp"] -= dmg_to_player
            msg += f"{battle['monster_name']} の攻撃！{dmg_to_player} ダメージ！\n"

        # 戦闘結果チェック
        if battle["monster_hp"] <= 0:
            user_data["exp"] += battle["monster_exp"]
            user_data["gold"] += battle["monster_gold"]
            user_data["hp"] = battle["user_hp"]
            self.save_user(ctx.author.id, user_data)
            self.active_battles.pop(ctx.author.id)
            msg += f"🎉 {battle['monster_name']} を倒した！経験値 {battle['monster_exp']} 獲得、G {battle['monster_gold']} 獲得！"
        elif battle["user_hp"] <= 0:
            user_data["gold"] = max(0, user_data["gold"] - user_data["level"])
            user_data["hp"] = 1
            self.save_user(ctx.author.id, user_data)
            self.active_battles.pop(ctx.author.id)
            msg += (
                f"💀 {user_data['name']} は倒されました。G {user_data['level']} 減少！"
            )
        else:
            self.active_battles[ctx.author.id] = battle
            user_data["hp"] = battle["user_hp"]
            self.save_user(ctx.author.id, user_data)
            msg += f"現在HP: {battle['user_hp']} / {user_data['max_hp']}"

        await ctx.send(msg)

    # ----------------------
    # 防御コマンド
    # ----------------------
    @commands.command(name="防御")
    async def defend(self, ctx):
        if ctx.author.id not in self.active_battles:
            await ctx.send("現在戦闘中ではありません。")
            return

        battle = self.active_battles[ctx.author.id]
        user_data = self.load_user(ctx.author.id)

        # 防御するとダメージ半減
        dmg_to_player = max(0, (battle["monster_attack"] - user_data["defense"]) // 2)
        battle["user_hp"] -= dmg_to_player
        user_data["hp"] = battle["user_hp"]
        self.save_user(ctx.author.id, user_data)

        await ctx.send(
            f"{user_data['name']} は防御！{battle['monster_name']} の攻撃を半減 {dmg_to_player} ダメージ。現在HP: {battle['user_hp']} / {user_data['max_hp']}"
        )

    # ----------------------
    # アイテム使用
    # ----------------------
    @commands.command(name="アイテム使用")
    async def use_item(self, ctx, *, item_name: str):
        user_data = self.load_user(ctx.author.id)
        if not user_data or item_name not in user_data["items"]:
            await ctx.send("そのアイテムは持っていません。")
            return

        # 効果判定（回復・強化など）
        if "回復" in item_name:
            if "全" in item_name:
                user_data["hp"] = user_data["max_hp"]
            else:
                user_data["hp"] = min(user_data["max_hp"], user_data["hp"] + 10)
        elif "攻撃" in item_name:
            user_data["attack"] += 3
        elif "防御" in item_name:
            user_data["defense"] += 3
        user_data["items"].remove(item_name)
        self.save_user(ctx.author.id, user_data)

        await ctx.send(
            f"{user_data['name']} が {item_name} を使用！現在HP: {user_data['hp']} / {user_data['max_hp']}"
        )

    # ----------------------
    # 逃走コマンド
    # ----------------------
    @commands.command(name="逃げる")
    async def flee(self, ctx):
        if ctx.author.id not in self.active_battles:
            await ctx.send("戦闘中ではありません。")
            return

        if random.random() < 0.5:
            await ctx.send("逃げ成功！")
            self.active_battles.pop(ctx.author.id)
        else:
            await ctx.send("逃げ失敗！モンスターの攻撃！")
            battle = self.active_battles[ctx.author.id]
            user_data = self.load_user(ctx.author.id)
            dmg_to_player = max(0, battle["monster_attack"] - user_data["defense"])
            battle["user_hp"] -= dmg_to_player
            user_data["hp"] = battle["user_hp"]
            self.save_user(ctx.author.id, user_data)
            await ctx.send(
                f"{user_data['name']} は {dmg_to_player} ダメージを受けました。現在HP: {battle['user_hp']} / {user_data['max_hp']}"
            )

    # ----------------------
    # 自動戦闘
    # ----------------------
    @commands.command(name="自動戦闘")
    async def auto_battle(self, ctx):
        if ctx.author.id not in self.active_battles:
            await ctx.send("戦闘中ではありません。")
            return

        await ctx.send("自動戦闘開始！")
        while ctx.author.id in self.active_battles:
            await self.attack(ctx)
            await asyncio.sleep(1)

    # ----------------------
    # PvP戦闘コマンド
    # ----------------------
    @commands.command(name="攻撃_PvP")
    async def pvp_attack(self, ctx):
        user_data = self.load_user(ctx.author.id)
        target_id = None
        for k, v in self.active_pvp.items():
            if v.get("challenger") == ctx.author.id or k == ctx.author.id:
                target_id = k if k != ctx.author.id else v["challenger"]
                break
        if not target_id:
            await ctx.send("PvP中ではありません。")
            return
        target_data = self.load_user(target_id)

        dmg_to_target = max(0, user_data["attack"] - target_data["defense"])
        target_data["hp"] -= dmg_to_target
        self.save_user(target_id, target_data)

        msg = f"{user_data['name']} の攻撃！{target_data['name']} に {dmg_to_target} ダメージ！現在HP: {target_data['hp']} / {target_data['max_hp']}"

        if target_data["hp"] <= 0:
            user_data["gold"] += target_data["gold"]
            target_data["gold"] = 0
            target_data["hp"] = target_data["max_hp"]
            self.save_user(ctx.author.id, user_data)
            self.save_user(target_id, target_data)
            msg += f"\n🏆 {target_data['name']} を倒した！全Gを獲得！"
            self.active_pvp.pop(target_id, None)
        await ctx.send(msg)


# Cog登録
async def setup(bot):
    await bot.add_cog(RPGCog(bot))
