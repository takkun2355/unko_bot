import discord
from discord.ext import commands

class TPStock(commands.Cog):
    """トイレットペーパー在庫シミュレーターCog"""

    def __init__(self, bot):
        self.bot = bot
        self.stock = 100  # 初期在庫

    @commands.command(name="tp_stock")
    async def check_stock(self, ctx):
        """現在のトイレットペーパー在庫を確認"""
        await ctx.send(f"🧻 現在の在庫: {self.stock} ロール紙")

    @commands.command(name="tp_buy")
    async def buy_tp(self, ctx, amount: int):
        """トイレットペーパーを購入"""
        if amount <= 0:
            await ctx.send("❌ 1以上の数を指定してください。")
            return
        if amount > self.stock:
            await ctx.send(f"❌ 在庫が足りません！現在の在庫: {self.stock}")
        else:
            self.stock -= amount
            await ctx.send(f"✅ {ctx.author.name} が {amount} ロール購入しました。在庫残り: {self.stock}")

    @commands.command(name="tp_restock")
    async def restock_tp(self, ctx, amount: int):
        """在庫補充（管理者用想定）"""
        if amount <= 0:
            await ctx.send("❌ 1以上の数を指定してください。")
            return
        self.stock += amount
        await ctx.send(f"🟢 在庫を {amount} ロール補充しました。在庫: {self.stock}")

# CogをBotに登録
async def setup(bot):
    await bot.add_cog(TPStock(bot))
