import os
import re
import sys


def process_file(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 絵文字削除
    emoji_pattern = re.compile(r"[✅🔧⚠️❌✨🎲ℹ️]")
    content = emoji_pattern.sub("", content)

    # print を logger に置き換え
    # print("...") -> logger.info("...")
    # 簡易的に変換する
    # 実際の運用ではログレベルの自動判定は難しいので、すべてinfoにし、必要であれば後で手動修正する
    content = content.replace("print(", "logger.info(")

    # import の追加
    if "import logging" not in content:
        content = re.sub(r"(import .*)", r"import logging\n\1", content, count=1)

    if "logger = logging.getLogger(__name__)" not in content:
        content = re.sub(r"(import .*)", r"\1\n\nlogger = logging.getLogger(__name__)", content, count=1)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)


cogs_dir = "D:/programming/github/unko_bot/cogs/"
for filename in os.listdir(cogs_dir):
    if filename.endswith(".py"):
        process_file(os.path.join(cogs_dir, filename))
        print(f"Processed: {filename}")
