import discord
from discord.ext import commands


class UtilityURL(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        try:
            import pyshorteners

            self.s = pyshorteners.Shortener()
            self.available = True
        except Exception as e:
            self.s = None
            self.available = False
            print(f"[WARNING] pyshorteners初期化失敗: {e}")

    def error_embed(self, title, description):
        return discord.Embed(
            title=f"❌ {title}", description=description, color=discord.Color.red()
        )

    @commands.command(name="shorten")
    async def shorten(self, ctx, url: str):
        """URLを短縮"""
        if not self.available:
            await ctx.send(
                embed=self.error_embed("URL短縮エラー", "この機能は現在利用できません")
            )
            return
        try:
            short_url = self.s.tinyurl.short(url)
            embed = discord.Embed(
                title="🔗 短縮URL",
                description=f"**入力**: {url}\n**出力**: {short_url}",
                color=discord.Color.blue(),
            )
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(embed=self.error_embed("URL短縮エラー", str(e)))

    @commands.command(name="expand")
    async def expand(self, ctx, url: str):
        """短縮URLを展開"""
        if not self.available:
            await ctx.send(
                embed=self.error_embed("URL展開エラー", "この機能は現在利用できません")
            )
            return
        try:
            long_url = self.s.tinyurl.expand(url)
            embed = discord.Embed(
                title="🔍 URL展開",
                description=f"**入力**: {url}\n**出力**: {long_url}",
                color=discord.Color.green(),
            )
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(embed=self.error_embed("URL展開エラー", str(e)))


async def setup(bot):
    try:
        await bot.add_cog(UtilityURL(bot))
    except Exception as e:
        print(f"[ERROR] UtilityURL Cog 読み込み失敗: {e}")
