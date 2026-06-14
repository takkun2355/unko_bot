# cogs/music_full.py
import discord
from discord.ext import commands
import asyncio
import os

try:
    import yt_dlp as youtube_dl

    YTDLP_AVAILABLE = True
except ImportError:
    YTDLP_AVAILABLE = False

ytdl_format_options = {
    "format": "bestaudio/best",
    "quiet": True,
    "noplaylist": True,
}

# ffmpegはシステムPATHから検索。環境変数 FFMPEG_PATH で上書き可能
_ffmpeg_path = os.environ.get("FFMPEG_PATH", "ffmpeg")

ffmpeg_options = {
    "options": "-vn",
    "executable": _ffmpeg_path,
}

REACTION_EMOJIS = {
    "⏯": "pause_resume",
    "⏭": "skip",
    "⏹": "stop",
    "📜": "queue",
    "⏩": "forward_10",
    "⏪": "backward_10",
    "➖": "remove_song",
}


class music_full(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queues = {}  # サーバーID -> [URL_or_File]
        self.now_playing_messages = {}  # サーバーID -> メッセージ
        self.control_messages = {}  # サーバーID -> メッセージ
        self.current_time = {}  # サーバーID -> 秒
        # ytdlpはインスタンス生成時に初期化（モジュールレベルを避ける）
        if YTDLP_AVAILABLE:
            self.ytdl = youtube_dl.YoutubeDL(ytdl_format_options)
        else:
            self.ytdl = None

    # ------------------------
    # 再生処理
    # ------------------------
    async def play_next(self, ctx):
        server_id = ctx.guild.id
        queue = self.queues.get(server_id)
        if not queue or len(queue) == 0:
            if self.now_playing_messages.get(server_id):
                try:
                    await self.now_playing_messages[server_id].delete()
                except Exception:
                    pass
                self.now_playing_messages.pop(server_id, None)
            await ctx.send("✅ キューが空です。")
            if self.control_messages.get(server_id):
                try:
                    await self.control_messages[server_id].delete()
                except Exception:
                    pass
                self.control_messages.pop(server_id, None)
            return

        url_or_file = queue.pop(0)
        self.current_time[server_id] = 0

        if os.path.exists(url_or_file):
            source = discord.FFmpegOpusAudio(url_or_file, **ffmpeg_options)
            title = os.path.basename(url_or_file)
            thumbnail = None
            duration = 0
        else:
            if not self.ytdl:
                await ctx.send(
                    "❌ yt-dlpがインストールされていません。`pip install yt-dlp` を実行してください。"
                )
                return
            info = self.ytdl.extract_info(url_or_file, download=False)
            source = await discord.FFmpegOpusAudio.from_probe(
                info["url"], **ffmpeg_options
            )
            title = info.get("title", "Unknown")
            thumbnail = info.get("thumbnail")
            duration = info.get("duration", 0)

        ctx.voice_client.play(
            source,
            after=lambda e: asyncio.run_coroutine_threadsafe(
                self.play_next(ctx), self.bot.loop
            ),
        )

        bars_total = 5
        bar_str = "▰" + "▱" * (bars_total - 1)

        embed = discord.Embed(title="🎶 Now Playing", description=title, color=0x00FF00)
        if thumbnail:
            embed.set_thumbnail(url=thumbnail)
        embed.add_field(name="再生進行", value=bar_str, inline=False)
        if duration:
            embed.add_field(
                name="再生時間", value=f"0:{duration // 60:02d}", inline=False
            )

        np_msg = self.now_playing_messages.get(server_id)
        if np_msg:
            try:
                await np_msg.edit(embed=embed)
            except Exception:
                self.now_playing_messages[server_id] = await ctx.send(embed=embed)
        else:
            self.now_playing_messages[server_id] = await ctx.send(embed=embed)

        await self.add_control_reactions(
            self.now_playing_messages[server_id], server_id
        )

    # ------------------------
    # リアクション追加
    # ------------------------
    async def add_control_reactions(self, message, guild_id):
        for emoji in REACTION_EMOJIS.keys():
            await message.add_reaction(emoji)
        self.control_messages[guild_id] = message

    # ------------------------
    # リアクション操作
    # ------------------------
    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if user.bot:
            return
        guild_id = reaction.message.guild.id
        if self.control_messages.get(guild_id) != reaction.message:
            return

        ctx = await self.bot.get_context(reaction.message)
        action = REACTION_EMOJIS.get(str(reaction.emoji))
        queue = self.queues.get(guild_id, [])

        if action == "pause_resume":
            if ctx.voice_client and ctx.voice_client.is_playing():
                ctx.voice_client.pause()
                await reaction.message.channel.send("⏸ 一時停止")
            elif ctx.voice_client and ctx.voice_client.is_paused():
                ctx.voice_client.resume()
                await reaction.message.channel.send("▶ 再開")

        elif action == "skip":
            if ctx.voice_client and ctx.voice_client.is_playing():
                ctx.voice_client.stop()
                await reaction.message.channel.send("⏭ スキップしました")

        elif action == "stop":
            if ctx.voice_client:
                ctx.voice_client.stop()
                self.queues.pop(guild_id, None)
                await reaction.message.channel.send("⏹ 停止しました")
                if self.now_playing_messages.get(guild_id):
                    try:
                        await self.now_playing_messages[guild_id].delete()
                    except Exception:
                        pass
                    self.now_playing_messages.pop(guild_id, None)

        elif action == "queue":
            if not queue:
                await reaction.message.channel.send("❌ キューは空です")
            else:
                embed = discord.Embed(title="🎵 キュー一覧", color=0x00FF00)
                for i, url in enumerate(queue, start=1):
                    try:
                        info = self.ytdl.extract_info(url, download=False)
                        embed.add_field(
                            name=f"{i}. {info['title']}", value=url, inline=False
                        )
                    except Exception:
                        embed.add_field(
                            name=f"{i}. (取得失敗)", value=url, inline=False
                        )
                await reaction.message.channel.send(embed=embed)

        elif action == "forward_10":
            await reaction.message.channel.send("⏩ 10秒早送り (擬似)")

        elif action == "backward_10":
            await reaction.message.channel.send("⏪ 10秒巻き戻し (擬似)")

        elif action == "remove_song":
            if queue:
                removed = queue.pop(0)
                await reaction.message.channel.send(f"➖ キューから削除: {removed}")
            else:
                await reaction.message.channel.send("❌ キューは空です")

        await reaction.remove(user)

    # ------------------------
    # コマンド群
    # ------------------------
    @commands.command(name="join")
    async def join(self, ctx):
        if ctx.author.voice:
            await ctx.author.voice.channel.connect()
            await ctx.send("✅ VCに参加しました")
        else:
            await ctx.send("❌ VCに入ってから呼んでね")

    @commands.command(name="leave")
    async def leave(self, ctx):
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
            await ctx.send("👋 VCから抜けました")
            self.queues.pop(ctx.guild.id, None)
            if self.now_playing_messages.get(ctx.guild.id):
                try:
                    await self.now_playing_messages[ctx.guild.id].delete()
                except Exception:
                    pass
                self.now_playing_messages.pop(ctx.guild.id, None)
            if self.control_messages.get(ctx.guild.id):
                try:
                    await self.control_messages[ctx.guild.id].delete()
                except Exception:
                    pass
                self.control_messages.pop(ctx.guild.id, None)
        else:
            await ctx.send("❌ VCに入っていません")

    @commands.command(name="play")
    async def play(self, ctx, *, url_or_file):
        if not ctx.voice_client:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                await ctx.send("❌ VCに入ってから呼んでね")
                return
        self.queues.setdefault(ctx.guild.id, []).append(url_or_file)
        if not ctx.voice_client.is_playing() and not ctx.voice_client.is_paused():
            await self.play_next(ctx)
        else:
            await ctx.send("➕ キューに追加しました")

    @commands.command(name="queue")
    async def queue_cmd(self, ctx):
        queue = self.queues.get(ctx.guild.id, [])
        if not queue:
            await ctx.send("❌ キューは空です")
        else:
            embed = discord.Embed(title="🎵 キュー一覧", color=0x00FF00)
            for i, url in enumerate(queue, start=1):
                try:
                    info = self.ytdl.extract_info(url, download=False)
                    embed.add_field(
                        name=f"{i}. {info['title']}", value=url, inline=False
                    )
                except Exception:
                    embed.add_field(name=f"{i}. (取得失敗)", value=url, inline=False)
            await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(music_full(bot))
