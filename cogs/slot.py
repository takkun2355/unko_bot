import random
from discord.ext import commands

class SlotGame(commands.Cog):
    """スロットゲーム"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def slot(self, ctx):
        symbols = ["🍒", "🍋", "🔔", "⭐", "7️⃣"]
        result = [random.choice(symbols) for _ in range(3)]
        display = " | ".join(result)
        await ctx.send(f"🎰 スロット！\n{display}")

        if len(set(result)) == 1:
            await ctx.send("🎉 大当たり！全部そろった！")
        elif len(set(result)) == 2:
            await ctx.send("👌 おしい！2つそろった！")
        else:
            await ctx.send("😢 はずれ…")

# async setup
async def setup(bot):
    await bot.add_cog(SlotGame(bot))
