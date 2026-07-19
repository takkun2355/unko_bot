import logging

logger = logging.getLogger(__name__)
import os
import sys

from discord.ext import commands


class BasicCommandCog(commands.Cog):
    """基本コマンドと管理コマンド"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def hello(self, ctx):
        await ctx.send("こんにちは！\nPython出身天才あがりちゃんです！")

    @commands.command()
    async def korosuzo(self, ctx):
        await ctx.send("えっ\nこわ杉")

    @commands.command()
    async def nanahoshimuseum(self, ctx):
        await ctx.send("[ナナホシ博物館](https://site.nanahoshi.akikukeo.f5.si)")

    @commands.command()
    async def agaurl(self, ctx):
        await ctx.send(
            "[aga youtube](https://www.youtube.com/@アヒルA)\n[aga pixiv](https://www.pixiv.net/users/111052500)\n[aga X](https://x.com/Chaba_A15)\n[aga tiktok](https://www.tiktok.com/@user1145278799555?_d=secCgYIASAHKAESPgo8Klpd2eBULMnb7BngVy5MzohMfr981zNGeo9UbLzBnENNULjce3pYjcTspOtgRrRyjEoOEjon1Ghq53xaGgA%3D&_r=1&_svg=1&checksum=426db1e6e29cc5f18e111c23420f287d27207153796f5c950724d310c01b3ae6&item_author_type=1&sec_uid=MS4wLjABAAAAD7eNzJyIyitQ6tVAggvMKfPQDGd98ylhT8DAEJvZ9YPJZk6qvq-SUaVnRt0egD4q&sec_user_id=MS4wLjABAAAAD7eNzJyIyitQ6tVAggvMKfPQDGd98ylhT8DAEJvZ9YPJZk6qvq-SUaVnRt0egD4q&share_app_id=473824&share_author_id=7357291116108760065&share_link_id=f2ab9227-1cd4-430f-bd8d-13e394a3743c&share_scene=1&sharer_language=ja&social_share_type=5&source=h5_m&timestamp=1754023967&u_code=edgfe4e3eej344&ug_btm=b8727%2Cb7360&ugbiz_name=ACCOUNT&user_id=7357291116108760065&utm_campaign=client_share&utm_medium=android&utm_source=copy)"
        )

    @commands.command()
    async def agariurl(self, ctx):
        await ctx.send(
            "[aga youtube](https://www.youtube.com/@アヒルA)\n[aga pixiv](https://www.pixiv.net/users/111052500)\n[aga X](https://x.com/Chaba_A15)\n[aga tiktok](https://www.tiktok.com/@user1145278799555?_d=secCgYIASAHKAESPgo8Klpd2eBULMnb7BngVy5MzohMfr981zNGeo9UbLzBnENNULjce3pYjcTspOtgRrRyjEoOEjon1Ghq53xaGgA%3D&_r=1&_svg=1&checksum=426db1e6e29cc5f18e111c23420f287d27207153796f5c950724d310c01b3ae6&item_author_type=1&sec_uid=MS4wLjABAAAAD7eNzJyIyitQ6tVAggvMKfPQDGd98ylhT8DAEJvZ9YPJZk6qvq-SUaVnRt0egD4q&sec_user_id=MS4wLjABAAAAD7eNzJyIyitQ6tVAggvMKfPQDGd98ylhT8DAEJvZ9YPJZk6qvq-SUaVnRt0egD4q&share_app_id=473824&share_author_id=7357291116108760065&share_link_id=f2ab9227-1cd4-430f-bd8d-13e394a3743c&share_scene=1&sharer_language=ja&social_share_type=5&source=h5_m&timestamp=1754023967&u_code=edgfe4e3eej344&ug_btm=b8727%2Cb7360&ugbiz_name=ACCOUNT&user_id=7357291116108760065&utm_campaign=client_share&utm_medium=android&utm_source=copy)"
        )

    @commands.command()
    async def agarisns(self, ctx):
        await ctx.send(
            "[aga youtube](https://www.youtube.com/@アヒルA)\n[aga pixiv](https://www.pixiv.net/users/111052500)\n[aga X](https://x.com/Chaba_A15)\n[aga tiktok](https://www.tiktok.com/@user1145278799555?_d=secCgYIASAHKAESPgo8Klpd2eBULMnb7BngVy5MzohMfr981zNGeo9UbLzBnENNULjce3pYjcTspOtgRrRyjEoOEjon1Ghq53xaGgA%3D&_r=1&_svg=1&checksum=426db1e6e29cc5f18e111c23420f287d27207153796f5c950724d310c01b3ae6&item_author_type=1&sec_uid=MS4wLjABAAAAD7eNzJyIyitQ6tVAggvMKfPQDGd98ylhT8DAEJvZ9YPJZk6qvq-SUaVnRt0egD4q&sec_user_id=MS4wLjABAAAAD7eNzJyIyitQ6tVAggvMKfPQDGd98ylhT8DAEJvZ9YPJZk6qvq-SUaVnRt0egD4q&share_app_id=473824&share_author_id=7357291116108760065&share_link_id=f2ab9227-1cd4-430f-bd8d-13e394a3743c&share_scene=1&sharer_language=ja&social_share_type=5&source=h5_m&timestamp=1754023967&u_code=edgfe4e3eej344&ug_btm=b8727%2Cb7360&ugbiz_name=ACCOUNT&user_id=7357291116108760065&utm_campaign=client_share&utm_medium=android&utm_source=copy)"
        )

    @commands.command()
    async def agasns(self, ctx):
        await ctx.send(
            "[aga youtube](https://www.youtube.com/@アヒルA)\n[aga pixiv](https://www.pixiv.net/users/111052500)\n[aga X](https://x.com/Chaba_A15)\n[aga tiktok](https://www.tiktok.com/@user1145278799555?_d=secCgYIASAHKAESPgo8Klpd2eBULMnb7BngVy5MzohMfr981zNGeo9UbLzBnENNULjce3pYjcTspOtgRrRyjEoOEjon1Ghq53xaGgA%3D&_r=1&_svg=1&checksum=426db1e6e29cc5f18e111c23420f287d27207153796f5c950724d310c01b3ae6&item_author_type=1&sec_uid=MS4wLjABAAAAD7eNzJyIyitQ6tVAggvMKfPQDGd98ylhT8DAEJvZ9YPJZk6qvq-SUaVnRt0egD4q&sec_user_id=MS4wLjABAAAAD7eNzJyIyitQ6tVAggvMKfPQDGd98ylhT8DAEJvZ9YPJZk6qvq-SUaVnRt0egD4q&share_app_id=473824&share_author_id=7357291116108760065&share_link_id=f2ab9227-1cd4-430f-bd8d-13e394a3743c&share_scene=1&sharer_language=ja&social_share_type=5&source=h5_m&timestamp=1754023967&u_code=edgfe4e3eej344&ug_btm=b8727%2Cb7360&ugbiz_name=ACCOUNT&user_id=7357291116108760065&utm_campaign=client_share&utm_medium=android&utm_source=copy)"
        )

    @commands.command()
    @commands.is_owner()
    async def stop(self, ctx):
        await ctx.send("Botを終了します…")
        await self.bot.close()

    @commands.command()
    @commands.is_owner()
    async def restart(self, ctx):
        await ctx.send("Botを再起動します…")
        python = sys.executable
        os.execl(python, python, *sys.argv)


async def setup(bot):
    await bot.add_cog(BasicCommandCog(bot))
