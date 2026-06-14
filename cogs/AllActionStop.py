"""
bot_control.py
==============
スコープ付きでコマンドを停止／一時停止／再開するCog。

スコープオプション:
    all       - 全サーバーに適用（オーナー専用）
    server    - 実行サーバーのみ（サーバー管理者以上）
    category  - 指定カテゴリのみ（サーバー管理者以上）
    channel   - 指定チャンネルのみ（サーバー管理者以上）

コマンド例:
    ^^commandstop all
    ^^commandstop server
    ^^commandstop category 📢アナウンス
    ^^commandstop channel #general

    ^^pause all
    ^^pause server
    ^^pause category 📢アナウンス
    ^^pause channel #general

    ^^resume all
    ^^resume server
    ^^resume category 📢アナウンス
    ^^resume channel #general

    ^^cmdinitstats       ← 現在いるチャンネルの状態を確認

組み込み方:
    既存の main.py に以下を1行追加するだけ:
        await bot.load_extension("cogs.bot_control")
"""

import asyncio
import discord
from discord.ext import commands
import logging
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
#  状態定義
# ─────────────────────────────────────────────
class BotState(Enum):
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"


# ─────────────────────────────────────────────
#  スコープ別状態ストア
# ─────────────────────────────────────────────
_global_state: BotState = BotState.RUNNING
_server_states: dict[int, BotState] = {}  # guild_id   -> BotState
_category_states: dict[int, BotState] = {}  # category_id -> BotState
_channel_states: dict[int, BotState] = {}  # channel_id  -> BotState


def _effective_state(ctx: commands.Context) -> BotState:
    """
    チャンネル > カテゴリ > サーバー > グローバル の優先順位で
    そのコンテキストに適用される状態を返す。
    いずれかのスコープが STOPPED なら STOPPED を優先する。
    """
    states = [_global_state]

    if ctx.guild:
        states.append(_server_states.get(ctx.guild.id, BotState.RUNNING))

    if hasattr(ctx.channel, "category") and ctx.channel.category:
        states.append(_category_states.get(ctx.channel.category.id, BotState.RUNNING))

    states.append(_channel_states.get(ctx.channel.id, BotState.RUNNING))

    if BotState.STOPPED in states:
        return BotState.STOPPED
    if BotState.PAUSED in states:
        return BotState.PAUSED
    return BotState.RUNNING


# ─────────────────────────────────────────────
#  実行中タスクの追跡
#  key: message_id  value: (Task, Context)
# ─────────────────────────────────────────────
_running_tasks: dict[int, tuple[asyncio.Task, commands.Context]] = {}


# ─────────────────────────────────────────────
#  カスタム例外
# ─────────────────────────────────────────────
class CommandStoppedError(commands.CheckFailure):
    def __init__(self):
        super().__init__("コマンドは現在完全停止中です。")


class BotPausedError(commands.CheckFailure):
    def __init__(self):
        super().__init__("Botは現在一時停止中です。")


# ─────────────────────────────────────────────
#  グローバルチェック
# ─────────────────────────────────────────────
async def bot_state_check(ctx: commands.Context) -> bool:
    if isinstance(ctx.cog, BotControl):
        return True
    state = _effective_state(ctx)
    if state == BotState.STOPPED:
        raise CommandStoppedError()
    if state == BotState.PAUSED:
        raise BotPausedError()
    return True


# ─────────────────────────────────────────────
#  スコープ解決ユーティリティ
# ─────────────────────────────────────────────
async def _resolve_scope(
    ctx: commands.Context,
    scope: str,
    target: Optional[str],
) -> tuple[bool, str, Optional[int]]:
    """
    (成功フラグ, エラーメッセージ or スコープ説明, スコープID or None) を返す。
    スコープIDは server/category/channel のみ使用。
    """
    scope = scope.lower()

    if scope == "all":
        return True, "全サーバー", None

    if scope == "server":
        if not ctx.guild:
            return False, "このコマンドはサーバー内でのみ使用できます。", None
        return True, f"サーバー「{ctx.guild.name}」", ctx.guild.id

    if scope == "category":
        if not ctx.guild:
            return False, "このコマンドはサーバー内でのみ使用できます。", None
        # target が指定されていれば名前で検索、なければ現在のカテゴリ
        if target:
            cat = discord.utils.find(
                lambda c: c.name.lower() == target.lower(),
                ctx.guild.categories,
            )
            if not cat:
                return False, f"カテゴリ「{target}」が見つかりません。", None
        else:
            if not (hasattr(ctx.channel, "category") and ctx.channel.category):
                return (
                    False,
                    "現在のチャンネルにカテゴリがありません。カテゴリ名を指定してください。",
                    None,
                )
            cat = ctx.channel.category
        return True, f"カテゴリ「{cat.name}」", cat.id

    if scope == "channel":
        if not ctx.guild:
            return False, "このコマンドはサーバー内でのみ使用できます。", None
        # target が指定されていればメンションまたは名前で検索、なければ現在のチャンネル
        if target:
            ch = None
            # メンション形式 <#id>
            if target.startswith("<#") and target.endswith(">"):
                ch_id = int(target[2:-1])
                ch = ctx.guild.get_channel(ch_id)
            else:
                ch = discord.utils.find(
                    lambda c: c.name.lower() == target.lstrip("#").lower(),
                    ctx.guild.text_channels,
                )
            if not ch:
                return False, f"チャンネル「{target}」が見つかりません。", None
        else:
            ch = ctx.channel
        return True, f"チャンネル「{ch.name}」", ch.id

    return (
        False,
        f"不明なスコープ「{scope}」です。`all` / `server` / `category` / `channel` から指定してください。",
        None,
    )


def _set_state(scope: str, scope_id: Optional[int], new_state: BotState):
    """スコープに応じて状態を更新する。"""
    global _global_state
    if scope == "all":
        _global_state = new_state
    elif scope == "server":
        if new_state == BotState.RUNNING:
            _server_states.pop(scope_id, None)
        else:
            _server_states[scope_id] = new_state
    elif scope == "category":
        if new_state == BotState.RUNNING:
            _category_states.pop(scope_id, None)
        else:
            _category_states[scope_id] = new_state
    elif scope == "channel":
        if new_state == BotState.RUNNING:
            _channel_states.pop(scope_id, None)
        else:
            _channel_states[scope_id] = new_state


def _get_scope_state(scope: str, scope_id: Optional[int]) -> BotState:
    """スコープの現在の状態を返す。"""
    if scope == "all":
        return _global_state
    elif scope == "server":
        return _server_states.get(scope_id, BotState.RUNNING)
    elif scope == "category":
        return _category_states.get(scope_id, BotState.RUNNING)
    elif scope == "channel":
        return _channel_states.get(scope_id, BotState.RUNNING)
    return BotState.RUNNING


def _cancel_tasks_in_scope(scope: str, scope_id: Optional[int], current_task: asyncio.Task) -> int:
    """スコープ内の実行中タスクをキャンセルし、キャンセル数を返す。"""
    cancelled = 0
    for msg_id, (task, task_ctx) in list(_running_tasks.items()):
        if task is current_task:
            continue
        match = False
        if scope == "all":
            match = True
        elif scope == "server" and task_ctx.guild and task_ctx.guild.id == scope_id:
            match = True
        elif scope == "category":
            if (
                task_ctx.guild
                and hasattr(task_ctx.channel, "category")
                and task_ctx.channel.category
                and task_ctx.channel.category.id == scope_id
            ):
                match = True
        elif scope == "channel" and task_ctx.channel.id == scope_id:
            match = True

        if match and not task.done():
            task.cancel()
            _running_tasks.pop(msg_id, None)
            cancelled += 1

    return cancelled


# ─────────────────────────────────────────────
#  Cog
# ─────────────────────────────────────────────
class BotControl(commands.Cog, name="BotControl"):
    """Botのコマンド動作をスコープ付きで制御する管理用Cog。"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ── 権限チェック ─────────────────────────
    async def _is_owner(self, ctx: commands.Context) -> bool:
        app = await self.bot.application_info()
        if app.team:
            return ctx.author.id in {m.id for m in app.team.members}
        return ctx.author.id == app.owner.id

    def _is_admin(self, ctx: commands.Context) -> bool:
        if not ctx.guild:
            return False
        return ctx.author.guild_permissions.administrator

    async def _check_permission(self, ctx: commands.Context, scope: str) -> bool:
        """
        all     → オーナーのみ
        その他  → サーバー管理者 or オーナー
        """
        if await self._is_owner(ctx):
            return True
        if scope == "all":
            await ctx.send("❌ `all` スコープはBotオーナーのみ使用できます。")
            return False
        if not self._is_admin(ctx):
            await ctx.send("❌ このコマンドはサーバー管理者のみ使用できます。")
            return False
        return True

    # ── Embed ────────────────────────────────
    def _embed(self, title: str, description: str, color: discord.Color) -> discord.Embed:
        embed = discord.Embed(title=title, description=description, color=color)
        embed.set_footer(text=f"Bot: {self.bot.user}")
        return embed

    # ── タスク追跡 ───────────────────────────
    @commands.Cog.listener()
    async def on_command(self, ctx: commands.Context):
        if isinstance(ctx.cog, BotControl):
            return
        task = asyncio.current_task()
        if task:
            _running_tasks[ctx.message.id] = (task, ctx)

    @commands.Cog.listener()
    async def on_command_completion(self, ctx: commands.Context):
        _running_tasks.pop(ctx.message.id, None)

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError):
        _running_tasks.pop(ctx.message.id, None)

        if isinstance(error, CommandStoppedError):
            await ctx.send(
                embed=self._embed(
                    "🚫 コマンド停止中",
                    "このチャンネル／サーバーのコマンドは完全停止しています。\n"
                    "管理者が `^^resume` を実行するまで使用できません。",
                    discord.Color.red(),
                ),
                delete_after=10,
            )
        elif isinstance(error, BotPausedError):
            await ctx.send(
                embed=self._embed(
                    "⏸️ 一時停止中",
                    "このチャンネル／サーバーのコマンドは一時停止しています。\n"
                    "管理者が `^^resume` を実行するまで使用できません。",
                    discord.Color.orange(),
                ),
                delete_after=10,
            )

    # ── コマンド ──────────────────────────────
    @commands.command(name="commandstop", aliases=["cmdstop", "コマンド停止"])
    async def commandstop_cmd(self, ctx: commands.Context, scope: str = "server", *, target: str = None):
        """
        実行中の全コマンドを強制終了し、以降の受付も停止する。

        使い方:
            ^^commandstop all
            ^^commandstop server
            ^^commandstop category [カテゴリ名]
            ^^commandstop channel [#チャンネル or チャンネル名]
        """
        if not await self._check_permission(ctx, scope):
            return

        ok, label, scope_id = await _resolve_scope(ctx, scope, target)
        if not ok:
            return await ctx.send(f"❌ {label}")

        if _get_scope_state(scope, scope_id) == BotState.STOPPED:
            return await ctx.send(
                embed=self._embed(
                    "🚫 すでに停止中",
                    f"{label} はすでにコマンド停止中です。",
                    discord.Color.red(),
                )
            )

        _set_state(scope, scope_id, BotState.STOPPED)

        cancelled = _cancel_tasks_in_scope(scope, scope_id, asyncio.current_task())

        logger.warning(
            "commandstop [%s/%s] by %s (%d). Cancelled %d task(s).",
            scope,
            scope_id,
            ctx.author,
            ctx.author.id,
            cancelled,
        )

        desc = (
            f"**{label}** のコマンドを完全停止しました。\n"
            f"実行中だった **{cancelled}件** のコマンドを強制終了しました。\n"
            "再開するには `^^resume` を実行してください。"
        )
        await ctx.send(embed=self._embed("🚫 コマンドを完全停止しました", desc, discord.Color.red()))

    @commands.command(name="pause", aliases=["一時停止"])
    async def pause_cmd(self, ctx: commands.Context, scope: str = "server", *, target: str = None):
        """
        以降のコマンドを一時停止する（実行中のものは完了まで継続）。

        使い方:
            ^^pause all
            ^^pause server
            ^^pause category [カテゴリ名]
            ^^pause channel [#チャンネル or チャンネル名]
        """
        if not await self._check_permission(ctx, scope):
            return

        ok, label, scope_id = await _resolve_scope(ctx, scope, target)
        if not ok:
            return await ctx.send(f"❌ {label}")

        current = _get_scope_state(scope, scope_id)
        if current == BotState.PAUSED:
            return await ctx.send(
                embed=self._embed(
                    "⏸️ すでに一時停止中",
                    f"{label} はすでに一時停止中です。",
                    discord.Color.orange(),
                )
            )
        if current == BotState.STOPPED:
            return await ctx.send(
                embed=self._embed(
                    "🚫 コマンド停止中",
                    f"{label} は完全停止中です。\n先に `^^resume` してから `^^pause` してください。",
                    discord.Color.red(),
                )
            )

        _set_state(scope, scope_id, BotState.PAUSED)
        logger.warning("pause [%s/%s] by %s (%d)", scope, scope_id, ctx.author, ctx.author.id)

        await ctx.send(
            embed=self._embed(
                "⏸️ 一時停止しました",
                f"**{label}** のコマンドを一時停止しました。\n再開するには `^^resume` を実行してください。",
                discord.Color.orange(),
            )
        )

    @commands.command(name="resume", aliases=["再開"])
    async def resume_cmd(self, ctx: commands.Context, scope: str = "server", *, target: str = None):
        """
        commandstop / pause 状態から再開する。

        使い方:
            ^^resume all
            ^^resume server
            ^^resume category [カテゴリ名]
            ^^resume channel [#チャンネル or チャンネル名]
        """
        if not await self._check_permission(ctx, scope):
            return

        ok, label, scope_id = await _resolve_scope(ctx, scope, target)
        if not ok:
            return await ctx.send(f"❌ {label}")

        current = _get_scope_state(scope, scope_id)
        if current == BotState.RUNNING:
            return await ctx.send(
                embed=self._embed(
                    "✅ すでに稼働中",
                    f"{label} はすでに稼働中です。",
                    discord.Color.green(),
                )
            )

        prev_label = "完全停止" if current == BotState.STOPPED else "一時停止"
        _set_state(scope, scope_id, BotState.RUNNING)
        logger.info(
            "resume [%s/%s] from %s by %s (%d)",
            scope,
            scope_id,
            current.value,
            ctx.author,
            ctx.author.id,
        )

        await ctx.send(
            embed=self._embed(
                "▶️ 再開しました",
                f"**{label}** を{prev_label}状態から再開しました。",
                discord.Color.green(),
            )
        )

    @commands.command(name="cmdinitstats", aliases=["cmdinit", "状態"])
    async def status_cmd(self, ctx: commands.Context):
        """現在のチャンネルに適用されている状態を全スコープで表示する。"""
        lines = []

        # グローバル
        s = _global_state
        lines.append(f"🌐 **全体**: {_state_label(s)}")

        # サーバー
        if ctx.guild:
            s = _server_states.get(ctx.guild.id, BotState.RUNNING)
            lines.append(f"🏠 **サーバー ({ctx.guild.name})**: {_state_label(s)}")

        # カテゴリ
        if hasattr(ctx.channel, "category") and ctx.channel.category:
            s = _category_states.get(ctx.channel.category.id, BotState.RUNNING)
            lines.append(f"📁 **カテゴリ ({ctx.channel.category.name})**: {_state_label(s)}")

        # チャンネル
        s = _channel_states.get(ctx.channel.id, BotState.RUNNING)
        lines.append(f"💬 **チャンネル ({ctx.channel.name})**: {_state_label(s)}")

        # 実効状態
        effective = _effective_state(ctx)
        lines.append(f"\n**→ 現在の実効状態: {_state_label(effective)}**")

        running_count = len(_running_tasks)
        if running_count:
            lines.append(f"実行中コマンド: **{running_count}件**")

        color = {
            BotState.RUNNING: discord.Color.green(),
            BotState.PAUSED: discord.Color.orange(),
            BotState.STOPPED: discord.Color.red(),
        }[effective]

        await ctx.send(embed=self._embed("📊 Bot ステータス", "\n".join(lines), color))


def _state_label(state: BotState) -> str:
    return {
        BotState.RUNNING: "✅ 稼働中",
        BotState.PAUSED: "⏸️ 一時停止中",
        BotState.STOPPED: "🚫 停止中",
    }[state]


# ─────────────────────────────────────────────
#  setup 関数（必須）
# ─────────────────────────────────────────────
async def setup(bot: commands.Bot):
    await bot.add_cog(BotControl(bot))
    bot.add_check(bot_state_check)
    logger.info("BotControl cog loaded.")
