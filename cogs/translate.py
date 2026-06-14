import discord
from discord.ext import commands


class Translate(commands.Cog):
    """翻訳コマンド"""

    def __init__(self, bot):
        self.bot = bot
        try:
            from deep_translator import GoogleTranslator

            self.translator_class = GoogleTranslator
            self.available = True
        except Exception as e:
            self.translator_class = None
            self.available = False
            print(f"[WARNING] GoogleTranslator 初期化失敗: {e}")

    def error_embed(self, title, description):
        return discord.Embed(
            title=f"❌ {title}", description=description, color=discord.Color.red()
        )

    @commands.command(name="translate")
    async def translate(self, ctx, lang: str, *, text: str):
        if not self.available:
            await ctx.send(
                embed=self.error_embed("翻訳エラー", "翻訳機能は現在利用できません")
            )
            return
        try:
            translator = self.translator_class(source="auto", target=lang)
            translated_text = translator.translate(text)
            embed = discord.Embed(
                title="🌐 翻訳結果",
                description=f"**原文**: {text}\n**訳文 ({lang})**: {translated_text}",
                color=discord.Color.blue(),
            )
            await ctx.send(embed=embed)
        except ValueError:
            await ctx.send(
                embed=self.error_embed(
                    "翻訳失敗",
                    "サポートされていない言語コードです。\n`^^languages` で対応一覧を確認してください。",
                )
            )
        except Exception as e:
            await ctx.send(embed=self.error_embed("翻訳エラー", str(e)))

    @commands.command(name="languages")
    async def languages(self, ctx):
        if not self.available:
            await ctx.send(
                embed=self.error_embed("翻訳エラー", "翻訳機能は現在利用できません")
            )
            return
        try:
            langs = self.translator_class().get_supported_languages(as_dict=True)
            formatted = ", ".join([f"{code}" for code in langs.keys()])
            embed = discord.Embed(
                title="🌐 利用可能な言語コード一覧",
                description=formatted,
                color=discord.Color.green(),
            )
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(embed=self.error_embed("言語リスト取得失敗", str(e)))


async def setup(bot):
    try:
        await bot.add_cog(Translate(bot))
    except Exception as e:
        print(f"[ERROR] Translate Cog 読み込み失敗: {e}")
