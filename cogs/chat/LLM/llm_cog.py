import discord
from discord.ext import commands
import ctypes
import os

class LLMCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        # C/C++ライブラリのパス（Windows用）
        BASE_DIR = os.path.dirname(__file__)
        lib_path = os.path.abspath(os.path.join(BASE_DIR, "lib", "pseudo_llm.dll"))
        self.lib = ctypes.CDLL(lib_path)

        # 関数の型情報を設定
        self.lib.generate_response.argtypes = [ctypes.c_char_p]
        self.lib.generate_response.restype = ctypes.c_char_p

    @commands.command(name="AIChat")
    async def chat_command(self, ctx, *, user_text):
        """
        LLMにチャットするコマンド
        例: ^^AIChat こんにちは
        """
        # ここでLLM応答を生成（C関数呼び出し）
        resp_bytes = self.lib.generate_response(user_text.encode("utf-8"))
        
        if not resp_bytes:
            await ctx.send("LLMが空応答を返した")
            return

        resp_text = resp_bytes.decode("utf-8")

        # Discordに送信
        await ctx.send(resp_text)

async def setup(bot):
    await bot.add_cog(LLMCog(bot))