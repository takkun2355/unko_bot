import sys
import os
import asyncio
import traceback
import discord
import time
import bot_markov as mu
from discord.ext import commands

# =========================================
# Discord Bot の Intents 設定
# =========================================
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="^^", intents=intents, help_command=None)

CHAT_LOG = "chatlog.txt"
SPECIAL_LOG = "special_log.txt"
TARGET_USER = 1118799600816492626  # 永久保存ユーザー

FAILED_COGS = []  # Cogロード失敗を記録

# =========================================
# talkコマンド (Markov生成)
# =========================================
@bot.command()
async def talk(ctx, length: int = 50, n: int = 5):
    await ctx.send("^^talkは学習データが多いほど生成に時間が掛かります。\nそのため時間がかかる可能性があります。\n^^talkを使用中はすべてのサーバーまたはDMでのコマンドが使用不可になる可能性があります。")
    """
    Markovモデルで文章生成
    length: 生成文字数 (デフォルト50)
    n: n-gramの長さ (デフォルト5)
    例: ^^talk 80 6
    """
    combined_text = mu.read_logs()
    if not combined_text.strip():
        await ctx.send("まだ学習データがありません！")
        return

    model = mu.build_model(combined_text, n=n)
    if not model:
        await ctx.send("モデルの生成に失敗しました…")
        return

    sentence = mu.generate_sentence(model, length=length)
    await ctx.send(sentence)

# =========================================
# Stdin command handler
# =========================================
class MockContext:
    """A mock context for invoking commands from stdin."""
    def __init__(self, channel, bot_instance):
        self.channel = channel
        self.bot = bot_instance

    async def send(self, *args, **kwargs):
        if self.channel:
            await self.channel.send(*args, **kwargs)
        else:
            print(*args)

async def handle_stdin(bot_instance):
    """Reads commands from stdin and executes them."""
    loop = asyncio.get_running_loop()
    await bot_instance.wait_until_ready()
    
    channel_id = 1416694818339291147
    channel = bot_instance.get_channel(channel_id)
    if not channel:
        print(f"Fatal: Could not find channel {channel_id} for stdin command output.")
        return

    mock_ctx = MockContext(channel, bot_instance)

    while not bot_instance.is_closed():
        line = await loop.run_in_executor(None, sys.stdin.readline)
        command_name = line.strip()

        if not command_name:
            if line == '':
                print("stdin closed. Exiting stdin handler.")
                return
            continue

        command = bot_instance.get_command(command_name)
        if command:
            print(f"Executing command from stdin: {command_name}")
            asyncio.create_task(command.callback(mock_ctx))
        else:
            print(f"Unknown command from stdin: {command_name}")

# =========================================
# Cog をロードして起動
# =========================================
async def main():
    async with bot:
        # Start the stdin handler as a background task
        stdin_task = asyncio.create_task(handle_stdin(bot))

        # Cog を追加
        cogs = [
            "cogs.roulette",
            "cogs.weather",
            "cogs.help",
            "cogs.file_explorer",
            "cogs.fun_games",
            "cogs.server",
            "cogs.fun",
            "cogs.spam",
            "cogs.translate",
            "cogs.utility_url",
            "cogs.janken",
            "cogs.number",
            "cogs.slot",
            "cogs.shiritori",
            "cogs.bot_event",
            "cogs.Basic_command",
            "cogs.not_find_command",
            "cogs.roast",
            "cogs.SlashAuto",
            "cogs.AutoRoleAssigner",
            "cogs.nameaga",
            "cogs.WorldClock",
            "cogs.OnionFortune",
            "cogs.PizzaGenerator",
            "cogs.Achievements",
            "cogs.AntiSpam",
            "cogs.WikipediaSearch",
            "cogs.HentaiRank",
            "cogs.TPStock",
            "cogs.BirthdayManager",
            "cogs.IceBot",
            "cogs.IQDownQuotes",
            "cogs.BlackJackFull",
            "cogs.WishBot",
            "cogs.Calculator",
            "cogs.RPGCog",
            "cogs.ReactionGameCog",
            "cogs.QuoteCog",
            "cogs.RiddleCog",
            "cogs.MagicSpellBot",
            "cogs.SpamOwnerCog",
            "cogs.random_name_auto",
            "cogs.IconCog"
        ]
        for cog in cogs:
            try:
                await bot.load_extension(cog)
                print(f"Loaded cog: {cog}")
            except Exception as e:
                error_text = "".join(traceback.format_exception(type(e), e, e.__traceback__))
                FAILED_COGS.append((cog, error_text))
                print(f"Failed to load cog {cog}:\n{error_text}")

        # トークン取得
        TOKEN = os.getenv("DISCORD_BOT_TOKEN")
        if not TOKEN:
            print("❌ Botトークンが設定されていません！")
            stdin_task.cancel()
            return

        # Bot 起動
        await bot.start(TOKEN)

# =========================================
# 起動完了時に失敗したCogを通知
# =========================================
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")

    if FAILED_COGS:
        notify_channels = [
            1416694818339291147,
            1399496192479592523,
        ]

        for cog, error in FAILED_COGS:
            msg = f"⚠️ Cog `{cog}` のロードに失敗しました！\n```py\n{error}\n```"
            for ch_id in notify_channels:
                channel = bot.get_channel(ch_id)
                if channel:
                    if len(msg) > 1900:
                        for i in range(0, len(msg), 1900):
                            await channel.send(msg[i:i+1900])
                    else:
                        await channel.send(msg)
# =========================================
# 非同期で実行
# =========================================
asyncio.run(main())
