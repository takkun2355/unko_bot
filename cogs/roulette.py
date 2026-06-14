import logging

logger = logging.getLogger(__name__)
import asyncio
import pathlib
import random
from datetime import datetime, timedelta

from discord.ext import commands


class Roulette(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.history = []  # 過去結果保存

    @commands.command()
    async def roulette(self, ctx, *args):
        """ルーレットコマンド
        使用例:
        ^^roulette fast loop topN5 countdown duplicate gif background winner sound history A B C,D.txt
        """
        if not args:
            await ctx.send(" 候補を指定してください！")
            return

        # ---------- 引数解析 ----------
        fast_mode = False
        loop_mode = False
        topN_mode = False
        countdown_mode = False
        duplicate_mode = False
        gif_mode = False
        background_mode = False
        winner_effect_mode = False
        sound_mode = False
        history_mode = False

        loop_count = 1
        topN_count = 3
        scheduled_time = None

        remaining_args = []
        for arg in args:
            low = arg.lower()
            if low == "fast":
                fast_mode = True
            elif low == "loop":
                loop_mode = True
            elif low.startswith("topn"):
                topN_mode = True
                try:
                    topN_count = int(low[4:])  # topN5なら5
                except:
                    topN_count = 3
            elif low == "countdown":
                countdown_mode = True
            elif low == "duplicate":
                duplicate_mode = True
            elif low == "gif":
                gif_mode = True
            elif low == "background":
                background_mode = True
            elif low == "winner":
                winner_effect_mode = True
            elif low == "sound":
                sound_mode = True
            elif low == "history":
                history_mode = True
            elif low.startswith("time:"):
                try:
                    scheduled_time = datetime.strptime(low[5:], "%H:%M")
                except:
                    await ctx.send(" 時間指定は HH:MM 形式で入力してください")
                    return
            elif low.isdigit() and loop_mode:
                loop_count = int(low)
            else:
                remaining_args.append(arg)

        # ---------- 候補取得 ----------
        candidates = []
        if len(remaining_args) == 1 and remaining_args[0].endswith(".txt"):
            filenames = remaining_args[0].split(",")  # 複数ファイル対応
            for filename in filenames:
                if not pathlib.Path(filename).exists():
                    await ctx.send(f" ファイル `{filename}` が見つかりません！")
                    return
                with pathlib.Path(filename).open(encoding="utf-8") as f:
                    candidates += [line.strip() for line in f if line.strip()]
        else:
            candidates = remaining_args

        if not candidates:
            await ctx.send(" 候補が空です！")
            return

        # ---------- 時間指定ルーレット ----------
        if scheduled_time:
            self.schedule_roulette(
                ctx,
                candidates,
                scheduled_time,
                fast_mode,
                topN_mode,
                topN_count,
                countdown_mode,
                duplicate_mode,
                gif_mode,
                background_mode,
                winner_effect_mode,
                sound_mode,
                history_mode,
                loop_count,
            )
            await ctx.send(f"⏰ {scheduled_time.strftime('%H:%M')} にルーレットを予約しました")
            return

        # ---------- 複数回ルーレット ----------
        for _ in range(loop_count):
            await self.run_roulette(
                ctx,
                candidates,
                fast_mode,
                topN_mode,
                topN_count,
                countdown_mode,
                duplicate_mode,
                gif_mode,
                background_mode,
                winner_effect_mode,
                sound_mode,
                history_mode,
            )

    # ---------- ルーレット実行 ----------
    async def run_roulette(
        self,
        ctx,
        candidates,
        fast_mode,
        topN_mode,
        topN_count,
        countdown_mode,
        duplicate_mode,
        gif_mode,
        background_mode,
        winner_effect_mode,
        sound_mode,
        history_mode,
    ):
        display_count = topN_count if topN_mode else 3

        # 重複あり対応
        pool = candidates.copy()
        if duplicate_mode:
            pool = candidates * 2

        # 即結果モード
        if fast_mode:
            final = random.sample(pool, min(display_count, len(pool)))
            await ctx.send(self.format_result(final, winner_effect_mode))
            if history_mode:
                self.history.append(final)
            return

        # 回転中メッセージ
        message = await ctx.send(" 回転中…")

        # カウントダウン演出
        if countdown_mode:
            for i in range(3, 0, -1):
                await message.edit(content=f" 回転開始まで… {i}")
                await asyncio.sleep(1)

        # GIF/背景演出（テキスト上で表現）
        if gif_mode:
            await message.edit(content="🎬 回転GIF表示中…")
            await asyncio.sleep(1)
        if background_mode:
            await message.edit(content="🖼 背景画像ランダム適用中…")
            await asyncio.sleep(1)

        # 回転演出
        shuffled = random.sample(pool, len(pool))
        delay = 0.1
        for choice in shuffled * 2:
            await message.edit(content=f" 回転中… → **{choice}**")
            await asyncio.sleep(delay)
            delay *= 1.1

        # 最終結果
        final = random.sample(pool, min(display_count, len(pool)))
        result_text = self.format_result(final, winner_effect_mode)
        await message.edit(content=result_text)

        if sound_mode:
            await ctx.send("🔊 音声通知再生（現在VC非対応のため使用不可）")

        if history_mode:
            self.history.append(final)

    # ---------- 結果フォーマット ----------
    def format_result(self, winners, winner_effect_mode):
        medals = ["🥇", "🥈", "🥉", "🏅", "🏅"]
        text = "🎉🏆 最終結果 🏆🎉\n"
        for idx, item in enumerate(winners):
            eff = "" if winner_effect_mode else ""
            text += f"{medals[idx]} {idx + 1}位: **{item}** {eff}\n"
        return text

    # ---------- 時間指定スケジュール ----------
    def schedule_roulette(
        self,
        ctx,
        candidates,
        scheduled_time,
        fast_mode,
        topN_mode,
        topN_count,
        countdown_mode,
        duplicate_mode,
        gif_mode,
        background_mode,
        winner_effect_mode,
        sound_mode,
        history_mode,
        loop_count,
    ):
        now = datetime.now()
        run_time = scheduled_time.replace(year=now.year, month=now.month, day=now.day)
        if run_time < now:
            run_time += timedelta(days=1)
        delay = (run_time - now).total_seconds()

        async def task():
            await asyncio.sleep(delay)
            for _ in range(loop_count):
                await self.run_roulette(
                    ctx,
                    candidates,
                    fast_mode,
                    topN_mode,
                    topN_count,
                    countdown_mode,
                    duplicate_mode,
                    gif_mode,
                    background_mode,
                    winner_effect_mode,
                    sound_mode,
                    history_mode,
                )

        self.bot.loop.create_task(task())

    # ---------- 履歴確認 ----------
    @commands.command()
    async def roulettehistory(self, ctx):
        if not self.history:
            await ctx.send("📜 履歴はまだありません")
            return
        text = "📜 過去ルーレット結果\n"
        for idx, entry in enumerate(self.history[-10:], start=1):
            text += f"{idx}: {', '.join(entry)}\n"
        await ctx.send(text)


# Cog をセットアップする関数
async def setup(bot):
    await bot.add_cog(Roulette(bot))
