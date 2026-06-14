import wikipedia
from discord.ext import commands

# 言語設定（日本語版）
wikipedia.set_lang("ja")


class WikipediaSearch(commands.Cog):
    """Wikipedia検索Cog"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="wiki")
    async def wiki_search(self, ctx, *, query: str):
        """Wikipediaでキーワードを検索して概要を返す
        例: /wiki Python
        """
        try:
            summary = wikipedia.summary(query, sentences=3)  # 3文だけ表示
            # Discordの文字数制限（約2000文字）対応
            if len(summary) > 1800:
                summary = summary[:1800] + "…"
            await ctx.send(f"🔍 **{query}** の概要:\n{summary}")
        except wikipedia.DisambiguationError as e:
            options = ", ".join(e.options[:5])  # 選択肢を5個だけ表示
            await ctx.send(f"⚠️ 曖昧なキーワードです。候補: {options}")
        except wikipedia.PageError:
            await ctx.send(f"❌ ページが見つかりません: {query}")
        except Exception as e:
            await ctx.send(f"❌ エラー: {e}")


# CogをBotに登録
async def setup(bot):
    await bot.add_cog(WikipediaSearch(bot))
