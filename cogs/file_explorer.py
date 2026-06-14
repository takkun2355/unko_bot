import os
from discord.ext import commands


class FileExplorer(commands.Cog):
    # Bot 実行中のフォルダを基準にする
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))

    def __init__(self, bot):
        self.bot = bot
        # オーナーIDリスト（必要なら複数指定可）
        self.OWNER_IDS = {123456789012345678, 987654321098765432}

    @commands.command(name="files")
    async def files(self, ctx, *args):
        """
        管理者＆オーナー専用ファイル閲覧コマンド
        使用例:
        ^^files                  -> Botフォルダ内のトップ層
        ^^files venv             -> venv 内のファイル表示
        ^^files .txt             -> .txt ファイルだけ表示
        ^^files address          -> BASE_DIR のフルパスを表示
        """

        # 権限チェック
        if not ctx.author.guild_permissions.administrator and ctx.author.id not in self.OWNER_IDS:
            await ctx.send("❌ このコマンドを使用できるのは管理者とBotオーナーのみです。")
            return

        target_dir = self.BASE_DIR
        extension_filter = None
        full_path_mode = False

        # 引数処理
        if args:
            if args[0].lower() == "address":
                full_path_mode = True
            elif args[0].startswith("."):
                extension_filter = args[0]
            else:
                candidate_dir = os.path.join(self.BASE_DIR, args[0])
                if (
                    os.path.exists(candidate_dir)
                    and os.path.commonpath([candidate_dir, self.BASE_DIR]) == self.BASE_DIR
                ):
                    target_dir = candidate_dir
                else:
                    await ctx.send(f"❌ `{args[0]}` は存在しないか閲覧不可です。")
                    return

        if not os.path.exists(target_dir):
            await ctx.send(f"❌ `{target_dir}` が存在しません。")
            return

        def list_dir(dir_path, prefix=""):
            try:
                items = sorted(os.listdir(dir_path))
            except PermissionError:
                return [f"{prefix}⚠ 権限がありません"]

            lines = []
            for i, item in enumerate(items):
                path = os.path.join(dir_path, item)
                if extension_filter and not item.endswith(extension_filter):
                    continue
                branch = "└─" if i == len(items) - 1 else "├─"
                display_name = path if full_path_mode else item
                lines.append(f"{prefix}{branch} {display_name}")
                if os.path.isdir(path):
                    extension = "   " if i == len(items) - 1 else "│  "
                    lines.extend(list_dir(path, prefix + extension))
            return lines

        lines = list_dir(target_dir)
        if not lines:
            await ctx.send("表示できるファイル・フォルダがありません。")
            return

        header = f"📁 ディレクトリ: {target_dir if full_path_mode else os.path.relpath(target_dir, self.BASE_DIR)}\n"
        msg = "\n".join(lines)
        full_msg = f"```\n{header}{msg}\n```"

        # Discord メッセージ長さに合わせて分割送信
        max_len = 1900
        for i in range(0, len(full_msg), max_len):
            await ctx.send(full_msg[i : i + max_len])


# Cog をロードする関数
async def setup(bot):
    await bot.add_cog(FileExplorer(bot))
