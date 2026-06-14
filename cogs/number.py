import random
from discord.ext import commands


class NumberGame(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.number_games = {}

    @commands.command()
    async def start_number(self, ctx):
        answer = random.randint(1, 100)
        self.number_games[ctx.channel.id] = answer
        await ctx.send("🎲 数当てゲーム開始！ 1〜100の数字を当ててね！")

    @commands.command()
    async def guess(self, ctx, number: int):
        if ctx.channel.id not in self.number_games:
            await ctx.send(
                "まだゲームが始まっていないよ。`^^start_number` で開始してね。"
            )
            return

        answer = self.number_games[ctx.channel.id]

        if number < answer:
            await ctx.send("🔼 もっと大きい数字だよ！")
        elif number > answer:
            await ctx.send("🔽 もっと小さい数字だよ！")
        else:
            await ctx.send(f"🎉 正解！ {ctx.author.mention} が当てました！")
            del self.number_games[ctx.channel.id]


async def setup(bot):
    await bot.add_cog(NumberGame(bot))
