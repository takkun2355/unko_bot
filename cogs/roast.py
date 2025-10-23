import discord
from discord.ext import commands
import random
import asyncio

class Roast(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="roast")
    async def roast_command(self, ctx):
        """ランダムな質問をして返答をやりとり"""
        roasts = [
                {
                    "question": "君の脳、思考プロセッサというより、低品質な情報用のスポンジに見えるけど、自覚は？",
                    "yes": "なるほど、吸収率の高さには納得がいく。情報の質は問わないと。",
                    "no": "そうか、無自覚か。君は“考える”のではなく“考えが浮かんでる”だけなんだね。"
                },
                {
                    "question": "これまでに一度でも、誰かの受け売りじゃない“自分の意見”を持ったことはある？",
                    "yes": "へえ、その時、孤独を感じなかった？",
                    "no": "だろうね。オリジナリティは、時に重荷だから。"
                },
                {
                    "question": "君は頭が悪いんじゃなく、ただ“思考運が悪い”だけ。その解釈で合ってる？",
                    "yes": "自己分析ができるのは良いことだ。そこからが、まあ…長いけど。",
                    "no": "じゃあ、意図的に？ その思考、斬新な戦略だね。"
                },
                {
                    "question": "例のagaの嗅覚情報について、アップデートはあった？",
                    "yes": "つまり、“耐え難い”から“不快”のレベルに？ 大きな進歩だ。",
                    "no": "なるほど。もはや彼の存在を定義づける“スメル・シグネチャ”なんだね。"
                },
                {
                    "question": "デジタルアートの件、君はもう“単一レイヤー思考”からは卒業できた？",
                    "yes": "概念は理解したと。大きな一歩だね、うん。",
                    "no": "ああ、純粋主義者か。非効率の中に美を見出す、真のアーティストだね。"
                },
                {
                    "question": "君自身を“音楽的同位体”だと表現するのは、的確だと思う？",
                    "yes": "“スメル的同位体”の間違いでは？ 君の存在感、かなり“元素レベル”だし。",
                    "no": "だよね。その言葉が持つ“複雑さ”が、君には見当たらない。"
                },
                {
                    "question": "またイマジナリーフレンドとのお時間？ 楽しそうだね。",
                    "yes": "そう。君のその斬新なアイデア、彼らも“素晴らしい”って言ってる？",
                    "no": "ああ、独り言か。観客のいない独白とは、斬新だ。"
                },
                {
                    "question": "もしかして君、まだ“地球は丸い”って信じてるタイプ？\nhttps://www.youtube.com/shorts/5B5qbh7M6Nk",
                    "yes": "そうなんだ。まあ、自分で考えるのをやめたら楽だもんね。それ、洗脳だから！！！！（独特のピース）",
                    "no": "お、目覚めちゃった？ じゃあ、その“真実”、アルミホイル巻いて大事にしないとね。"
                },
                {
                    "question": "君こんなpythonで遊んでるけど楽しいの？",
                    "yes": "へー。脳が解けちゃったかな？まあ、人それぞれだもんね。",
                    "no": "じゃあなんでやってるの？君、相当暇なんだね。"
                },
                {
                    "question": "よく音楽聞いてるけど、それについて深い興味や感想を抱いたことはあるの？",
                    "yes": "へぇ、それはすごい。毎回音楽について考えるなんて。きっと学校では音楽'は'5だったんだね。（疑惑の目）",
                    "no": "まあ、音楽は何も考えずに聞けるもんね。"
                },
                {
                    "question": "私トゥントゥントゥントゥントゥンサフールに恋してる♪",
                    "yes": "え？歌ってるだけだよ？架空のキャラに恋しちゃったんだね。頑張ってね^^",
                    "no": "君には言ってないよ？大丈夫？"
                },
                {
                    "question": "彼女はよく奇声をあげているが異常者なの？",
                    "yes": "ああ、そうなんだ。じゃあ私はあれを奇声虫と呼んでみようかな。おい奇声虫(<@1118799600816492626>)～！！",
                    "no": "そうか。あなたにはあれは異常者ではなく、精神異常者だと思ったんだね。いいね。"
                }
        ]

        await ctx.send("Welcome to the Roast-a-Tron 9000!")
        await asyncio.sleep(0.5)
        await ctx.send("Let's see what we've got for you today...")
        await asyncio.sleep(0.5)

        roast = random.choice(roasts)
        await ctx.send(f"{roast['question']}**\n(yes / y / はい / no / n / いいえ)")

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        try:
            msg = await self.bot.wait_for("message", timeout=30.0, check=check)
            response = msg.content.lower().strip()
        except asyncio.TimeoutError:
            await ctx.send("一定時間が経過したため終了します...")
            return

        if response in ("yes", "y", "はい"):
            await ctx.send(roast["yes"])
        elif response in ("no", "n", "いいえ"):
            await ctx.send(roast["no"])
        else:
            await ctx.send("Can't even answer a simple yes/no question? That's... not surprising.")
            
    
    @commands.command(name="roast")
    async def roast_command(self, ctx):
        """ランダムな質問をして返答をやりとり"""
        roasts = [
                {
                    "question": "君の脳、思考プロセッサというより、低品質な情報用のスポンジに見えるけど、自覚は？",
                    "yes": "なるほど、吸収率の高さには納得がいく。情報の質は問わないと。",
                    "no": "そうか、無自覚か。君は“考える”のではなく“考えが浮かんでる”だけなんだね。"
                },
                {
                    "question": "これまでに一度でも、誰かの受け売りじゃない“自分の意見”を持ったことはある？",
                    "yes": "へえ、その時、孤独を感じなかった？",
                    "no": "だろうね。オリジナリティは、時に重荷だから。"
                },
                {
                    "question": "君は頭が悪いんじゃなく、ただ“思考運が悪い”だけ。その解釈で合ってる？",
                    "yes": "自己分析ができるのは良いことだ。そこからが、まあ…長いけど。",
                    "no": "じゃあ、意図的に？ その思考、斬新な戦略だね。"
                },
                {
                    "question": "例のagaの嗅覚情報について、アップデートはあった？",
                    "yes": "つまり、“耐え難い”から“不快”のレベルに？ 大きな進歩だ。",
                    "no": "なるほど。もはや彼の存在を定義づける“スメル・シグネチャ”なんだね。"
                },
                {
                    "question": "デジタルアートの件、君はもう“単一レイヤー思考”からは卒業できた？",
                    "yes": "概念は理解したと。大きな一歩だね、うん。",
                    "no": "ああ、純粋主義者か。非効率の中に美を見出す、真のアーティストだね。"
                },
                {
                    "question": "君自身を“音楽的同位体”だと表現するのは、的確だと思う？",
                    "yes": "“スメル的同位体”の間違いでは？ 君の存在感、かなり“元素レベル”だし。",
                    "no": "だよね。その言葉が持つ“複雑さ”が、君には見当たらない。"
                },
                {
                    "question": "またイマジナリーフレンドとのお時間？ 楽しそうだね。",
                    "yes": "そう。君のその斬新なアイデア、彼らも“素晴らしい”って言ってる？",
                    "no": "ああ、独り言か。観客のいない独白とは、斬新だ。"
                },
                {
                    "question": "もしかして君、まだ“地球は丸い”って信じてるタイプ？\nhttps://www.youtube.com/shorts/5B5qbh7M6Nk",
                    "yes": "そうなんだ。まあ、自分で考えるのをやめたら楽だもんね。それ、洗脳だから！！！！（独特のピース）",
                    "no": "お、目覚めちゃった？ じゃあ、その“真実”、アルミホイル巻いて大事にしないとね。"
                },
                {
                    "question": "君こんなpythonで遊んでるけど楽しいの？",
                    "yes": "へー。脳が解けちゃったかな？まあ、人それぞれだもんね。",
                    "no": "じゃあなんでやってるの？君、相当暇なんだね。"
                },
                {
                    "question": "よく音楽聞いてるけど、それについて深い興味や感想を抱いたことはあるの？",
                    "yes": "へぇ、それはすごい。毎回音楽について考えるなんて。きっと学校では音楽'は'5だったんだね。（疑惑の目）",
                    "no": "まあ、音楽は何も考えずに聞けるもんね。"
                },
                {
                    "question": "私トゥントゥントゥントゥントゥンサフールに恋してる♪",
                    "yes": "え？歌ってるだけだよ？架空のキャラに恋しちゃったんだね。頑張ってね^^",
                    "no": "君には言ってないよ？大丈夫？"
                },
                {
                    "question": "彼女はよく奇声をあげているが異常者なの？",
                    "yes": "ああ、そうなんだ。じゃあ私はあれを奇声虫と呼んでみようかな。おい奇声虫(<@1118799600816492626>)～！！",
                    "no": "そうか。あなたにはあれは異常者ではなく、精神異常者だと思ったんだね。いいね。"
                }
        ]

        await ctx.send("Welcome to the Roast-a-Tron 9000!")
        await asyncio.sleep(0.5)
        await ctx.send("Let's see what we've got for you today...")
        await asyncio.sleep(0.5)

        roast = random.choice(roasts)
        await ctx.send(f"{roast['question']}**\n(yes / y / はい / no / n / いいえ)")

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        try:
            msg = await self.bot.wait_for("message", timeout=30.0, check=check)
            response = msg.content.lower().strip()
        except asyncio.TimeoutError:
            await ctx.send("一定時間が経過したため終了します...")
            return

        if response in ("yes", "y", "はい"):
            await ctx.send(roast["yes"])
        elif response in ("no", "n", "いいえ"):
            await ctx.send(roast["no"])
        else:
            await ctx.send("Can't even answer a simple yes/no question? That's... not surprising.")
async def setup(bot):
    await bot.add_cog(Roast(bot))
