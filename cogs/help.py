import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import discord
from discord.ext import commands

SEARCH_PATHS = [
    Path(__file__).with_name("command_help.json"),
    Path(__file__).parent.parent / "command_help.json",
    Path.cwd() / "command_help.json",
]

commands_found = []

for path in SEARCH_PATHS:
    if path.exists():
        DATA_FILE = path
        break
else:
    DATA_FILE = None

if not DATA_FILE.exists():
    print("[WARNING] command_help.json not found")

for cmd in self.bot.commands:
    commands_found.append({
        "name": cmd.name,
        "description": cmd.help or cmd.brief or "説明なし"
    })

def _clean_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _truncate(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    if limit <= 1:
        return text[:limit]
    return text[: max(0, limit - 1)] + "…"


def _inline_code(text: str) -> str:
    text = _clean_text(text).replace("`", "ˋ")
    return f"`{text}`" if text else "`-`"


def _normalize_query(text: str) -> str:
    return re.sub(r"\s+", " ", _clean_text(text)).lower()


class HelpView(discord.ui.View):
    def __init__(self, cog: "HelpCog", author_id: int, page: int = 0):
        super().__init__(timeout=120)
        self.cog = cog
        self.author_id = author_id
        self.page = page
        self.message: Optional[discord.Message] = None
        self._sync_buttons()

    def _sync_buttons(self) -> None:
        has_prev = self.page > 0
        has_next = self.page < max(0, self.cog.page_count - 1)

        for item in self.children:
            if isinstance(item, discord.ui.Button):
                if item.custom_id == "help_prev":
                    item.disabled = not has_prev
                elif item.custom_id == "help_next":
                    item.disabled = not has_next

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(
                "このヘルプ操作は呼び出した本人だけが使えます。",
                ephemeral=True,
            )
            return False
        return True

    async def on_timeout(self) -> None:
        for item in self.children:
            if isinstance(item, discord.ui.Button):
                item.disabled = True
        if self.message:
            try:
                await self.message.edit(view=self)
            except discord.HTTPException:
                pass

    async def _refresh(self, interaction: discord.Interaction) -> None:
        self._sync_buttons()
        embed = self.cog.build_list_embed(self.page)
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="前へ", style=discord.ButtonStyle.secondary, custom_id="help_prev")
    async def prev_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        if self.page > 0:
            self.page -= 1
        await self._refresh(interaction)

    @discord.ui.button(label="次へ", style=discord.ButtonStyle.secondary, custom_id="help_next")
    async def next_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        if self.page < self.cog.page_count - 1:
            self.page += 1
        await self._refresh(interaction)


class HelpCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.prefix = DEFAULT_PREFIX
        self.per_page = PER_PAGE
        self.data = self._load_help_json()
        self.top_level_commands = self._collect_top_level_commands()
        self.all_entries: List[Dict[str, Any]] = []
        self.path_index: Dict[Tuple[str, ...], List[Dict[str, Any]]] = {}
        self.name_index: Dict[str, List[Dict[str, Any]]] = {}
        self._build_indexes()

    def _load_help_json(self) -> Dict[str, Any]:
        try:
            with DATA_FILE.open("r", encoding="utf-8") as fp:
                return json.load(fp)
        except FileNotFoundError:
            return {
                "meta": {
                    "prefix": DEFAULT_PREFIX,
                    "bot_name": "Unkoman Bot",
                    "schema_version": 2,
                },
                "sections": [],
            }
        except json.JSONDecodeError:
            return {
                "meta": {
                    "prefix": DEFAULT_PREFIX,
                    "bot_name": "Unkoman Bot",
                    "schema_version": 2,
                },
                "sections": [],
            }

    def _collect_top_level_commands(self) -> List[Dict[str, Any]]:
        commands: List[Dict[str, Any]] = []
        sections = self.data.get("sections", [])

        if isinstance(sections, list):
            for section in sections:
                groups = section.get("groups", []) if isinstance(section, dict) else []
                if not isinstance(groups, list):
                    continue
                for group in groups:
                    group_name = _clean_text(group.get("name")) if isinstance(group, dict) else ""
                    group_commands = group.get("commands", []) if isinstance(group, dict) else []
                    if not isinstance(group_commands, list):
                        continue
                    for command in group_commands:
                        if isinstance(command, dict):
                            commands.append(
                                {
                                    "section": _clean_text(section.get("name")) if isinstance(section, dict) else "",
                                    "group": group_name,
                                    "command": command,
                                }
                            )
        return commands

    def _build_indexes(self) -> None:
        for item in self.top_level_commands:
            section = item["section"]
            group = item["group"]
            command = item["command"]
            self._index_command(command, section, group, [command.get("name", "")])

    def _index_command(
        self,
        command: Dict[str, Any],
        section: str,
        group: str,
        path: List[str],
    ) -> None:
        norm_path = tuple(_normalize_query(part) for part in path if _clean_text(part))
        entry = {
            "section": section,
            "group": group,
            "path": path[:],
            "command": command,
        }
        self.all_entries.append(entry)
        self.path_index.setdefault(norm_path, []).append(entry)

        name_key = _normalize_query(command.get("name", ""))
        if name_key:
            self.name_index.setdefault(name_key, []).append(entry)

        for alias in command.get("aliases", []) or []:
            alias_key = _normalize_query(alias)
            if alias_key:
                self.name_index.setdefault(alias_key, []).append(entry)

        for child_key in ("subcommands", "admin_subcommands"):
            for child in command.get(child_key, []) or []:
                if isinstance(child, dict):
                    self._index_command(child, section, group, path + [child.get("name", "")])

    @property
    def page_count(self) -> int:
        if not self.top_level_commands:
            return 1
        return max(1, (len(self.top_level_commands) + self.per_page - 1) // self.per_page)

    def _resolve_entry(self, query: str) -> Tuple[str, Any]:
        tokens = [_normalize_query(part) for part in _clean_text(query).split() if _clean_text(part)]
        if not tokens:
            return "empty", None

        path_key = tuple(tokens)
        exact = self.path_index.get(path_key)
        if exact:
            if len(exact) == 1:
                return "ok", exact[0]
            return "ambiguous", exact

        if len(tokens) == 1:
            by_name = self.name_index.get(tokens[0], [])
            if not by_name:
                return "not_found", None

            # Prefer exact top-level command if there is one.
            top_level = [e for e in by_name if len(e["path"]) == 1]
            if len(top_level) == 1:
                return "ok", top_level[0]
            if len(top_level) > 1:
                return "ambiguous", top_level

            if len(by_name) == 1:
                return "ok", by_name[0]
            return "ambiguous", by_name

        # Fallback: exact last token name among all entries can still be useful.
        tail_matches = [e for e in self.all_entries if _normalize_query(e["path"][-1]) == tokens[-1]]
        if len(tail_matches) == 1:
            return "ok", tail_matches[0]
        if len(tail_matches) > 1:
            return "ambiguous", tail_matches

        return "not_found", None

    def _command_short_desc(self, command: Dict[str, Any]) -> str:
        return _clean_text(command.get("description")) or "説明なし"

    def _entry_title(self, entry: Dict[str, Any]) -> str:
        path = entry["path"]
        return f"{self.prefix}{' '.join(path)}"

    def _entry_usage(self, command: Dict[str, Any]) -> str:
        usage = _clean_text(command.get("usage"))
        if usage:
            return usage
        path = _clean_text(command.get("name"))
        return f"{self.prefix}{path}" if path else self.prefix

    def _render_subcommands(self, subcommands: List[Dict[str, Any]], parent_path: List[str], depth: int = 0) -> List[str]:
        lines: List[str] = []
        indent = "  " * depth
        for child in subcommands:
            if not isinstance(child, dict):
                continue
            child_name = _clean_text(child.get("name"))
            if not child_name:
                continue
            child_path = parent_path + [child_name]
            usage = _clean_text(child.get("usage")) or f"{self.prefix}{' '.join(child_path)}"
            description = _clean_text(child.get("description"))
            line = f"{indent}• {_inline_code(usage)}"
            if description:
                line += f"\n{indent}  {description}"
            lines.append(line)

            nested = []
            nested.extend(child.get("subcommands", []) or [])
            nested.extend(child.get("admin_subcommands", []) or [])
            if nested:
                lines.extend(self._render_subcommands(nested, child_path, depth + 1))
        return lines

    def _build_detail_embed(self, entry: Dict[str, Any]) -> discord.Embed:
        command = entry["command"]
        title = self._entry_title(entry)
        embed = discord.Embed(
            title=title,
            description=self._command_short_desc(command),
            color=discord.Color.green(),
        )

        usage = self._entry_usage(command)
        embed.add_field(name="使用例", value=_inline_code(usage), inline=False)

        aliases = command.get("aliases", []) or []
        if aliases:
            embed.add_field(
                name="別名",
                value=", ".join(_inline_code(alias) for alias in aliases),
                inline=False,
            )

        notes = command.get("notes", []) or []
        if isinstance(notes, str):
            notes = [notes]
        if notes:
            embed.add_field(
                name="補足",
                value="\n".join(f"• {_clean_text(note)}" for note in notes if _clean_text(note)),
                inline=False,
            )

        examples = command.get("examples", []) or []
        if examples:
            lines = []
            for example in examples:
                if not isinstance(example, dict):
                    continue
                ex_usage = _clean_text(example.get("usage"))
                ex_desc = _clean_text(example.get("description"))
                if ex_desc:
                    lines.append(f"• {_inline_code(ex_usage)}\n  {ex_desc}")
                else:
                    lines.append(f"• {_inline_code(ex_usage)}")
            if lines:
                embed.add_field(name="例", value="\n".join(lines), inline=False)

        options = command.get("options", []) or []
        modes = command.get("modes", []) or []
        option_lines: List[str] = []
        for opt in options:
            if not isinstance(opt, dict):
                continue
            opt_usage = _clean_text(opt.get("usage"))
            opt_desc = _clean_text(opt.get("description"))
            if opt_usage:
                if opt_desc:
                    option_lines.append(f"• {_inline_code(opt_usage)}\n  {opt_desc}")
                else:
                    option_lines.append(f"• {_inline_code(opt_usage)}")
        if modes:
            if option_lines:
                option_lines.append("")
            for mode in modes:
                if not isinstance(mode, dict):
                    continue
                mode_name = _clean_text(mode.get("name"))
                mode_desc = _clean_text(mode.get("description"))
                if mode_name:
                    if mode_desc:
                        option_lines.append(f"• {_inline_code(mode_name)}\n  {mode_desc}")
                    else:
                        option_lines.append(f"• {_inline_code(mode_name)}")
        if option_lines:
            embed.add_field(name="オプション", value="\n".join(option_lines), inline=False)

        child_lines: List[str] = []
        subcommands = command.get("subcommands", []) or []
        admin_subcommands = command.get("admin_subcommands", []) or []
        if subcommands:
            child_lines.extend(self._render_subcommands(subcommands, entry["path"]))
        if admin_subcommands:
            if child_lines:
                child_lines.append("")
            child_lines.append("管理者向け")
            child_lines.extend(self._render_subcommands(admin_subcommands, entry["path"]))
        if child_lines:
            embed.add_field(name="子要素", value="\n".join(child_lines), inline=False)

        footer_bits = []
        if entry.get("section"):
            footer_bits.append(entry["section"])
        if entry.get("group") and entry["group"] != entry.get("section"):
            footer_bits.append(entry["group"])
        if footer_bits:
            embed.set_footer(text=" / ".join(footer_bits))

        return embed

    def build_list_embed(self, page: int) -> discord.Embed:
        page = max(0, min(page, self.page_count - 1))
        start = page * self.per_page
        end = start + self.per_page

        embed = discord.Embed(
            title="📖 コマンド一覧",
            description="`^^help <CMD>` で詳細を表示します。",
            color=discord.Color.blurple(),
        )

        if not self.top_level_commands:
            embed.add_field(
                name="案内",
                value="ヘルプデータが見つかりません。",
                inline=False,
            )
            return embed

        for item in self.top_level_commands[start:end]:
            command = item["command"]
            name = self._entry_title(item)
            desc = self._command_short_desc(command)
            embed.add_field(
                name=name,
                value=_truncate(desc, 900),
                inline=False,
            )

        embed.set_footer(text=f"{page + 1}/{self.page_count} ページ")
        return embed

    def _build_ambiguous_embed(self, query: str, matches: List[Dict[str, Any]]) -> discord.Embed:
        embed = discord.Embed(
            title="候補が複数あります",
            description=f"`{query}` に一致するコマンドが複数見つかりました。",
            color=discord.Color.orange(),
        )
        lines = []
        for entry in matches[:10]:
            lines.append(
                f"• `{self.prefix}{' '.join(entry['path'])}` - {_truncate(self._command_short_desc(entry['command']), 120)}"
            )
        embed.add_field(name="候補", value="\n".join(lines), inline=False)
        embed.set_footer(text=f"`{self.prefix}help <CMD>` で、できるだけ正確に指定してください。")
        return embed

    @commands.command(name="help", aliases=["h"])
    async def help_command(self, ctx: commands.Context, *, arg: Optional[str] = None):
        if not arg:
            view = HelpView(self, ctx.author.id, page=0)
            embed = self.build_list_embed(0)
            message = await ctx.send(embed=embed, view=view)
            view.message = message
            return

        status, payload = self._resolve_entry(arg)
        if status == "ok":
            embed = self._build_detail_embed(payload)
            await ctx.send(embed=embed)
            return

        if status == "ambiguous":
            embed = self._build_ambiguous_embed(arg, payload)
            await ctx.send(embed=embed)
            return

        embed = discord.Embed(
            title="見つかりませんでした",
            description=f"`{arg}` に一致するコマンドは見つかりませんでした。",
            color=discord.Color.red(),
        )
        embed.add_field(
            name="試す例",
            value=f"`{self.prefix}help vote`\n`{self.prefix}help vote create`\n`{self.prefix}help pin`",
            inline=False,
        )
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(HelpCog(bot))
