from __future__ import annotations

import asyncio
import re
import shlex
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

import discord
from discord.ext import commands, tasks

JST = timezone(timedelta(hours=9))


# =========================
#  Utility
# =========================

DURATION_RE = re.compile(
    r"(?:(\d+)y)?(?:(\d+)M)?(?:(\d+)d)?(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?$"
)


def utcnow_ts() -> int:
    return int(datetime.now(timezone.utc).timestamp())


def jst_now() -> datetime:
    return datetime.now(JST)


def parse_duration(text: str) -> Optional[int]:
    """
    Parse duration strings like:
      1y2M3d4h5m6s
      1h30m
      10m
    Returns seconds or None if invalid.

    Notes:
      y = 365 days
      M = 30 days
    """
    text = text.strip()
    if not text:
        return None

    m = DURATION_RE.fullmatch(text)
    if not m:
        return None

    years, months, days, hours, minutes, seconds = (
        int(x) if x else 0 for x in m.groups()
    )
    total = (
        years * 365 * 24 * 3600
        + months * 30 * 24 * 3600
        + days * 24 * 3600
        + hours * 3600
        + minutes * 60
        + seconds
    )
    return total if total > 0 else None


def split_csv_ids(value: str) -> list[int]:
    ids: list[int] = []
    for part in re.split(r"[,\s]+", value.strip()):
        if not part:
            continue
        if part.isdigit():
            ids.append(int(part))
    return ids


def normalize_lines(text: str) -> list[str]:
    items: list[str] = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        # Allow comma-separated lines too.
        for part in re.split(r"\s*,\s*", line):
            part = part.strip()
            if part:
                items.append(part)
    # drop duplicates while preserving order
    seen = set()
    result = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def chunked(seq: list, size: int) -> list[list]:
    return [seq[i : i + size] for i in range(0, len(seq), size)]


# =========================
#  SQLite layer
# =========================

SCHEMA_SQL = """
PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;

CREATE TABLE IF NOT EXISTS polls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id INTEGER NOT NULL,
    channel_id INTEGER NOT NULL,
    message_id INTEGER NOT NULL,
    creator_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    vote_type INTEGER NOT NULL DEFAULT 0,          -- 0 = single, 1 = multi
    anonymous INTEGER NOT NULL DEFAULT 0,          -- 0 = public names allowed, 1 = hide names
    public INTEGER NOT NULL DEFAULT 1,             -- 0 = counts only, 1 = voter list allowed
    live_result INTEGER NOT NULL DEFAULT 0,        -- 0 = final only, 1 = update after votes
    max_select INTEGER NOT NULL DEFAULT 1,
    status INTEGER NOT NULL DEFAULT 0,             -- 0 = open, 1 = closed, 2 = deleted
    option_count INTEGER NOT NULL DEFAULT 0,
    created_at INTEGER NOT NULL,
    end_at INTEGER,
    role_limit TEXT,
    channel_limit TEXT
);

CREATE TABLE IF NOT EXISTS poll_options (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    poll_id INTEGER NOT NULL,
    option_name TEXT NOT NULL,
    display_order INTEGER NOT NULL,
    vote_count INTEGER NOT NULL DEFAULT 0,
    is_deleted INTEGER NOT NULL DEFAULT 0,
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL,
    FOREIGN KEY(poll_id) REFERENCES polls(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_poll_options_poll_order
ON poll_options(poll_id, display_order);

CREATE INDEX IF NOT EXISTS idx_poll_options_poll_deleted
ON poll_options(poll_id, is_deleted);

CREATE TABLE IF NOT EXISTS poll_votes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    poll_id INTEGER NOT NULL,
    option_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1,
    FOREIGN KEY(poll_id) REFERENCES polls(id) ON DELETE CASCADE,
    FOREIGN KEY(option_id) REFERENCES poll_options(id) ON DELETE CASCADE
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_poll_votes_unique_active
ON poll_votes(poll_id, user_id, option_id, is_active);

CREATE INDEX IF NOT EXISTS idx_poll_votes_poll_user
ON poll_votes(poll_id, user_id);

CREATE INDEX IF NOT EXISTS idx_poll_votes_option_active
ON poll_votes(option_id, is_active);

CREATE TABLE IF NOT EXISTS poll_permissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    poll_id INTEGER NOT NULL,
    permission_type TEXT NOT NULL,      -- owner / op / role
    target_id INTEGER,
    FOREIGN KEY(poll_id) REFERENCES polls(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_poll_permissions_poll
ON poll_permissions(poll_id, permission_type);
"""


@dataclass(slots=True)
class CreateSettings:
    vote_type: int = 0  # 0 single, 1 multi
    anonymous: int = 0  # 0 public, 1 anonymous
    public: int = 1  # 0 counts only, 1 voter list allowed
    live_result: int = 0
    max_select: int = 1
    duration_seconds: Optional[int] = None
    role_limit: list[int] | None = None
    channel_limit: list[int] | None = None

    @property
    def end_at_ts(self) -> Optional[int]:
        if self.duration_seconds is None:
            return None
        return utcnow_ts() + self.duration_seconds


class VoteStore:
    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA busy_timeout = 5000;")
        return conn

    def init_db(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.executescript(SCHEMA_SQL)

    # ---------- low-level helpers ----------

    def _fetchone(self, query: str, params: tuple = ()) -> Optional[sqlite3.Row]:
        with self._connect() as conn:
            cur = conn.execute(query, params)
            return cur.fetchone()

    def _fetchall(self, query: str, params: tuple = ()) -> list[sqlite3.Row]:
        with self._connect() as conn:
            cur = conn.execute(query, params)
            return cur.fetchall()

    def _execute(self, query: str, params: tuple = ()) -> int:
        with self._connect() as conn:
            cur = conn.execute(query, params)
            conn.commit()
            return cur.lastrowid

    # ---------- poll creation ----------

    def create_poll(
        self,
        *,
        guild_id: int,
        channel_id: int,
        message_id: int,
        creator_id: int,
        title: str,
        description: str | None,
        settings: CreateSettings,
        options: list[str],
    ) -> int:
        now = utcnow_ts()
        end_at = settings.end_at_ts
        role_limit = ",".join(map(str, settings.role_limit or [])) or None
        channel_limit = ",".join(map(str, settings.channel_limit or [])) or None

        with self._connect() as conn:
            cur = conn.execute(
                """
                INSERT INTO polls (
                    guild_id, channel_id, message_id, creator_id,
                    title, description, vote_type, anonymous, public,
                    live_result, max_select, status, option_count,
                    created_at, end_at, role_limit, channel_limit
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?, ?, ?)
                """,
                (
                    guild_id,
                    channel_id,
                    message_id,
                    creator_id,
                    title,
                    description,
                    settings.vote_type,
                    settings.anonymous,
                    settings.public,
                    settings.live_result,
                    max(1, settings.max_select),
                    len(options),
                    now,
                    end_at,
                    role_limit,
                    channel_limit,
                ),
            )
            poll_id = cur.lastrowid

            for idx, opt in enumerate(options):
                conn.execute(
                    """
                    INSERT INTO poll_options (
                        poll_id, option_name, display_order,
                        vote_count, is_deleted, created_at, updated_at
                    ) VALUES (?, ?, ?, 0, 0, ?, ?)
                    """,
                    (poll_id, opt, idx, now, now),
                )

            # Default management permission is owner only.
            conn.execute(
                """
                INSERT INTO poll_permissions (poll_id, permission_type, target_id)
                VALUES (?, 'owner', NULL)
                """,
                (poll_id,),
            )
            conn.commit()
            return int(poll_id)

    # ---------- queries ----------

    def get_poll(self, poll_id: int) -> Optional[sqlite3.Row]:
        return self._fetchone("SELECT * FROM polls WHERE id = ?", (poll_id,))

    def get_poll_by_message(self, message_id: int) -> Optional[sqlite3.Row]:
        return self._fetchone("SELECT * FROM polls WHERE message_id = ?", (message_id,))

    def get_options(
        self, poll_id: int, *, include_deleted: bool = False
    ) -> list[sqlite3.Row]:
        if include_deleted:
            return self._fetchall(
                """
                SELECT * FROM poll_options
                WHERE poll_id = ?
                ORDER BY display_order ASC, id ASC
                """,
                (poll_id,),
            )
        return self._fetchall(
            """
            SELECT * FROM poll_options
            WHERE poll_id = ? AND is_deleted = 0
            ORDER BY display_order ASC, id ASC
            """,
            (poll_id,),
        )

    def get_option(self, option_id: int) -> Optional[sqlite3.Row]:
        return self._fetchone("SELECT * FROM poll_options WHERE id = ?", (option_id,))

    def get_active_vote_option_ids(self, poll_id: int, user_id: int) -> list[int]:
        rows = self._fetchall(
            """
            SELECT option_id
            FROM poll_votes
            WHERE poll_id = ? AND user_id = ? AND is_active = 1
            ORDER BY option_id ASC
            """,
            (poll_id, user_id),
        )
        return [int(r["option_id"]) for r in rows]

    def get_voter_ids_for_option(self, option_id: int) -> list[int]:
        rows = self._fetchall(
            """
            SELECT DISTINCT user_id
            FROM poll_votes
            WHERE option_id = ? AND is_active = 1
            """,
            (option_id,),
        )
        return [int(r["user_id"]) for r in rows]

    def list_manageable_polls(
        self, guild_id: int, user: discord.Member | discord.User
    ) -> list[sqlite3.Row]:
        rows = self._fetchall(
            """
            SELECT *
            FROM polls
            WHERE guild_id = ? AND status IN (0, 1)
            ORDER BY id DESC
            """,
            (guild_id,),
        )
        result = []
        for row in rows:
            if self.can_manage_poll(user, row, guild=None):
                result.append(row)
        return result

    def list_user_polls(self, guild_id: int, creator_id: int) -> list[sqlite3.Row]:
        return self._fetchall(
            """
            SELECT *
            FROM polls
            WHERE guild_id = ? AND creator_id = ? AND status IN (0, 1, 2)
            ORDER BY id DESC
            """,
            (guild_id, creator_id),
        )

    # ---------- permissions ----------

    def get_manage_permission_rows(self, poll_id: int) -> list[sqlite3.Row]:
        return self._fetchall(
            "SELECT * FROM poll_permissions WHERE poll_id = ?",
            (poll_id,),
        )

    def can_manage_poll(
        self,
        member: discord.Member | discord.User,
        poll_row: sqlite3.Row,
        guild: Optional[discord.Guild] = None,
    ) -> bool:
        if getattr(member, "id", None) == poll_row["creator_id"]:
            return True

        if isinstance(member, discord.Member):
            if (
                member.guild_permissions.manage_guild
                or member.guild_permissions.administrator
            ):
                return True

        # Settings by permission table.
        perms = self.get_manage_permission_rows(int(poll_row["id"]))
        if not perms:
            return getattr(member, "id", None) == poll_row["creator_id"]

        if isinstance(member, discord.Member):
            member_role_ids = {r.id for r in member.roles}
        else:
            member_role_ids = set()

        for perm in perms:
            ptype = perm["permission_type"]
            target_id = perm["target_id"]
            if (
                ptype == "owner"
                and getattr(member, "id", None) == poll_row["creator_id"]
            ):
                return True
            if ptype == "op" and isinstance(member, discord.Member):
                if (
                    member.guild_permissions.manage_guild
                    or member.guild_permissions.administrator
                ):
                    return True
            if (
                ptype == "role"
                and target_id is not None
                and target_id in member_role_ids
            ):
                return True

        return False

    def can_use_poll_in_channel(
        self,
        member: discord.Member | discord.User,
        poll_row: sqlite3.Row,
        channel_id: int,
    ) -> bool:
        role_limit = poll_row["role_limit"]
        channel_limit = poll_row["channel_limit"]

        if channel_limit:
            allowed_channels = {
                int(x) for x in str(channel_limit).split(",") if x.isdigit()
            }
            if channel_id not in allowed_channels:
                return False

        if isinstance(member, discord.Member) and role_limit:
            allowed_roles = {int(x) for x in str(role_limit).split(",") if x.isdigit()}
            member_roles = {r.id for r in member.roles}
            if allowed_roles and not (allowed_roles & member_roles):
                return False

        return True

    # ---------- poll updates ----------

    def set_poll_status(self, poll_id: int, status: int) -> None:
        self._execute("UPDATE polls SET status = ? WHERE id = ?", (status, poll_id))

    def set_poll_end_at(self, poll_id: int, end_at: Optional[int]) -> None:
        self._execute("UPDATE polls SET end_at = ? WHERE id = ?", (end_at, poll_id))

    def update_poll_meta(
        self,
        poll_id: int,
        *,
        title: str,
        description: str | None,
        options: list[str],
    ) -> list[int]:
        """Replace poll metadata and reconcile options by order.

        Returns list of removed option IDs (so we can notify voters).
        """
        now = utcnow_ts()
        removed_option_ids: list[int] = []

        with self._connect() as conn:
            poll = conn.execute(
                "SELECT * FROM polls WHERE id = ?", (poll_id,)
            ).fetchone()
            if poll is None:
                return []

            conn.execute(
                "UPDATE polls SET title = ?, description = ?, option_count = ? WHERE id = ?",
                (title, description, len(options), poll_id),
            )

            old_options = conn.execute(
                """
                SELECT * FROM poll_options
                WHERE poll_id = ?
                ORDER BY display_order ASC, id ASC
                """,
                (poll_id,),
            ).fetchall()

            max_len = max(len(old_options), len(options))
            for idx in range(max_len):
                old = old_options[idx] if idx < len(old_options) else None
                new_text = options[idx] if idx < len(options) else None

                if old is not None and new_text is not None:
                    conn.execute(
                        """
                        UPDATE poll_options
                        SET option_name = ?, is_deleted = 0, updated_at = ?
                        WHERE id = ?
                        """,
                        (new_text, now, old["id"]),
                    )
                elif old is not None and new_text is None:
                    conn.execute(
                        "UPDATE poll_options SET is_deleted = 1, updated_at = ? WHERE id = ?",
                        (now, old["id"]),
                    )
                    removed_option_ids.append(int(old["id"]))
                elif old is None and new_text is not None:
                    conn.execute(
                        """
                        INSERT INTO poll_options (
                            poll_id, option_name, display_order,
                            vote_count, is_deleted, created_at, updated_at
                        ) VALUES (?, ?, ?, 0, 0, ?, ?)
                        """,
                        (poll_id, new_text, idx, now, now),
                    )

            conn.commit()
            return removed_option_ids

    def delete_poll_soft(self, poll_id: int) -> None:
        self._execute("UPDATE polls SET status = 2 WHERE id = ?", (poll_id,))

    def close_poll(self, poll_id: int) -> None:
        self._execute("UPDATE polls SET status = 1 WHERE id = ?", (poll_id,))

    def reopen_poll(self, poll_id: int, *, new_end_at: Optional[int] = None) -> None:
        self._execute(
            "UPDATE polls SET status = 0, end_at = ? WHERE id = ?",
            (new_end_at, poll_id),
        )

    # ---------- voting ----------

    def get_poll_vote_totals(self, poll_id: int) -> dict[int, int]:
        rows = self._fetchall(
            """
            SELECT option_id, COUNT(*) AS cnt
            FROM poll_votes
            WHERE poll_id = ? AND is_active = 1
            GROUP BY option_id
            """,
            (poll_id,),
        )
        return {int(r["option_id"]): int(r["cnt"]) for r in rows}

    def set_vote_state(
        self, poll_id: int, user_id: int, selected_option_ids: list[int]
    ) -> None:
        """Reconcile user's votes for a poll with the provided selected option ids."""
        now = utcnow_ts()
        selected = set(selected_option_ids)

        with self._connect() as conn:
            poll = conn.execute(
                "SELECT * FROM polls WHERE id = ?", (poll_id,)
            ).fetchone()
            if poll is None:
                return

            current_rows = conn.execute(
                """
                SELECT id, option_id, is_active
                FROM poll_votes
                WHERE poll_id = ? AND user_id = ?
                """,
                (poll_id, user_id),
            ).fetchall()

            current_active = {
                int(r["option_id"]): int(r["id"])
                for r in current_rows
                if int(r["is_active"]) == 1
            }

            # Deactivate votes not in selection
            for option_id, vote_row_id in current_active.items():
                if option_id not in selected:
                    conn.execute(
                        "UPDATE poll_votes SET is_active = 0, updated_at = ? WHERE id = ?",
                        (now, vote_row_id),
                    )
                    conn.execute(
                        "UPDATE poll_options SET vote_count = MAX(vote_count - 1, 0), updated_at = ? WHERE id = ?",
                        (now, option_id),
                    )

            # Activate new selections
            for option_id in selected:
                if option_id in current_active:
                    continue

                # If there's an inactive row, revive it; otherwise insert a new one.
                inactive = conn.execute(
                    """
                    SELECT id
                    FROM poll_votes
                    WHERE poll_id = ? AND user_id = ? AND option_id = ? AND is_active = 0
                    ORDER BY id DESC
                    LIMIT 1
                    """,
                    (poll_id, user_id, option_id),
                ).fetchone()

                if inactive is not None:
                    conn.execute(
                        "UPDATE poll_votes SET is_active = 1, updated_at = ? WHERE id = ?",
                        (now, int(inactive["id"])),
                    )
                else:
                    conn.execute(
                        """
                        INSERT INTO poll_votes (
                            poll_id, option_id, user_id,
                            created_at, updated_at, is_active
                        ) VALUES (?, ?, ?, ?, ?, 1)
                        """,
                        (poll_id, option_id, user_id, now, now),
                    )

                conn.execute(
                    "UPDATE poll_options SET vote_count = vote_count + 1, updated_at = ? WHERE id = ?",
                    (now, option_id),
                )

            conn.commit()

    def toggle_single_vote(self, poll_id: int, user_id: int, option_id: int) -> None:
        """Legacy helper. Kept for clarity, but multi/single both use set_vote_state."""
        self.set_vote_state(poll_id, user_id, [option_id])

    # ---------- cleanup / restore ----------

    def list_active_polls(self) -> list[sqlite3.Row]:
        return self._fetchall(
            """
            SELECT *
            FROM polls
            WHERE status = 0
            ORDER BY end_at IS NULL DESC, end_at ASC, id ASC
            """
        )

    def list_due_polls(self, now_ts: Optional[int] = None) -> list[sqlite3.Row]:
        now_ts = now_ts or utcnow_ts()
        return self._fetchall(
            """
            SELECT *
            FROM polls
            WHERE status = 0
              AND end_at IS NOT NULL
              AND end_at <= ?
            ORDER BY end_at ASC, id ASC
            """,
            (now_ts,),
        )


# =========================
#  UI helpers
# =========================


def poll_display_embed(
    *,
    poll_row: sqlite3.Row,
    options: list[sqlite3.Row],
    totals: dict[int, int],
    guild: Optional[discord.Guild] = None,
    include_voters: bool = False,
) -> discord.Embed:
    total_votes = sum(totals.values())
    end_at = poll_row["end_at"]
    created_at = datetime.fromtimestamp(int(poll_row["created_at"]), tz=timezone.utc)

    embed = discord.Embed(
        title=f"📊 {poll_row['title']}",
        description=poll_row["description"] or " ",
        color=discord.Color.blurple(),
        timestamp=created_at,
    )

    if end_at:
        embed.add_field(
            name="期間",
            value=f"<t:{int(end_at)}:F>\n(<t:{int(end_at)}:R>)",
            inline=False,
        )
    else:
        embed.add_field(name="期間", value="無期限", inline=False)

    embed.add_field(
        name="方式",
        value="複数投票" if int(poll_row["vote_type"]) == 1 else "単一投票",
        inline=True,
    )
    embed.add_field(
        name="公開",
        value="匿名"
        if int(poll_row["anonymous"]) == 1
        else ("公開" if int(poll_row["public"]) == 1 else "結果のみ"),
        inline=True,
    )
    embed.add_field(
        name="総票数",
        value=str(total_votes),
        inline=True,
    )

    lines: list[str] = []
    for opt in options:
        cnt = totals.get(int(opt["id"]), int(opt["vote_count"]))
        label = opt["option_name"]
        line = f"**{label}**: {cnt}票"
        lines.append(line)

        if (
            include_voters
            and int(poll_row["anonymous"]) == 0
            and int(poll_row["public"]) == 1
            and guild is not None
        ):
            voter_ids = []  # filled by callers when needed
            # placeholder: keep the embed readable; detailed voter listing is added outside by the caller
            pass

    embed.add_field(
        name="選択肢", value="\n".join(lines) if lines else "なし", inline=False
    )
    embed.set_footer(text=f"Poll ID: {poll_row['id']}")
    return embed


class ConfirmView(discord.ui.View):
    def __init__(self, *, timeout: float = 60, owner_id: Optional[int] = None):
        super().__init__(timeout=timeout)
        self.value: Optional[bool] = None
        self.owner_id = owner_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if self.owner_id is not None and interaction.user.id != self.owner_id:
            await interaction.response.send_message(
                "この操作は実行できません。", ephemeral=True
            )
            return False
        return True

    @discord.ui.button(
        label="YES", style=discord.ButtonStyle.danger, custom_id="vote:confirm:yes"
    )
    async def yes(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = True
        await interaction.response.defer()
        self.stop()

    @discord.ui.button(
        label="NO", style=discord.ButtonStyle.secondary, custom_id="vote:confirm:no"
    )
    async def no(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = False
        await interaction.response.defer()
        self.stop()


class ModalLaunchView(discord.ui.View):
    def __init__(
        self, *, label: str, modal_factory, owner_id: int, timeout: float = 180
    ):
        super().__init__(timeout=timeout)
        self.label = label
        self.modal_factory = modal_factory
        self.owner_id = owner_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(
                "この操作は実行できません。", ephemeral=True
            )
            return False
        return True

    @discord.ui.button(
        label="開く", style=discord.ButtonStyle.primary, custom_id="vote:modal:open"
    )
    async def open_modal(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(
                "この操作は実行できません。", ephemeral=True
            )
            return
        await interaction.response.send_modal(self.modal_factory())


class VoteCreateModal(discord.ui.Modal, title="投票を作成"):
    def __init__(self, cog: "VoteCog", settings: CreateSettings):
        super().__init__(timeout=300)
        self.cog = cog
        self.settings = settings

        self.title_input = discord.ui.TextInput(
            label="タイトル",
            style=discord.TextStyle.short,
            max_length=100,
            required=True,
            placeholder="例: 今日の夕飯",
        )
        self.description_input = discord.ui.TextInput(
            label="説明",
            style=discord.TextStyle.paragraph,
            max_length=1000,
            required=False,
            placeholder="説明文があれば入力",
        )
        self.options_input = discord.ui.TextInput(
            label="選択肢",
            style=discord.TextStyle.paragraph,
            max_length=2000,
            required=True,
            placeholder="1行につき1つの選択肢を書いてください",
        )

        self.add_item(self.title_input)
        self.add_item(self.description_input)
        self.add_item(self.options_input)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        title = str(self.title_input.value).strip()
        description = str(self.description_input.value).strip() or None
        options = normalize_lines(str(self.options_input.value))

        if not title:
            await interaction.response.send_message(
                "タイトルが空です。", ephemeral=True
            )
            return

        if len(options) < 2:
            await interaction.response.send_message(
                "選択肢は2つ以上必要です。", ephemeral=True
            )
            return

        if len(options) > 25:
            await interaction.response.send_message(
                "選択肢は25個までです。", ephemeral=True
            )
            return

        channel = interaction.channel
        if not isinstance(channel, discord.abc.Messageable):
            await interaction.response.send_message(
                "この場所では投票を作成できません。", ephemeral=True
            )
            return

        # Send placeholder to get message_id for persistence.
        await interaction.response.defer(ephemeral=True, thinking=True)

        poll_id, poll_message = await self.cog.create_poll_message(
            interaction=interaction,
            title=title,
            description=description,
            settings=self.settings,
            options=options,
        )

        await interaction.followup.send(
            f"投票を作成しました。ID: {poll_id}", ephemeral=True
        )
        if poll_message is not None:
            try:
                await poll_message.reply(
                    f"✅ 投票を作成しました。`ID: {poll_id}`", mention_author=False
                )
            except Exception:
                pass


class VoteEditModal(discord.ui.Modal, title="投票を編集"):
    def __init__(self, cog: "VoteCog", poll_row: sqlite3.Row):
        super().__init__(timeout=300)
        self.cog = cog
        self.poll_row = poll_row

        self.title_input = discord.ui.TextInput(
            label="タイトル",
            style=discord.TextStyle.short,
            max_length=100,
            required=True,
            default=poll_row["title"],
        )
        self.description_input = discord.ui.TextInput(
            label="説明",
            style=discord.TextStyle.paragraph,
            max_length=1000,
            required=False,
            default=poll_row["description"] or "",
        )
        options = self.cog.store.get_options(int(poll_row["id"]), include_deleted=False)
        self.options_input = discord.ui.TextInput(
            label="選択肢",
            style=discord.TextStyle.paragraph,
            max_length=2000,
            required=True,
            default="\n".join(opt["option_name"] for opt in options),
        )

        self.add_item(self.title_input)
        self.add_item(self.description_input)
        self.add_item(self.options_input)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        title = str(self.title_input.value).strip()
        description = str(self.description_input.value).strip() or None
        options = normalize_lines(str(self.options_input.value))

        if len(options) < 2:
            await interaction.response.send_message(
                "選択肢は2つ以上必要です。", ephemeral=True
            )
            return

        removed = await self.cog.update_poll_meta(
            self.poll_row["id"], title=title, description=description, options=options
        )

        await interaction.response.send_message("投票を更新しました。", ephemeral=True)

        if removed:
            await self.cog.notify_removed_options(self.poll_row["id"], removed)

        await self.cog.refresh_poll_message(int(self.poll_row["id"]))


class PollChoiceSelect(discord.ui.Select):
    def __init__(self, cog: "VoteCog", poll_row: sqlite3.Row):
        self.cog = cog
        self.poll_row = poll_row
        options = self.cog.store.get_options(int(poll_row["id"]), include_deleted=False)

        max_values = (
            1
            if int(poll_row["vote_type"]) == 0
            else max(1, min(int(poll_row["max_select"]), len(options)))
        )
        select_options = [
            discord.SelectOption(
                label=opt["option_name"][:100], value=str(int(opt["id"]))
            )
            for opt in options
        ]

        super().__init__(
            placeholder="投票先を選択",
            min_values=1,
            max_values=max_values,
            options=select_options,
            custom_id=f"vote:poll:{int(poll_row['id'])}:select",
            row=0,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        await self.cog.handle_vote_interaction(
            interaction, self.poll_row, list(self.values)
        )


class PollVoteView(discord.ui.View):
    def __init__(self, cog: "VoteCog", poll_row: sqlite3.Row):
        super().__init__(timeout=None)
        self.cog = cog
        self.poll_row = poll_row
        self.add_item(PollChoiceSelect(cog, poll_row))

    @discord.ui.button(
        label="結果更新",
        style=discord.ButtonStyle.secondary,
        custom_id="vote:poll:refresh",
        row=1,
    )
    async def refresh(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await self.cog.send_poll_embed(
            interaction, int(self.poll_row["id"]), ephemeral=True
        )

    @discord.ui.button(
        label="取消",
        style=discord.ButtonStyle.danger,
        custom_id="vote:poll:cancel",
        row=1,
    )
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.cog.handle_vote_clear(interaction, self.poll_row)


class ResultRefreshView(discord.ui.View):
    def __init__(self, cog: "VoteCog", poll_id: int):
        super().__init__(timeout=180)
        self.cog = cog
        self.poll_id = poll_id

    @discord.ui.button(
        label="更新", style=discord.ButtonStyle.primary, custom_id="vote:result:refresh"
    )
    async def refresh(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await self.cog.send_poll_embed(interaction, self.poll_id, ephemeral=False)


class VoteActionSelect(discord.ui.Select):
    def __init__(self, cog: "VoteCog"):
        self.cog = cog
        options = [
            discord.SelectOption(label="create", description="投票を作成"),
            discord.SelectOption(label="edit", description="投票を編集"),
            discord.SelectOption(label="delete", description="投票を削除"),
            discord.SelectOption(label="close", description="投票を終了"),
            discord.SelectOption(label="reopen", description="投票を再開"),
            discord.SelectOption(label="result", description="投票結果を見る"),
        ]
        super().__init__(
            placeholder="管理したい機能を選択",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="vote:manage:actions",
            row=0,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        action = self.values[0]
        await self.cog.route_management_action(interaction, action)


class VoteManagementView(discord.ui.View):
    def __init__(self, cog: "VoteCog", owner_id: int):
        super().__init__(timeout=180)
        self.cog = cog
        self.owner_id = owner_id
        self.add_item(VoteActionSelect(cog))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(
                "この操作は実行できません。", ephemeral=True
            )
            return False
        return True

    @discord.ui.button(
        label="ヘルプ",
        style=discord.ButtonStyle.secondary,
        custom_id="vote:manage:help",
        row=1,
    )
    async def help_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await interaction.response.send_message(
            self.cog.build_help_text(), ephemeral=True
        )


class PollTargetSelect(discord.ui.Select):
    def __init__(self, cog: "VoteCog", action: str, polls: list[sqlite3.Row]):
        self.cog = cog
        self.action = action
        self.polls = polls

        options = []
        for poll in polls[:25]:
            label = f"#{poll['id']} {poll['title']}"
            description = f"status={poll['status']}"
            options.append(
                discord.SelectOption(
                    label=label[:100],
                    description=description[:100],
                    value=str(int(poll["id"])),
                )
            )

        super().__init__(
            placeholder="対象投票を選択",
            min_values=1,
            max_values=1,
            options=options or [discord.SelectOption(label="対象なし", value="0")],
            custom_id=f"vote:target:{action}",
            row=0,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        if self.values[0] == "0":
            await interaction.response.send_message(
                "対象の投票がありません。", ephemeral=True
            )
            return
        await self.cog.handle_target_action(
            interaction, self.action, int(self.values[0])
        )


class PollTargetView(discord.ui.View):
    def __init__(
        self, cog: "VoteCog", action: str, polls: list[sqlite3.Row], owner_id: int
    ):
        super().__init__(timeout=180)
        self.owner_id = owner_id
        self.add_item(PollTargetSelect(cog, action, polls))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(
                "この操作は実行できません。", ephemeral=True
            )
            return False
        return True


# =========================
#  Cog
# =========================


class VoteCog(commands.Cog):
    def __init__(self, bot: commands.Bot, db_path: str = "data/votes.db"):
        self.bot = bot
        self.store = VoteStore(db_path)
        self.store.init_db()
        self.poll_watcher.start()

        self.flag_aliases = {
            "l": "live",
            "live": "live",
            "m": "multi",
            "multi": "multi",
            "a": "anonymous",
            "anonymous": "anonymous",
            "p": "public",
            "public": "public",
            "r": "role",
            "role": "role",
            "c": "channel",
            "channel": "channel",
            "d": "duration",
            "duration": "duration",
            "mx": "max",
            "max": "max",
        }

    def cog_unload(self) -> None:
        self.poll_watcher.cancel()

    # ---------- help ----------

    def build_help_text(self) -> str:
        return (
            "^^vote:\n"
            "    説明: 投票機能の管理画面を開きます。\n"
            "    例: ^^vote\n"
            "    オプション:\n"
            "        ^^vote -l /l live:\n"
            "        説明: リアルタイム結果表示を有効にします。\n"
            "        ^^vote -m /m multi:\n"
            "        説明: 複数投票を有効にします。\n"
            "        ^^vote -a /a anonymous:\n"
            "        説明: 匿名投票にします。\n"
            "        ^^vote -p /p public:\n"
            "        説明: 投票者公開を有効にします。\n"
            "        ^^vote -r /r role:\n"
            "        説明: 投票可能ロールを指定します。\n"
            "        ^^vote -c /c channel:\n"
            "        説明: 投票可能チャンネルを指定します。\n"
            "        ^^vote -d /d duration:\n"
            "        説明: 投票期間を指定します。\n"
            "        ^^vote -mx /mx max:\n"
            "        説明: 最大選択数を指定します。\n"
            "\n"
            "^^vote create:\n"
            "    説明: 投票作成画面を開きます。\n"
            "    例: ^^vote create -m -d 1h30m\n"
            "^^vote edit:\n"
            "    説明: 投票編集画面を開きます。\n"
            "    例: ^^vote edit 123\n"
            "^^vote delete:\n"
            "    説明: 投票削除画面を開きます。\n"
            "    例: ^^vote delete 123\n"
            "^^vote close:\n"
            "    説明: 投票終了画面を開きます。\n"
            "    例: ^^vote close 123\n"
            "^^vote reopen:\n"
            "    説明: 投票再開画面を開きます。\n"
            "    例: ^^vote reopen 123\n"
            "^^vote result:\n"
            "    説明: 投票結果を表示します。\n"
            "    例: ^^vote result 123\n"
        )

    # ---------- command parsing ----------

    def parse_settings(self, token_list: list[str]) -> tuple[CreateSettings, list[str]]:
        settings = CreateSettings()
        rest: list[str] = []

        i = 0
        while i < len(token_list):
            token = token_list[i]
            key = token
            if token.startswith("-") or token.startswith("/"):
                key = token[1:]
            key = key.lower()

            canon = self.flag_aliases.get(key)
            if canon is None:
                rest.append(token)
                i += 1
                continue

            if canon == "multi":
                settings.vote_type = 1
                if settings.max_select < 2:
                    settings.max_select = 2
                i += 1
                continue
            if canon == "live":
                settings.live_result = 1
                i += 1
                continue
            if canon == "anonymous":
                settings.anonymous = 1
                settings.public = 0
                i += 1
                continue
            if canon == "public":
                settings.public = 1
                settings.anonymous = 0
                i += 1
                continue
            if canon == "duration":
                if i + 1 < len(token_list):
                    secs = parse_duration(token_list[i + 1])
                    if secs is not None:
                        settings.duration_seconds = secs
                        i += 2
                        continue
                rest.append(token)
                i += 1
                continue
            if canon == "max":
                if i + 1 < len(token_list) and token_list[i + 1].isdigit():
                    settings.max_select = max(1, int(token_list[i + 1]))
                    i += 2
                    continue
                rest.append(token)
                i += 1
                continue
            if canon in {"role", "channel"}:
                if i + 1 < len(token_list):
                    ids = split_csv_ids(token_list[i + 1])
                    if canon == "role":
                        settings.role_limit = ids or None
                    else:
                        settings.channel_limit = ids or None
                    i += 2
                    continue
                rest.append(token)
                i += 1
                continue

            rest.append(token)
            i += 1

        return settings, rest

    @commands.command(name="vote")
    @commands.guild_only()
    async def vote(self, ctx: commands.Context, *, args: str = "") -> None:
        parts = shlex.split(args) if args else []
        if not parts:
            await ctx.send(
                embed=self.management_embed(),
                view=VoteManagementView(self, ctx.author.id),
            )
            return

        sub = parts[0].lower()
        tail = parts[1:]

        if sub == "help":
            await ctx.send(self.build_help_text())
            return

        if sub == "create":
            settings, _ = self.parse_settings(tail)
            embed = discord.Embed(
                title="投票作成",
                description="下の「開く」ボタンから作成モーダルを開いてください。",
                color=discord.Color.blurple(),
            )
            await ctx.send(
                embed=embed,
                view=ModalLaunchView(
                    label="作成",
                    modal_factory=lambda: VoteCreateModal(self, settings),
                    owner_id=ctx.author.id,
                ),
            )
            return

        if sub in {"edit", "delete", "close", "reopen", "result"}:
            poll_id = None
            if tail and tail[0].isdigit():
                poll_id = int(tail[0])
            if poll_id is not None:
                await self.handle_target_action(ctx, sub, poll_id)
                return

            polls = self.store.list_user_polls(ctx.guild.id, ctx.author.id)
            if not polls:
                await ctx.send("対象の投票がありません。")
                return

            # Filter by permissions unless the user can manage the poll.
            managed = [
                p for p in polls if self.store.can_manage_poll(ctx.author, p, ctx.guild)
            ]
            if not managed:
                await ctx.send("操作できる投票がありません。")
                return

            await ctx.send(
                embed=self.selection_prompt_embed(sub),
                view=PollTargetView(self, sub, managed, ctx.author.id),
            )
            return

        await ctx.send("不明なサブコマンドです。`^^vote help` を確認してください。")

    # ---------- embeds ----------

    def management_embed(self) -> discord.Embed:
        embed = discord.Embed(title="📌 VOTE 管理画面", color=discord.Color.blurple())
        embed.description = (
            "create / edit / delete / close / reopen / result から選んでください。\n"
            "create は新規作成、その他は既存の投票を選んで操作します。"
        )
        return embed

    def selection_prompt_embed(self, action: str) -> discord.Embed:
        return discord.Embed(
            title=f"対象投票選択 - {action}",
            description="操作したい投票を選んでください。",
            color=discord.Color.blurple(),
        )

    # ---------- create / edit / delete / result ----------

    async def create_poll_message(
        self,
        *,
        interaction: discord.Interaction,
        title: str,
        description: str | None,
        settings: CreateSettings,
        options: list[str],
    ) -> tuple[int, Optional[discord.Message]]:
        # For the creation flow we need the final message_id, so send the placeholder first.
        channel = interaction.channel
        if not isinstance(
            channel, discord.TextChannel | discord.Thread | discord.VoiceChannel
        ):
            # fallback to anything sendable
            pass

        embed = discord.Embed(
            title=f"📊 {title}",
            description=description or " ",
            color=discord.Color.blurple(),
        )
        embed.add_field(name="準備中", value="投票を構築しています...", inline=False)

        # send message in the same channel, then persist.
        sent = await interaction.channel.send(embed=embed)
        poll_id = self.store.create_poll(
            guild_id=interaction.guild_id or 0,
            channel_id=interaction.channel_id or 0,
            message_id=sent.id,
            creator_id=interaction.user.id,
            title=title,
            description=description,
            settings=settings,
            options=options,
        )

        poll_row = self.store.get_poll(poll_id)
        if poll_row is None:
            return poll_id, sent

        await sent.edit(
            embed=await self.build_poll_embed(poll_row),
            view=PollVoteView(self, poll_row),
        )
        return poll_id, sent

    async def update_poll_meta(
        self, poll_id: int, *, title: str, description: str | None, options: list[str]
    ) -> list[int]:
        return await asyncio.to_thread(
            self.store.update_poll_meta,
            poll_id,
            title=title,
            description=description,
            options=options,
        )

    async def notify_removed_options(
        self, poll_id: int, removed_option_ids: list[int]
    ) -> None:
        poll = self.store.get_poll(poll_id)
        if poll is None or int(poll["status"]) == 2:
            return

        channel = self.bot.get_channel(int(poll["channel_id"]))
        if not isinstance(channel, discord.abc.Messageable):
            return

        for option_id in removed_option_ids:
            option_row = self.store.get_option(option_id)
            if option_row is None:
                continue

            voter_ids = self.store.get_voter_ids_for_option(option_id)
            if not voter_ids:
                continue

            message = (
                f"投票 `#{poll_id}` の選択肢 `{option_row['option_name']}` が削除されました。\n"
                f"必要なら投票内容を見直してください。"
            )

            for uid in voter_ids:
                user = self.bot.get_user(uid)
                if user is None:
                    try:
                        user = await self.bot.fetch_user(uid)
                    except Exception:
                        user = None
                if user is None:
                    continue
                try:
                    await user.send(message)
                except Exception:
                    # DM cannot be delivered. Keep silent.
                    pass

    async def handle_target_action(
        self, interaction_or_ctx, action: str, poll_id: int
    ) -> None:
        poll = self.store.get_poll(poll_id)
        if poll is None:
            if isinstance(interaction_or_ctx, commands.Context):
                await interaction_or_ctx.send("投票が見つかりません。")
            else:
                await interaction_or_ctx.response.send_message(
                    "投票が見つかりません。", ephemeral=True
                )
            return

        if isinstance(interaction_or_ctx, commands.Context):
            guild = interaction_or_ctx.guild
            member = interaction_or_ctx.author
            channel_id = interaction_or_ctx.channel.id
            channel = interaction_or_ctx.channel
        else:
            guild = interaction_or_ctx.guild
            member = interaction_or_ctx.user
            channel_id = interaction_or_ctx.channel_id or 0
            channel = interaction_or_ctx.channel

        # channel/role restrictions
        if isinstance(
            member, discord.Member
        ) and not self.store.can_use_poll_in_channel(member, poll, channel_id):
            if isinstance(interaction_or_ctx, commands.Context):
                await interaction_or_ctx.send("このチャンネルでは使用できません。")
            else:
                await interaction_or_ctx.response.send_message(
                    "このチャンネルでは使用できません。", ephemeral=True
                )
            return

        if action == "result":
            await self.send_poll_embed(
                interaction_or_ctx,
                poll_id,
                ephemeral=isinstance(interaction_or_ctx, commands.Context) is False,
            )
            return

        if not self.store.can_manage_poll(member, poll, guild):
            if isinstance(interaction_or_ctx, commands.Context):
                await interaction_or_ctx.send("権限がありません。")
            else:
                await interaction_or_ctx.response.send_message(
                    "権限がありません。", ephemeral=True
                )
            return

        if action == "edit":
            if isinstance(interaction_or_ctx, commands.Context):
                embed = discord.Embed(
                    title=f"投票編集 #{poll_id}",
                    description="下の「開く」ボタンから編集モーダルを開いてください。",
                    color=discord.Color.blurple(),
                )
                await interaction_or_ctx.send(
                    embed=embed,
                    view=ModalLaunchView(
                        label="編集",
                        modal_factory=lambda: VoteEditModal(self, poll),
                        owner_id=interaction_or_ctx.author.id,
                    ),
                )
                return
            await interaction_or_ctx.response.send_modal(VoteEditModal(self, poll))
            return

        if action == "delete":
            view = ConfirmView(
                owner_id=(
                    interaction_or_ctx.author.id
                    if isinstance(interaction_or_ctx, commands.Context)
                    else interaction_or_ctx.user.id
                )
            )
            if isinstance(interaction_or_ctx, commands.Context):
                msg = await interaction_or_ctx.send("本当に削除しますか？", view=view)
                await view.wait()
                if view.value:
                    await self.delete_poll_and_refresh(poll_id)
                    await msg.edit(content="削除しました。", view=None)
                else:
                    await msg.edit(content="キャンセルしました。", view=None)
            else:
                await interaction_or_ctx.response.send_message(
                    "本当に削除しますか？", view=view, ephemeral=True
                )
                await view.wait()
                if view.value:
                    await self.delete_poll_and_refresh(poll_id)
                    await interaction_or_ctx.followup.send(
                        "削除しました。", ephemeral=True
                    )
                else:
                    await interaction_or_ctx.followup.send(
                        "キャンセルしました。", ephemeral=True
                    )
            return

        if action == "close":
            self.store.close_poll(poll_id)
            await self.refresh_poll_message(poll_id)
            await self._send_action_feedback(interaction_or_ctx, "投票を終了しました。")
            return

        if action == "reopen":
            self.store.reopen_poll(poll_id)
            await self.refresh_poll_message(poll_id)
            await self._send_action_feedback(interaction_or_ctx, "投票を再開しました。")
            return

        await self._send_action_feedback(interaction_or_ctx, "未対応の操作です。")

    async def route_management_action(
        self, interaction: discord.Interaction, action: str
    ) -> None:
        if action == "create":
            await interaction.response.send_modal(
                VoteCreateModal(self, CreateSettings())
            )
            return

        polls = self.store.list_user_polls(
            interaction.guild_id or 0, interaction.user.id
        )
        managed = [
            p
            for p in polls
            if self.store.can_manage_poll(interaction.user, p, interaction.guild)
        ]
        if not managed:
            await interaction.response.send_message(
                "対象の投票がありません。", ephemeral=True
            )
            return

        await interaction.response.send_message(
            embed=self.selection_prompt_embed(action),
            view=PollTargetView(self, action, managed, interaction.user.id),
            ephemeral=True,
        )

    async def delete_poll_and_refresh(self, poll_id: int) -> None:
        self.store.delete_poll_soft(poll_id)
        poll = self.store.get_poll(poll_id)
        if poll:
            await self.refresh_poll_message(poll_id)

    async def _send_action_feedback(self, interaction_or_ctx, text: str) -> None:
        if isinstance(interaction_or_ctx, commands.Context):
            await interaction_or_ctx.send(text)
        else:
            try:
                await interaction_or_ctx.response.send_message(text, ephemeral=True)
            except discord.InteractionResponded:
                await interaction_or_ctx.followup.send(text, ephemeral=True)

    # ---------- voting ----------

    async def handle_vote_clear(
        self, interaction: discord.Interaction, poll_row: sqlite3.Row
    ) -> None:
        if interaction.user.id == int(poll_row["creator_id"]):
            # Creator can always clear own vote? Not required, but harmless.
            pass

        await interaction.response.defer(ephemeral=True, thinking=False)
        current = self.store.get_active_vote_option_ids(
            int(poll_row["id"]), interaction.user.id
        )
        if not current:
            await interaction.followup.send("まだ投票していません。", ephemeral=True)
            return

        self.store.set_vote_state(int(poll_row["id"]), interaction.user.id, [])
        await self.refresh_poll_message(int(poll_row["id"]))
        await interaction.followup.send("投票を取り消しました。", ephemeral=True)

    async def handle_vote_interaction(
        self,
        interaction: discord.Interaction,
        poll_row: sqlite3.Row,
        selected_values: list[str],
    ) -> None:
        if int(poll_row["status"]) != 0:
            await interaction.response.send_message(
                "この投票は終了しています。", ephemeral=True
            )
            return

        if not self.store.can_use_poll_in_channel(
            interaction.user
            if isinstance(interaction.user, discord.Member)
            else interaction.user,
            poll_row,
            interaction.channel_id or 0,
        ):
            await interaction.response.send_message(
                "このチャンネルでは投票できません。", ephemeral=True
            )
            return

        option_ids = [int(v) for v in selected_values if v.isdigit()]
        valid_ids = {
            int(r["id"])
            for r in self.store.get_options(int(poll_row["id"]), include_deleted=False)
        }
        option_ids = [oid for oid in option_ids if oid in valid_ids]

        if not option_ids:
            await interaction.response.send_message(
                "有効な選択肢がありません。", ephemeral=True
            )
            return

        if int(poll_row["vote_type"]) == 0 and len(option_ids) > 1:
            option_ids = option_ids[:1]

        if int(poll_row["vote_type"]) == 1:
            max_select = max(1, min(int(poll_row["max_select"]), len(valid_ids)))
            if len(option_ids) > max_select:
                await interaction.response.send_message(
                    f"選択数は {max_select} までです。", ephemeral=True
                )
                return

        await interaction.response.defer(ephemeral=True, thinking=False)
        self.store.set_vote_state(int(poll_row["id"]), interaction.user.id, option_ids)
        await self.refresh_poll_message(int(poll_row["id"]))
        await interaction.followup.send("投票を保存しました。", ephemeral=True)

    # ---------- result / embeds ----------

    async def build_poll_embed(self, poll_row: sqlite3.Row) -> discord.Embed:
        options = self.store.get_options(int(poll_row["id"]), include_deleted=False)
        totals = self.store.get_poll_vote_totals(int(poll_row["id"]))
        return poll_display_embed(
            poll_row=poll_row,
            options=options,
            totals=totals,
        )

    async def send_poll_embed(
        self, interaction_or_ctx, poll_id: int, *, ephemeral: bool
    ) -> None:
        poll = self.store.get_poll(poll_id)
        if poll is None:
            if isinstance(interaction_or_ctx, commands.Context):
                await interaction_or_ctx.send("投票が見つかりません。")
            else:
                await interaction_or_ctx.response.send_message(
                    "投票が見つかりません。", ephemeral=True
                )
            return

        options = self.store.get_options(poll_id, include_deleted=False)
        totals = self.store.get_poll_vote_totals(poll_id)
        embed = poll_display_embed(poll_row=poll, options=options, totals=totals)

        if int(poll["public"]) == 1 and int(poll["anonymous"]) == 0:
            details: list[str] = []
            for opt in options:
                voter_ids = self.store.get_voter_ids_for_option(int(opt["id"]))
                if not voter_ids:
                    continue
                names = []
                for uid in voter_ids[:30]:
                    member = None
                    if (
                        isinstance(interaction_or_ctx, commands.Context)
                        and interaction_or_ctx.guild is not None
                    ):
                        member = interaction_or_ctx.guild.get_member(uid)
                    elif (
                        isinstance(interaction_or_ctx, discord.Interaction)
                        and interaction_or_ctx.guild is not None
                    ):
                        member = interaction_or_ctx.guild.get_member(uid)
                    if member is None:
                        names.append(f"<@{uid}>")
                    else:
                        names.append(member.display_name)
                details.append(f"**{opt['option_name']}**: " + ", ".join(names))
            if details:
                embed.add_field(
                    name="投票者", value="\n".join(details)[:1024], inline=False
                )

        if isinstance(interaction_or_ctx, commands.Context):
            await interaction_or_ctx.send(
                embed=embed, view=ResultRefreshView(self, poll_id)
            )
        else:
            if interaction_or_ctx.response.is_done():
                await interaction_or_ctx.followup.send(
                    embed=embed,
                    view=ResultRefreshView(self, poll_id),
                    ephemeral=ephemeral,
                )
            else:
                await interaction_or_ctx.response.send_message(
                    embed=embed,
                    view=ResultRefreshView(self, poll_id),
                    ephemeral=ephemeral,
                )

    async def refresh_poll_message(self, poll_id: int) -> None:
        poll = self.store.get_poll(poll_id)
        if poll is None:
            return

        channel = self.bot.get_channel(int(poll["channel_id"]))
        if channel is None:
            try:
                channel = await self.bot.fetch_channel(int(poll["channel_id"]))
            except Exception:
                return

        if not isinstance(channel, discord.abc.Messageable):
            return

        try:
            message = await channel.fetch_message(int(poll["message_id"]))
        except Exception:
            return

        options = self.store.get_options(poll_id, include_deleted=False)
        totals = self.store.get_poll_vote_totals(poll_id)
        embed = poll_display_embed(poll_row=poll, options=options, totals=totals)
        view = None if int(poll["status"]) != 0 else PollVoteView(self, poll)
        try:
            await message.edit(embed=embed, view=view)
        except Exception:
            pass

    # ---------- automation ----------

    @tasks.loop(minutes=1)
    async def poll_watcher(self) -> None:
        for poll in self.store.list_due_polls():
            self.store.close_poll(int(poll["id"]))
            await self.refresh_poll_message(int(poll["id"]))

    @poll_watcher.before_loop
    async def before_poll_watcher(self) -> None:
        await self.bot.wait_until_ready()

    async def cog_load(self) -> None:
        await self.restore_views()

    async def restore_views(self) -> None:
        for poll in self.store.list_active_polls():
            message_id = int(poll["message_id"])
            self.bot.add_view(PollVoteView(self, poll), message_id=message_id)

    # ---------- startup event ----------

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        # Safety restore in case cog_load happens before bot fully ready.
        if not self.poll_watcher.is_running():
            self.poll_watcher.start()
        await self.restore_views()


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(VoteCog(bot))
