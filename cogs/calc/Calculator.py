import logging

logger = logging.getLogger(__name__)
import math

from discord.ext import commands


class Calculator(commands.Cog):
    """拡張計算Cog（math + ^対応 + 関数一覧表示）"""

    def __init__(self, bot):
        self.bot = bot

        # 許可する関数・定数
        self.allowed_names = {
            "abs": abs,
            "round": round,
            "pow": pow,
            "int": int,
            "float": float,
            "sqrt": math.sqrt,
            "sin": math.sin,
            "cos": math.cos,
            "tan": math.tan,
            "log": math.log,
            "log10": math.log10,
            "pi": math.pi,
            "e": math.e,
        }

    @commands.command(name="calc")
    async def calculate(self, ctx, *, expression: str):
        """数式を計算して結果を返す（math対応 + ^で累乗）
        例: /calc 2^8 + sqrt(16)
        """
        try:
            expression = expression.replace("^", "**")  # '^'を累乗に変換
            result = eval(expression, {"__builtins__": {}}, self.allowed_names)
            await ctx.send(f"🧮 計算結果: {result}")
        except Exception as e:
            await ctx.send(f" 計算エラー: {e}")

    @commands.command(name="calc_help")
    async def calc_help(self, ctx):
        """使用可能な演算子・関数・定数一覧を表示"""
        funcs = ", ".join(sorted(k for k in self.allowed_names.keys() if k.isalpha()))
        constants = ", ".join(k for k in self.allowed_names.keys() if not k.isalpha())
        operators = "+, -, *, /, ^ (累乗), (), **"
        message = (
            f"🧮 **対応演算子:** {operators}\n"
            f"🔹 **使用可能関数:** {funcs}\n"
            f"🔹 **使用可能定数:** {constants}\n"
            f"例: `/calc 2^3 + sqrt(16)`"
        )
        await ctx.send(message)


# CogをBotに登録
async def setup(bot):
    await bot.add_cog(Calculator(bot))
