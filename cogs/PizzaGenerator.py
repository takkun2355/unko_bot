import discord
from discord.ext import commands
import random


class PizzaGenerator(commands.Cog):
    """ピザランダムトッピング生成Cog"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="pizza1")
    async def pizza(self, ctx):
        """
        ランダムでピザトッピングを生成
        """
        base = ["マルゲリータ", "チーズ", "ペパロニ", "ハム", "ベジタリアン"]
        toppings = [
            "オリーブ",
            "マッシュルーム",
            "パイナップル",
            "トマト",
            "コーン",
            "サラミ",
            "バジル",
            "チーズ増量",
            "アンチョビ",
        ]
        # ランダムでベース1つ＋トッピング2〜4個
        pizza_base = random.choice(base)
        pizza_topping1 = random.sample(toppings, k=random.randint(2, 4))
        pizza_description = f"🍕 ピザ: {pizza_base} + {' , '.join(pizza_topping1)}"
        await ctx.send(pizza_description)

    @commands.command(name="pizza2")
    async def pizza(self, ctx):
        """
        ランダムでピザトッピングを生成
        """
        base = ["マルゲリータ", "チーズ", "ペパロニ", "ハム", "ベジタリアン"]
        toppings = [
            "オリーブ",
            "マッシュルーム",
            "パイナップル",
            "トマト",
            "コーン",
            "サラミ",
            "バジル",
            "チーズ増量",
            "アンチョビ",
        ]
        # ランダムでベース1つ＋トッピング2〜4個
        pizza_base = random.choice(base)
        pizza_topping1 = random.sample(toppings, k=random.randint(2, 4))
        pizza_topping2 = random.sample(toppings, k=random.randint(2, 4))
        pizza_description = f"🍕 ピザ: {pizza_base} + {' , '.join(pizza_topping1)} + {' , '.join(pizza_topping2)}"
        await ctx.send(pizza_description)

    @commands.command(name="pizza3")
    async def pizza(self, ctx):
        """
        ランダムでピザトッピングを生成
        """
        base = ["マルゲリータ", "チーズ", "ペパロニ", "ハム", "ベジタリアン"]
        toppings = [
            "オリーブ",
            "マッシュルーム",
            "パイナップル",
            "トマト",
            "コーン",
            "サラミ",
            "バジル",
            "チーズ増量",
            "アンチョビ",
        ]
        # ランダムでベース1つ＋トッピング2〜4個
        pizza_base = random.choice(base)
        pizza_topping1 = random.sample(toppings, k=random.randint(2, 4))
        pizza_topping2 = random.sample(toppings, k=random.randint(2, 4))
        pizza_topping3 = random.sample(toppings, k=random.randint(2, 4))
        pizza_description = f"🍕 ピザ: {pizza_base} + {' , '.join(pizza_topping1)} + {' , '.join(pizza_topping2)} + {' , '.join(pizza_topping3)}"
        await ctx.send(pizza_description)

    @commands.command(name="pizza3")
    async def pizza(self, ctx):
        """
        ランダムでピザトッピングを生成
        """
        base = ["マルゲリータ", "チーズ", "ペパロニ", "ハム", "ベジタリアン"]
        toppings = [
            "オリーブ",
            "マッシュルーム",
            "パイナップル",
            "トマト",
            "コーン",
            "サラミ",
            "バジル",
            "チーズ増量",
            "アンチョビ",
        ]
        # ランダムでベース1つ＋トッピング2〜4個
        pizza_base = random.choice(base)
        pizza_topping1 = random.sample(toppings, k=random.randint(2, 4))
        pizza_topping2 = random.sample(toppings, k=random.randint(2, 4))
        pizza_topping3 = random.sample(toppings, k=random.randint(2, 4))
        pizza_description = f"🍕 ピザ: {pizza_base} + {' , '.join(pizza_topping1)} + {' , '.join(pizza_topping2)} + {' , '.join(pizza_topping3)}"
        await ctx.send(pizza_description)

    @commands.command(name="pizza4")
    async def pizza(self, ctx):
        """
        ランダムでピザトッピングを生成
        """
        base = ["マルゲリータ", "チーズ", "ペパロニ", "ハム", "ベジタリアン"]
        toppings = [
            "オリーブ",
            "マッシュルーム",
            "パイナップル",
            "トマト",
            "コーン",
            "サラミ",
            "バジル",
            "チーズ増量",
            "アンチョビ",
        ]
        # ランダムでベース1つ＋トッピング2〜4個
        pizza_base = random.choice(base)
        pizza_topping1 = random.sample(toppings, k=random.randint(2, 4))
        pizza_topping2 = random.sample(toppings, k=random.randint(2, 4))
        pizza_topping3 = random.sample(toppings, k=random.randint(2, 4))
        pizza_topping4 = random.sample(toppings, k=random.randint(2, 4))
        pizza_description = f"🍕 ピザ: {pizza_base} + {' , '.join(pizza_topping1)} + {' , '.join(pizza_topping2)} + {' , '.join(pizza_topping3)} + {' , '.join(pizza_topping4)}"
        await ctx.send(pizza_description)

    @commands.command(name="pizza5")
    async def pizza(self, ctx):
        """
        ランダムでピザトッピングを生成
        """
        base = ["マルゲリータ", "チーズ", "ペパロニ", "ハム", "ベジタリアン"]
        toppings = [
            "オリーブ",
            "マッシュルーム",
            "パイナップル",
            "トマト",
            "コーン",
            "サラミ",
            "バジル",
            "チーズ増量",
            "アンチョビ",
        ]
        # ランダムでベース1つ＋トッピング2〜4個
        pizza_base = random.choice(base)
        pizza_topping1 = random.sample(toppings, k=random.randint(2, 4))
        pizza_topping2 = random.sample(toppings, k=random.randint(2, 4))
        pizza_topping3 = random.sample(toppings, k=random.randint(2, 4))
        pizza_topping4 = random.sample(toppings, k=random.randint(2, 4))
        pizza_topping5 = random.sample(toppings, k=random.randint(2, 4))
        pizza_description = f"🍕 ピザ: {pizza_base} + {' , '.join(pizza_topping1)} + {' , '.join(pizza_topping2)} + {' , '.join(pizza_topping3)} + {' , '.join(pizza_topping4)} + {' , '.join(pizza_topping5)}"
        await ctx.send(pizza_description)

    @commands.command(name="pizza6")
    async def pizza(self, ctx):
        """
        ランダムでピザトッピングを生成
        """
        base = ["マルゲリータ", "チーズ", "ペパロニ", "ハム", "ベジタリアン"]
        toppings = [
            "オリーブ",
            "マッシュルーム",
            "パイナップル",
            "トマト",
            "コーン",
            "サラミ",
            "バジル",
            "チーズ増量",
            "アンチョビ",
        ]
        # ランダムでベース1つ＋トッピング2〜4個
        pizza_base = random.choice(base)
        pizza_topping1 = random.sample(toppings, k=random.randint(2, 4))
        pizza_topping2 = random.sample(toppings, k=random.randint(2, 4))
        pizza_topping3 = random.sample(toppings, k=random.randint(2, 4))
        pizza_topping4 = random.sample(toppings, k=random.randint(2, 4))
        pizza_topping5 = random.sample(toppings, k=random.randint(2, 4))
        pizza_topping6 = random.sample(toppings, k=random.randint(2, 4))
        pizza_description = f"🍕 ピザ: {pizza_base} + {' , '.join(pizza_topping1)} + {' , '.join(pizza_topping2)} + {' , '.join(pizza_topping3)} + {' , '.join(pizza_topping4)} + {' , '.join(pizza_topping5)} + {' , '.join(pizza_topping6)}"
        await ctx.send(pizza_description)

    @commands.command(name="pizza7")
    async def pizza(self, ctx):
        """
        ランダムでピザトッピングを生成
        """
        base = ["マルゲリータ", "チーズ", "ペパロニ", "ハム", "ベジタリアン"]
        toppings = [
            "オリーブ",
            "マッシュルーム",
            "パイナップル",
            "トマト",
            "コーン",
            "サラミ",
            "バジル",
            "チーズ増量",
            "アンチョビ",
        ]
        # ランダムでベース1つ＋トッピング2〜4個
        pizza_base = random.choice(base)
        pizza_topping1 = random.sample(toppings, k=random.randint(2, 4))
        pizza_topping2 = random.sample(toppings, k=random.randint(2, 4))
        pizza_topping3 = random.sample(toppings, k=random.randint(2, 4))
        pizza_topping4 = random.sample(toppings, k=random.randint(2, 4))
        pizza_topping5 = random.sample(toppings, k=random.randint(2, 4))
        pizza_topping6 = random.sample(toppings, k=random.randint(2, 4))
        pizza_topping7 = random.sample(toppings, k=random.randint(2, 4))
        pizza_description = f"🍕 ピザ: {pizza_base} + {' , '.join(pizza_topping1)} + {' , '.join(pizza_topping2)} + {' , '.join(pizza_topping3)} + {' , '.join(pizza_topping4)} + {' , '.join(pizza_topping5)} + {' , '.join(pizza_topping6)} + {' , '.join(pizza_topping7)}"
        await ctx.send(pizza_description)

    @commands.command(name="pizza8")
    async def pizza(self, ctx):
        """
        ランダムでピザトッピングを生成
        """
        base = ["マルゲリータ", "チーズ", "ペパロニ", "ハム", "ベジタリアン"]
        toppings = [
            "オリーブ",
            "マッシュルーム",
            "パイナップル",
            "トマト",
            "コーン",
            "サラミ",
            "バジル",
            "チーズ増量",
            "アンチョビ",
        ]
        # ランダムでベース1つ＋トッピング2〜4個
        pizza_base = random.choice(base)
        pizza_topping1 = random.sample(toppings, k=random.randint(2, 4))
        pizza_topping2 = random.sample(toppings, k=random.randint(2, 4))
        pizza_topping3 = random.sample(toppings, k=random.randint(2, 4))
        pizza_topping4 = random.sample(toppings, k=random.randint(2, 4))
        pizza_topping5 = random.sample(toppings, k=random.randint(2, 4))
        pizza_topping6 = random.sample(toppings, k=random.randint(2, 4))
        pizza_topping7 = random.sample(toppings, k=random.randint(2, 4))
        pizza_topping8 = random.sample(toppings, k=random.randint(2, 4))
        pizza_description = f"🍕 ピザ: {pizza_base} + {' , '.join(pizza_topping1)} + {' , '.join(pizza_topping2)} + {' , '.join(pizza_topping3)} + {' , '.join(pizza_topping4)} + {' , '.join(pizza_topping5)} + {' , '.join(pizza_topping6)} + {' , '.join(pizza_topping7)} + {' , '.join(pizza_topping8)}"
        await ctx.send(pizza_description)

    @commands.command(name="pizza9")
    async def pizza(self, ctx):
        """
        ランダムでピザトッピングを生成
        """
        base = ["マルゲリータ", "チーズ", "ペパロニ", "ハム", "ベジタリアン"]
        toppings = [
            "オリーブ",
            "マッシュルーム",
            "パイナップル",
            "トマト",
            "コーン",
            "サラミ",
            "バジル",
            "チーズ増量",
            "アンチョビ",
        ]
        # ランダムでベース1つ＋トッピング2〜4個
        pizza_base = random.choice(base)
        pizza_topping1 = random.sample(toppings, k=random.randint(2, 4))
        pizza_topping2 = random.sample(toppings, k=random.randint(2, 4))
        pizza_topping3 = random.sample(toppings, k=random.randint(2, 4))
        pizza_topping4 = random.sample(toppings, k=random.randint(2, 4))
        pizza_topping5 = random.sample(toppings, k=random.randint(2, 4))
        pizza_topping6 = random.sample(toppings, k=random.randint(2, 4))
        pizza_topping7 = random.sample(toppings, k=random.randint(2, 4))
        pizza_topping8 = random.sample(toppings, k=random.randint(2, 4))
        pizza_topping9 = random.sample(toppings, k=random.randint(2, 4))
        pizza_description = f"🍕 ピザ: {pizza_base} + {' , '.join(pizza_topping1)} + {' , '.join(pizza_topping2)} + {' , '.join(pizza_topping3)} + {' , '.join(pizza_topping4)} + {' , '.join(pizza_topping5)} + {' , '.join(pizza_topping6)} + {' , '.join(pizza_topping7)} + {' , '.join(pizza_topping8)} + {' , '.join(pizza_topping9)}"
        await ctx.send(pizza_description)

    @commands.command(name="pizza10")
    async def pizza(self, ctx):
        """
        ランダムでピザトッピングを生成
        """
        base = ["マルゲリータ", "チーズ", "ペパロニ", "ハム", "ベジタリアン"]
        toppings = [
            "オリーブ",
            "マッシュルーム",
            "パイナップル",
            "トマト",
            "コーン",
            "サラミ",
            "バジル",
            "チーズ増量",
            "アンチョビ",
        ]
        # ランダムでベース1つ＋トッピング2〜4個
        pizza_base = random.choice(base)
        pizza_topping1 = random.sample(toppings, k=random.randint(2, 4))
        pizza_topping2 = random.sample(toppings, k=random.randint(2, 4))
        pizza_topping3 = random.sample(toppings, k=random.randint(2, 4))
        pizza_topping4 = random.sample(toppings, k=random.randint(2, 4))
        pizza_topping5 = random.sample(toppings, k=random.randint(2, 4))
        pizza_topping6 = random.sample(toppings, k=random.randint(2, 4))
        pizza_topping7 = random.sample(toppings, k=random.randint(2, 4))
        pizza_topping8 = random.sample(toppings, k=random.randint(2, 4))
        pizza_topping9 = random.sample(toppings, k=random.randint(2, 4))
        pizza_topping10 = random.sample(toppings, k=random.randint(2, 4))
        pizza_description = f"🍕 ピザ: {pizza_base} + {' , '.join(pizza_topping1)} + {' , '.join(pizza_topping2)} + {' , '.join(pizza_topping3)} + {' , '.join(pizza_topping4)} + {' , '.join(pizza_topping5)} + {' , '.join(pizza_topping6)} + {' , '.join(pizza_topping7)} + {' , '.join(pizza_topping8)} + {' , '.join(pizza_topping9)} + {' , '.join(pizza_topping10)}"
        await ctx.send(pizza_description)


# CogをBotに登録
async def setup(bot):
    await bot.add_cog(PizzaGenerator(bot))
