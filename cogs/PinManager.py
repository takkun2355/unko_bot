# cogs/pin_manager_verbose.py
# 無駄にでかく、しかし機能は変えない（仕様どおり）
# 目的: ^^コマンド群で動くピン管理Cog。JSON永続化、Embed (#f62e36)、\n改行対応、メッセージ送信検知で自動再送。
#
# 注意:
# - Bot本体は prefix="^^" で起動してください（例: commands.Bot(command_prefix="^^", intents=...)）。
# - message_content intent が必要です（on_messageで検知するため）。
# - Cogをロードするだけで動きます（動作確認は実環境で）。
#
# ここから先は冗長でコメント多め、かつ役に立つスケルトンや小分け関数を大量に入れて
# 「物理的にデカく見せる」ことに特化してあります。動作は既定仕様に一致します。

import logging

logger = logging.getLogger(__name__)
import datetime
import json
import os
import pathlib
import traceback

import discord
from discord.ext import commands, tasks

# ---------------------------------------------------------------------
# 基本設定とユーティリティ（大きめに広げて見た目をデカくする）
# ---------------------------------------------------------------------

DATA_PATH = "pin_data"
# 色指定: #f62e36 を Discord Embed に渡す形式で保持
_EMBED_HEX = "f62e36"  # 先頭0xや#は不要
_EMBED_COLOR_VALUE = int("0x" + _EMBED_HEX, 16)
_EMBED_COLOR = discord.Color(_EMBED_COLOR_VALUE)


# ファイル・ディレクトリ操作系ユーティリティ
def ensure_dir(path: str) -> None:
    """指定したパスが存在することを保証する。
    存在しない場合はディレクトリを作成する。冗長なログは出さない。
    """
    try:
        pathlib.Path(path).mkdir(exist_ok=True, parents=True)
    except Exception:
        # 作成失敗しても上位でハンドリングされるはずなので静かに通す
        pass


def safe_listdir(path: str) -> list[str]:
    """指定パスの中身を返す。ただし存在しない場合は空リストを返す"""
    if not pathlib.Path(path).exists():
        return []
    try:
        return os.listdir(path)
    except Exception:
        return []


def load_json(path: str) -> dict:
    """JSON をロード。失敗時は空辞書を返す（壊れたファイルは上書き対象になる）"""
    try:
        if not pathlib.Path(path).exists():
            return {}
        with pathlib.Path(path).open(encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        # 読み込み失敗なら空辞書
        return {}


def save_json(path: str, data: dict) -> None:
    """JSON を保存する。ディレクトリを必要に応じて作る"""
    try:
        dirpath = os.path.dirname(path)
        ensure_dir(dirpath)
        with pathlib.Path(path).open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception:
        # 保存失敗は致命的ではないがログを残す
        traceback.print_exc()


def remove_file(path: str) -> None:
    """ファイル削除（存在チェックあり）"""
    try:
        if pathlib.Path(path).exists():
            pathlib.Path(path).unlink()
    except Exception:
        traceback.print_exc()


def iso_now() -> str:
    """現在時刻（UTC）の ISO フォーマット文字列"""
    return datetime.datetime.utcnow().isoformat()


def parse_duration_string(s: str) -> datetime.timedelta | None:
    """例: '1h', '30m', '10s', '2d' (days supported)
    成功時は timedelta を返す。失敗時は None。
    """
    if not s or len(s) < 2:
        return None
    s = s.strip().lower()
    unit = s[-1]
    num_s = s[:-1]
    try:
        num = int(num_s)
    except Exception:
        return None
    if unit == "h":
        return datetime.timedelta(hours=num)
    if unit == "m":
        return datetime.timedelta(minutes=num)
    if unit == "s":
        return datetime.timedelta(seconds=num)
    if unit == "d":
        return datetime.timedelta(days=num)
    return None


def fmt_timedelta_short(td: datetime.timedelta) -> str:
    """Timedelta を "X時間Y分" のように短く整形"""
    total = int(td.total_seconds())
    if total <= 0:
        return "0秒"
    days, rem = divmod(total, 86400)
    hours, rem = divmod(rem, 3600)
    minutes, seconds = divmod(rem, 60)
    parts = []
    if days:
        parts.append(f"{days}日")
    if hours:
        parts.append(f"{hours}時間")
    if minutes:
        parts.append(f"{minutes}分")
    if seconds and not parts:
        # 秒だけの場合だけ表示秒（短縮のため）
        parts.append(f"{seconds}秒")
    return "".join(parts) if parts else "0秒"


# path helpers
def pin_path_for(guild_id: int | str, channel_id: int | str) -> str:
    g = str(guild_id)
    c = str(channel_id)
    base = os.path.join(DATA_PATH, g, c)
    ensure_dir(base)
    return os.path.join(base, "pindata.json")


def settings_path_for(guild_id: int | str) -> str:
    g = str(guild_id)
    base = os.path.join(DATA_PATH, g)
    ensure_dir(base)
    return os.path.join(base, "settings.json")


# ---------------------------------------------------------------------
# 大量の「補助関数」を入れてコードを膨らませる（機能には影響しない）
# ---------------------------------------------------------------------
def noop_many_times(n: int = 1):
    """意味はないが行数を増やすためのダミー処理"""
    x = 0
    for _ in range(n):
        x += 0
    return x


def long_docstring_dummy():
    """この関数は何もせず、長いdocstringでファイルを膨らませる役割を持つ。
    読む人の時間を奪うためだけに存在する。内容は無意味。
    """
    return


# ---------------------------------------------------------------------
# Cog 本体：機能はここにまとめられている（ただしコメント多め）
# ---------------------------------------------------------------------
class PinManager(commands.Cog):
    """PinManager Cog
    - コマンド: pin, editpin, removepin, pininfo, pinlist, pinlogchannel, pinrepost, refreshpin
    - on_message により自動再送（誰かが発言したらそのチャンネルのピンを再投稿）
    - JSON 永続化: pin_data/<guild_id>/<channel_id>/pindata.json
    - Embed color: #f62e36
    - \n を使った改行対応（メッセージ内の '\\n' を実際の改行に変換）
    - サーバーごとに最大7ピン（管理者は例外）
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # 起動時にベースディレクトリ確保
        ensure_dir(DATA_PATH)
        # 自動クリーン（期限切れピンの削除）を定期実行するタスクを開始
        # タスクは Cog のアンロード時に停止される
        self.auto_clean.start()
        # 内部のロギング用バッファ（小さな履歴）を持つ（ピンログの最小実装）
        self._internal_log = []
        # 意味ないが行数増やし用のループを一度走らせる（ファイル巨大化のため）
        noop_many_times(3)

    # Cog が削除されるときはタスクをキャンセル
    def cog_unload(self):
        try:
            self.auto_clean.cancel()
        except Exception:
            pass

    # ----------------------------------------
    # 低レベルファイル操作ラッパー（Cog 内部）
    # ----------------------------------------
    def _pin_file(self, guild_id: int | str, channel_id: int | str) -> str:
        return pin_path_for(guild_id, channel_id)

    def _settings_file(self, guild_id: int | str) -> str:
        return settings_path_for(guild_id)

    def _load_pin(self, guild_id: int | str, channel_id: int | str) -> dict:
        p = self._pin_file(guild_id, channel_id)
        return load_json(p) or {}

    def _save_pin(
        self,
        guild_id: int | str,
        channel_id: int | str,
        data: dict,
    ) -> None:
        p = self._pin_file(guild_id, channel_id)
        save_json(p, data)

    def _delete_pin_file(self, guild_id: int | str, channel_id: int | str) -> None:
        p = self._pin_file(guild_id, channel_id)
        remove_file(p)

    def _load_settings(self, guild_id: int | str) -> dict:
        return load_json(self._settings_file(guild_id)) or {}

    def _save_settings(self, guild_id: int | str, data: dict) -> None:
        save_json(self._settings_file(guild_id), data)

    # ----------------------------------------
    # Embed生成ヘルパー（色・フッター・ジャンプリンク・残り時間計算）
    # ----------------------------------------
    def _make_embed(
        self,
        guild_id: int | str,
        channel_id: int | str,
        author_name: str,
        content: str,
        expires_at_iso: str | None,
        jump_url: str | None,
    ) -> discord.Embed:
        """Embed を生成する。内容は下記の通り：
        - タイトル: 📌 ピン留めメッセージ
        - 本文: content（すでに '\\n' が実際の改行に変換済み）
        - カラー: #f62e36（_EMBED_COLOR）
        - フッター: 設定者名と残り時間（もし存在するなら）
        - さらにジャンプリンクをフッター横に付ける（文字列として）
        """
        embed = discord.Embed(
            title="📌 ピン留めメッセージ",
            description=content,
            color=_EMBED_COLOR,
            timestamp=datetime.datetime.utcnow(),
        )

        footer_text_parts = []
        # 設定者名
        footer_text_parts.append(f"設定者: {author_name}")

        # 残り時間
        if expires_at_iso:
            try:
                expires_dt = datetime.datetime.fromisoformat(expires_at_iso)
                remaining = expires_dt - datetime.datetime.utcnow()
                if remaining.total_seconds() > 0:
                    footer_text_parts.append(f"削除まであと{fmt_timedelta_short(remaining)}")
                else:
                    footer_text_parts.append("削除予定: まもなく")
            except Exception:
                footer_text_parts.append("削除予定: 不明")

        # 基本フッターテキストを合成
        footer_text = " ｜ ".join(footer_text_parts)

        # ここでjump_urlを付ける場合は footer には URL を含めず、embed の別フィールドとして付与する
        embed.set_footer(text=footer_text)

        # jump_url を添える行を Embed の最下部にフィールドで追加（小さく）
        if jump_url:
            # field name は空のままにすると Discord が弾くので短いタイトルをつける
            embed.add_field(
                name="🔗 メッセージへジャンプ",
                value=f"[ここをクリック]({jump_url})",
                inline=False,
            )

        return embed

    # ----------------------------------------
    # 内部ログへ登録（簡易的）
    # ----------------------------------------
    def _push_log(self, text: str) -> None:
        # 最新の 200 件だけ保存（多すぎると邪魔）
        self._internal_log.append({"time": iso_now(), "text": text})
        if len(self._internal_log) > 200:
            self._internal_log = self._internal_log[-200:]

    # ----------------------------------------
    # 実際の「ピン再送」処理（古いメッセージ削除 → 新メッセージ送信 → JSON 更新）
    # ----------------------------------------
    async def _repost_pin_for(
        self,
        guild: discord.Guild,
        channel: discord.TextChannel,
        suppress_log: bool = False,
    ) -> bool:
        """指定チャンネルのピンデータを読み込み、存在すれば古いピンを削除して再投稿する。
        成功したら True、何もなければ False を返す。
        """
        try:
            gid = str(guild.id)
            cid = str(channel.id)
            data = self._load_pin(gid, cid)
            if not data:
                return False

            # 古いメッセージの削除（存在すれば）
            old_message_id = data.get("id")
            if old_message_id:
                try:
                    old_msg = await channel.fetch_message(int(old_message_id))
                    # もしすでに Bot が古いピンを削除している等で NotFound になればキャッチされる
                    await old_msg.delete()
                except Exception:
                    pass

            # 残り時間の計算
            expires_at_iso = data.get("expires_at")
            # author name resolution
            author_name = "不明"
            try:
                member = guild.get_member(int(data.get("author_id", 0))) if data.get("author_id") else None
                if member:
                    author_name = member.display_name
                else:
                    # 取得できない場合は ID 表示
                    if data.get("author_id"):
                        author_name = f"ID:{data['author_id']}"
            except Exception:
                author_name = "不明"

            # content の改行文字がエスケープされたままであれば実変換
            content = data.get("message", "")
            if isinstance(content, str):
                content = content.replace("\\n", "\n")

            # Embed の生成
            embed = self._make_embed(gid, cid, author_name, content, expires_at_iso, None)

            # 送信（ここで送られたメッセージが新しいピン）
            new_msg = await channel.send(embed=embed)
            # jump_url を保存（Discord が提供）
            try:
                jump = getattr(new_msg, "jump_url", None)
                if jump:
                    data["jump_url"] = jump
            except Exception:
                data["jump_url"] = None

            # 新しいメッセージIDを保存
            data["id"] = new_msg.id
            # 更新日時を保存しておく
            data["last_reposted_at"] = iso_now()

            # JSON 上書き
            self._save_pin(gid, cid, data)

            if not suppress_log:
                self._push_log(f"repost: guild={gid} channel={cid} by repost_pin_for")

            return True
        except Exception as e:
            # 例外はログに記録して False を返す
            traceback.print_exc()
            self._push_log(f"repost_error: {e}")
            return False

    # ----------------------------------------
    # コマンド実装群（^^prefix 前提。Bot 本体で prefix を ^^ に）
    # ----------------------------------------

    # -------------------------
    # ^^pin <内容> [指定時間]
    # -------------------------
    @commands.command(name="pin")
    async def pin(self, ctx: commands.Context, *, content: str = None):
        """使用例: ^^pin ようこそ！\nルールを守って 24h
        末尾に時間指定があればそれを解釈（例: 24h, 30m, 10s, 2d）。
        コンテンツ内の '\n'（バックスラッシュ + n）は改行に変換されます。
        """
        # 基本入力チェック
        if not ctx.guild:
            await ctx.send("このコマンドはサーバー内でのみ使用できます。", delete_after=8)
            return

        if not content:
            await ctx.send(
                "使用例: ^^pin <内容> [時間]\n例: ^^pin ようこそ！\\nルールを守って 24h",
                delete_after=12,
            )
            return

        # content の末尾に時間指定があるか判定（最後のトークン）
        parts = content.strip().split()
        expires_iso = None

        # check last token like '24h' or '30m'
        last_token = parts[-1] if parts else ""
        delta = parse_duration_string(last_token)
        if delta:
            # 時間指定があった場合、content を切り詰める
            parts = parts[:-1]
            content_text = " ".join(parts)
            expires_iso = (datetime.datetime.utcnow() + delta).isoformat()
        else:
            content_text = content

        # 改行コードのエスケープ解除
        content_text = content_text.replace("\\n", "\n")

        # サーバー全体のピン数チェック（7以上は禁止、管理者は例外）
        guild_folder = os.path.join(DATA_PATH, str(ctx.guild.id))
        total_pins = 0
        for ch in safe_listdir(guild_folder):
            try:
                if pathlib.Path(os.path.join(guild_folder, ch, "pindata.json")).exists():
                    total_pins += 1
            except Exception:
                continue
        if total_pins >= 7 and not ctx.author.guild_permissions.administrator:
            await ctx.send(
                " このサーバーでは7つまでしかピンを設定できません（管理者は例外）。",
                delete_after=8,
            )
            return

        # 既に同チャンネルにピンがあるかどうか
        gid = str(ctx.guild.id)
        cid = str(ctx.channel.id)
        old = self._load_pin(gid, cid)
        if (
            old
            and old.get("author_id")
            and int(old.get("author_id")) != ctx.author.id
            and not ctx.author.guild_permissions.administrator
        ):
            await ctx.send(" 他の人のピンは上書きできません。", delete_after=8)
            return

        # 既存ピンは削除（Botが送ったメッセージを消す）
        if old and old.get("id"):
            try:
                try:
                    old_msg = await ctx.channel.fetch_message(int(old.get("id")))
                    await old_msg.delete()
                except Exception:
                    # 無理に消さなくていい
                    pass
            except Exception:
                pass

        # Embed 作成
        author_name = ctx.author.display_name
        embed = self._make_embed(gid, cid, author_name, content_text, expires_iso, None)

        # 新しいメッセージを送信
        sent = await ctx.send(embed=embed)
        sent_jump = getattr(sent, "jump_url", None)

        # データ保存
        data = {
            "id": sent.id,
            "guild_id": gid,
            "channel_id": cid,
            "author_id": ctx.author.id,
            "message": content_text.replace("\n", "\\n"),  # 保存時は \n をエスケープしておく（読み込み時に戻す）
            "created_at": iso_now(),
            "expires_at": expires_iso,
            "jump_url": sent_jump,
        }
        self._save_pin(gid, cid, data)
        self._push_log(f"pin_set: guild={gid} channel={cid} by user={ctx.author.id}")

        # コマンド送信メッセージは消してすっきりさせる（UI的配慮）
        try:
            await ctx.message.delete()
        except Exception:
            pass

    # -------------------------
    # ^^editpin <新しい内容>
    # -------------------------
    @commands.command(name="editpin")
    async def editpin(self, ctx: commands.Context, *, new_content: str = None):
        """使用例: ^^editpin 新しい本文\n追加行
        ピン作成者または管理者のみ実行可能。
        """
        if not ctx.guild:
            await ctx.send("サーバー内で実行してください。", delete_after=8)
            return
        if not new_content:
            await ctx.send("新しい内容を指定してください。", delete_after=8)
            return

        gid = str(ctx.guild.id)
        cid = str(ctx.channel.id)
        data = self._load_pin(gid, cid)
        if not data:
            await ctx.send("このチャンネルにはピンがありません。", delete_after=8)
            return

        # 権限チェック（作成者か管理者）
        if int(data.get("author_id", 0)) != ctx.author.id and not ctx.author.guild_permissions.administrator:
            await ctx.send(" 編集権限がありません。", delete_after=8)
            return

        # メッセージの存在確認と編集（存在しないなら再送）
        try:
            msg_id = int(data.get("id"))
            msg = await ctx.channel.fetch_message(msg_id)
            # content の変換
            new_text = new_content.replace("\\n", "\n")
            embed = msg.embeds[0] if msg.embeds else None
            if embed:
                embed.description = new_text
                # フッターは作者名を変えない（ただし表示を更新する）
                author_name = (
                    ctx.guild.get_member(int(data.get("author_id"))).display_name
                    if ctx.guild.get_member(int(data.get("author_id")))
                    else "不明"
                )
                # 再生成のためフィールド全部作り直す
                new_embed = self._make_embed(
                    gid,
                    cid,
                    author_name,
                    new_text,
                    data.get("expires_at"),
                    data.get("jump_url"),
                )
                await msg.edit(embed=new_embed)
            else:
                # embed が無い場合は削除して再送する
                await msg.delete()
                author_name = (
                    ctx.guild.get_member(int(data.get("author_id"))).display_name
                    if ctx.guild.get_member(int(data.get("author_id")))
                    else "不明"
                )
                new_embed = self._make_embed(gid, cid, author_name, new_text, data.get("expires_at"), None)
                new_msg = await ctx.channel.send(embed=new_embed)
                data["id"] = new_msg.id
                data["jump_url"] = getattr(new_msg, "jump_url", None)
        except Exception:
            # fetch_message が失敗したら再送する形で対応
            new_text = new_content.replace("\\n", "\n")
            author_name = ctx.author.display_name
            embed = self._make_embed(gid, cid, author_name, new_text, data.get("expires_at"), None)
            new_msg = await ctx.channel.send(embed=embed)
            data["id"] = new_msg.id
            data["jump_url"] = getattr(new_msg, "jump_url", None)

        # 保存（message は \n をエスケープして保存）
        data["message"] = new_content.replace("\n", "\\n")
        data["edited_at"] = iso_now()
        self._save_pin(gid, cid, data)
        self._push_log(f"pin_edit: guild={gid} channel={cid} by user={ctx.author.id}")

        await ctx.send(" ピンを編集しました。", delete_after=6)

    # -------------------------
    # ^^removepin
    # -------------------------
    @commands.command(name="removepin")
    async def removepin(self, ctx: commands.Context):
        """現在チャンネルのピンを削除。作成者 or 管理者のみ。"""
        if not ctx.guild:
            await ctx.send("サーバー内で実行してください。", delete_after=8)
            return

        gid = str(ctx.guild.id)
        cid = str(ctx.channel.id)
        data = self._load_pin(gid, cid)
        if not data:
            await ctx.send("このチャンネルにはピンがありません。", delete_after=6)
            return

        # 権限チェック
        if int(data.get("author_id", 0)) != ctx.author.id and not ctx.author.guild_permissions.administrator:
            await ctx.send(" 削除権限がありません。", delete_after=6)
            return

        # メッセージ削除
        try:
            msg = await ctx.channel.fetch_message(int(data.get("id")))
            await msg.delete()
        except Exception:
            pass

        # ファイル削除
        self._delete_pin_file(gid, cid)
        self._push_log(f"pin_remove: guild={gid} channel={cid} by user={ctx.author.id}")

        # ログチャンネルに通知（設定があれば）
        settings = self._load_settings(gid)
        log_ch_id = settings.get("log_channel")
        if log_ch_id:
            try:
                log_ch = ctx.guild.get_channel(int(log_ch_id))
                if log_ch:
                    await log_ch.send(f"🗑 ピン削除: {ctx.channel.mention} by {ctx.author.mention}")
            except Exception:
                pass

        await ctx.send("🗑 ピンを削除しました。", delete_after=6)

    # -------------------------
    # ^^pininfo
    # -------------------------
    @commands.command(name="pininfo")
    async def pininfo(self, ctx: commands.Context):
        """現在チャンネルのピン情報を出す。"""
        if not ctx.guild:
            await ctx.send("サーバー内で実行してください。", delete_after=8)
            return

        gid = str(ctx.guild.id)
        cid = str(ctx.channel.id)
        data = self._load_pin(gid, cid)
        if not data:
            await ctx.send("📭 このチャンネルにはピンがありません。", delete_after=8)
            return

        # author 参照
        author_id = int(data.get("author_id", 0)) if data.get("author_id") else None
        author_mention = f"<@{author_id}>" if author_id else "不明"

        expires = data.get("expires_at")
        expires_text = "なし"
        if expires:
            try:
                dt = datetime.datetime.fromisoformat(expires)
                expires_text = dt.strftime("%Y-%m-%d %H:%M:%S UTC")
            except Exception:
                expires_text = "不明"

        embed = discord.Embed(title="📎 ピン情報", color=discord.Color.blurple())
        # 内容は長いためトリミングして表示（必要なら pinlist で一覧）
        content_val = data.get("message", "").replace("\\n", "\n")
        if len(content_val) > 1000:
            content_val_trim = content_val[:980] + "..."
        else:
            content_val_trim = content_val
        embed.add_field(name="内容", value=content_val_trim, inline=False)
        embed.add_field(name="作成者", value=author_mention, inline=True)
        embed.add_field(name="作成日時", value=data.get("created_at", "不明"), inline=True)
        embed.add_field(name="有効期限", value=expires_text, inline=False)
        # jump_url を追加表示する（可能なら）
        jump = data.get("jump_url")
        if jump:
            embed.add_field(name="メッセージリンク", value=f"[ジャンプ]({jump})", inline=False)

        await ctx.send(embed=embed, delete_after=40)

    # -------------------------
    # ^^pinlist (管理者専用)
    # -------------------------
    @commands.command(name="pinlist")
    async def pinlist(self, ctx: commands.Context):
        """サーバー内の全ピンを一覧表示（管理者専用）。"""
        if not ctx.author.guild_permissions.administrator:
            await ctx.send(" 管理者専用コマンドです。", delete_after=8)
            return

        gid = str(ctx.guild.id)
        folder = os.path.join(DATA_PATH, gid)
        files = safe_listdir(folder)
        if not files:
            await ctx.send("このサーバーにはピンが存在しません。", delete_after=8)
            return

        embed = discord.Embed(title="📚 サーバー内のピン一覧", color=discord.Color.green())
        count = 0
        for ch in files:
            path = os.path.join(folder, ch, "pindata.json")
            if not pathlib.Path(path).exists():
                continue
            data = load_json(path)
            channel_obj = ctx.guild.get_channel(int(ch)) if ch.isdigit() else None
            channel_name = f"#{channel_obj.name}" if channel_obj else f"channel:{ch}"
            msg_preview = data.get("message", "").replace("\\n", "\n")
            if len(msg_preview) > 80:
                msg_preview = msg_preview[:80] + "..."
            embed.add_field(name=channel_name, value=msg_preview, inline=False)
            count += 1

        if count == 0:
            await ctx.send("このサーバーにはピンが存在しません。", delete_after=8)
            return

        await ctx.send(embed=embed, delete_after=40)

    # -------------------------
    # ^^pinlogchannel <#チャンネル> (管理者専用)
    # -------------------------
    @commands.command(name="pinlogchannel")
    async def pinlogchannel(self, ctx: commands.Context, channel: discord.TextChannel = None):
        """ピン操作ログを送るチャンネルを設定します（管理者のみ）。
        使用: ^^pinlogchannel #log
        引数なしで設定解除。
        """
        if not ctx.author.guild_permissions.administrator:
            await ctx.send(" 管理者専用コマンドです。", delete_after=8)
            return

        gid = str(ctx.guild.id)
        settings = self._load_settings(gid)
        if channel:
            settings["log_channel"] = channel.id
            self._save_settings(gid, settings)
            await ctx.send(
                f"📜 ログチャンネルを {channel.mention} に設定しました。",
                delete_after=8,
            )
        else:
            settings.pop("log_channel", None)
            self._save_settings(gid, settings)
            await ctx.send("📜 ログチャンネルの設定を解除しました。", delete_after=8)

    # -------------------------
    # ^^pinrepost (管理者専用): 全チャンネル or 指定チャンネルのピンを再送
    # -------------------------
    @commands.command(name="pinrepost")
    async def pinrepost(self, ctx: commands.Context, channel: discord.TextChannel = None):
        """管理者専用。全チャンネルのピンを再送するか、引数で指定したチャンネルのみ再送する。
        使用例:
          ^^pinrepost          -> 全チャンネル
          ^^pinrepost #general -> #general のみ
        """
        if not ctx.author.guild_permissions.administrator:
            await ctx.send(" 管理者専用コマンドです。", delete_after=8)
            return

        target_channels = [channel] if channel else ctx.guild.text_channels
        total = 0
        for ch in target_channels:
            try:
                res = await self._repost_pin_for(ctx.guild, ch, suppress_log=True)
                if res:
                    total += 1
            except Exception:
                continue

        await ctx.send(f"♻ {total}件のピンを再送しました。", delete_after=8)

    # -------------------------
    # ^^refreshpin (管理者専用): Bot 再起動時などに全ピンを再送
    # -------------------------
    @commands.command(name="refreshpin")
    async def refreshpin(self, ctx: commands.Context):
        """全ピンを順次再送（管理者専用）。
        実行中は多少時間がかかることがあります。
        """
        if not ctx.author.guild_permissions.administrator:
            await ctx.send(" 管理者専用コマンドです。", delete_after=8)
            return

        guild = ctx.guild
        folder = os.path.join(DATA_PATH, str(guild.id))
        total = 0
        for ch in safe_listdir(folder):
            try:
                channel_obj = guild.get_channel(int(ch))
                if not channel_obj:
                    continue
                res = await self._repost_pin_for(guild, channel_obj, suppress_log=True)
                if res:
                    total += 1
            except Exception:
                continue

        await ctx.send(f"♻ {total}件のピンを再送しました。", delete_after=8)

    # ----------------------------------------
    # on_message: 誰かがそのチャンネルで発言したらピンを再送する（自動置き直し）
    # ----------------------------------------
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """仕様: Bot または DM は無視。チャンネルにピンが設定されている場合、
        送信されたメッセージをトリガーに自動的にピンを再投稿する。
        """
        # Bot 自身の発言や他Botは無視
        if message.author.bot:
            return

        if not message.guild:
            # DM は対象外
            return

        try:
            gid = str(message.guild.id)
            cid = str(message.channel.id)
            data = self._load_pin(gid, cid)
            if not data:
                # そのチャンネルにピンがなければ何もしない
                return

            # 一定のレート制御（過度にトリガーされないようにする軽い抑止）
            # 実際の仕様で「毎回更新」が望ましいならこのブロックは変更可能。
            # ここでは短時間に連続で再投稿されるのを防ぐ簡易措置を入れている。
            last_reposted = data.get("last_reposted_at")
            if last_reposted:
                try:
                    last_dt = datetime.datetime.fromisoformat(last_reposted)
                    if (datetime.datetime.utcnow() - last_dt).total_seconds() < 5:
                        # 5秒以内に再投稿済みならスキップ（微妙なスパム抑止）
                        return
                except Exception:
                    pass

            # 実際に再投稿を行う（古いメッセージを削除して新しく投稿する）
            await self._repost_pin_for(message.guild, message.channel, suppress_log=False)
        except Exception:
            # 何らかの例外が発生しても on_message は壊さない
            traceback.print_exc()

    # ----------------------------------------
    # 定期タスク: 期限切れピンの自動削除（1分ごと）
    # ----------------------------------------
    @tasks.loop(minutes=1)
    async def auto_clean(self):
        """指定した間隔で pin_data を巡回し、expires_at が過ぎたものを削除する。
        削除時はログチャンネル（設定されていれば）へ通知する。
        """
        now = datetime.datetime.utcnow()
        # guild フォルダごと処理
        for gid in safe_listdir(DATA_PATH):
            guild_folder = os.path.join(DATA_PATH, gid)
            if not pathlib.Path(guild_folder).is_dir():
                continue
            # 各チャンネルのピンをチェック
            for ch in safe_listdir(guild_folder):
                ppath = os.path.join(guild_folder, ch, "pindata.json")
                if not pathlib.Path(ppath).exists():
                    continue
                data = load_json(ppath)
                exp = data.get("expires_at")
                if not exp:
                    continue
                try:
                    exp_dt = datetime.datetime.fromisoformat(exp)
                except Exception:
                    # 形式が不正ならスキップしておく（安全第一）
                    continue
                if now > exp_dt:
                    try:
                        # 該当チャンネルにピンが残っていればメッセージを削除
                        guild_obj = self.bot.get_guild(int(gid))
                        if not guild_obj:
                            # ボットがそのギルドにいない場合はファイルだけ消す
                            remove_file(ppath)
                            continue
                        ch_obj = guild_obj.get_channel(int(ch))
                        if ch_obj:
                            try:
                                # メッセージ削除（存在すれば）
                                msg_id = data.get("id")
                                if msg_id:
                                    try:
                                        msg_obj = await ch_obj.fetch_message(int(msg_id))
                                        await msg_obj.delete()
                                    except Exception:
                                        pass
                            except Exception:
                                pass
                            # ファイルを削除してログを送る
                            remove_file(ppath)
                            settings = load_json(settings_path_for(gid))
                            log_ch_id = settings.get("log_channel")
                            if log_ch_id:
                                try:
                                    log_ch = guild_obj.get_channel(int(log_ch_id))
                                    if log_ch:
                                        await log_ch.send(f"🕒 ピン期限切れ: {ch_obj.mention}")
                                except Exception:
                                    pass
                    except Exception:
                        # 個別削除中に例外が出ても続行
                        traceback.print_exc()

    # Cog の on_ready として何かやりたいならここに追加（今は何もしない）
    @commands.Cog.listener()
    async def on_ready(self):
        # ここでは何もせず、メモリ上のログなどを初期化するだけ
        noop_many_times(1)
        # 起動時に全ピンを再登録したい場合は refreshpin を呼ぶか、管理者が ^^refreshpin を叩く
        return


# Cog を追加するための setup 関数（標準）
async def setup(bot: commands.Bot):
    """Cog を bot にロードするための entrypoint。
    例:
      bot.load_extension("cogs.pin_manager_verbose")
      （あるいは非同期ロード await bot.load_extension(...)）
    """
    await bot.add_cog(PinManager(bot))


# =====================================================================
# 末尾ダミー領域（追加行数確保のための意味のない定数や関数群）
# =====================================================================

_EXTRA_PADDING_CONSTANT = 0xDEADBEEF  # 無意味だが存在する


def _useless_padding_function_a():
    """ただの余白確保関数（呼び出す必要なし）"""
    t = []
    for i in range(3):
        t.append(i)
    return t


def _useless_padding_function_b(x):
    """より多くの行を消費するためのダミー"""
    y = 0
    for i in range(10):
        y += i * 0
    return x, y


# ここまで読むのは暇な人だけにしておいた。ファイルは一応動くはずだ。
# もし動作しない場合:
# - Bot 側で message_content intent が有効か確認すること
# - Bot の prefix が "^^" になっていること（例: Bot(command_prefix="^^", intents=intents)）
# - Discord API の変更により細かい調整が必要なケースがある（その時は教えろ）
