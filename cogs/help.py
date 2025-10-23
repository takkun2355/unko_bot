import discord
from discord.ext import commands

class HelpCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.per_page = 10  # 1ページに表示するコマンド数
        self.help_data = self.load_help_data()
        
    def load_help_data(self):
        try:
            with open("command_help.txt", "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            return "ヘルプファイルが見つかりません。管理者に連絡してください。"
        
    def load_help_data(self):
        """txtファイルからコマンドデータを読み込む"""
        help_data = []
        with open("command_help.txt", "r", encoding="utf-8") as f:
            content = f.read()
        blocks = content.strip().split("\n\n")
        for block in blocks:
            lines = block.split("\n")
            cmd = lines[0].strip()
            desc = "\n".join(lines[1:])
            help_data.append((cmd, desc))
        return help_data

    def create_page(self, page_num: int):
        """Embedページを作成"""
        embed = discord.Embed(
            title="📖 コマンド一覧",
            description=f"ページ {page_num+1}/{(len(self.help_data)-1)//self.per_page+1}",
            color=discord.Color.blue()
        )
        start = page_num * self.per_page
        end = start + self.per_page
        for cmd, desc in self.help_data[start:end]:
            embed.add_field(name=cmd, value=desc, inline=False)
        return embed

    @commands.command(name="help")
    async def help_command(self, ctx, *, arg: str = None):
        if arg:  
            # 特定コマンドの詳細表示
            for cmd, desc in self.help_data:
                if arg.lower() in cmd.lower():
                    embed = discord.Embed(
                        title=f"📌 {cmd}",
                        description=desc,
                        color=discord.Color.green()
                    )
                    await ctx.send(embed=embed)
                    return
            await ctx.send(f"❌ `{arg}` というコマンドは見つかりませんでした。")
        else:
            # ページ付きヘルプ
            page = 0
            embed = self.create_page(page)
            message = await ctx.send(embed=embed)

            await message.add_reaction("⬅️")
            await message.add_reaction("➡️")

            def check(reaction, user):
                return (
                    user == ctx.author
                    and str(reaction.emoji) in ["⬅️", "➡️"]
                    and reaction.message.id == message.id
                )

            while True:
                try:
                    reaction, user = await self.bot.wait_for("reaction_add", timeout=60.0, check=check)
                except:
                    break

                if str(reaction.emoji) == "➡️" and (page+1)*self.per_page < len(self.help_data):
                    page += 1
                elif str(reaction.emoji) == "⬅️" and page > 0:
                    page -= 1

                await message.clear_reactions()
                embed = self.create_page(page)
                await message.edit(embed=embed)
                await message.add_reaction("⬅️")
                await message.add_reaction("➡️")

async def setup(bot):
    await bot.add_cog(HelpCog(bot))
