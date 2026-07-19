import datetime
import logging

logger = logging.getLogger(__name__)
import datetime

import pytz  # pip install pytz
from discord.ext import commands


class WorldClock(commands.Cog):
    """世界時計Cog"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="time")
    async def world_time(self, ctx, city: str):
        """都市名を指定して現地時間を返す
        例: /time Tokyo
        """
        city_map = {
            # 日本（Tokyo）
            "Tokyo": "Asia/Tokyo",
            "TOKYO": "Asia/Tokyo",
            "tokyo": "Asia/Tokyo",
            "トウキョウ": "Asia/Tokyo",
            "とうきょう": "Asia/Tokyo",
            "toukyou": "Asia/Tokyo",
            "to-kyo-": "Asia/Tokyo",
            "東京": "Asia/Tokyo",
            "日本": "Asia/Tokyo",
            "nihon": "Asia/Tokyo",
            "にほん": "Asia/Tokyo",
            "二ホン": "Asia/Tokyo",
            "ジャパン": "Asia/Tokyo",
            "Japan": "Asia/Tokyo",
            "じゃぱん": "Asia/Tokyo",
            # イギリス（London）
            "London": "Europe/London",
            "LONDON": "Europe/London",
            "london": "Europe/London",
            "ロンドン": "Europe/London",
            "ろんどん": "Europe/London",
            "England": "Europe/London",
            "イングランド": "Europe/London",
            "イギリス": "Europe/London",
            "UK": "Europe/London",
            "United_Kingdom": "Europe/London",
            # フランス（Paris）
            "Paris": "Europe/Paris",
            "PARIS": "Europe/Paris",
            "paris": "Europe/Paris",
            "パリ": "Europe/Paris",
            "ふらんす": "Europe/Paris",
            "フランス": "Europe/Paris",
            "France": "Europe/Paris",
            # 韓国（Seoul）
            "Seoul": "Asia/Seoul",
            "SEOUL": "Asia/Seoul",
            "seoul": "Asia/Seoul",
            "ソウル": "Asia/Seoul",
            "서울": "Asia/Seoul",
            "大韓民国": "Asia/Seoul",
            "대한민국": "Asia/Seoul",
            "Korea": "Asia/Seoul",
            "韓国": "Asia/Seoul",
            # アメリカ（New York）
            "New York": "America/New_York",
            "new york": "America/New_York",
            "NEW YORK": "America/New_York",
            "ニューヨーク": "America/New_York",
            "にゅーよーく": "America/New_York",
            "USA": "America/New_York",
            "America": "America/New_York",
            "アメリカ": "America/New_York",
            "米国": "America/New_York",
            # カナダ（Toronto）
            "Toronto": "America/Toronto",
            "toronto": "America/Toronto",
            "トロント": "America/Toronto",
            "カナダ": "America/Toronto",
            "Canada": "America/Toronto",
            # 中国（Beijing）
            "Beijing": "Asia/Shanghai",
            "北京": "Asia/Shanghai",
            "ペキン": "Asia/Shanghai",
            "China": "Asia/Shanghai",
            "中国": "Asia/Shanghai",
            "zhongguo": "Asia/Shanghai",
            # 台湾（Taipei）
            "Taipei": "Asia/Taipei",
            "台北": "Asia/Taipei",
            "たいぺい": "Asia/Taipei",
            "台湾": "Asia/Taipei",
            "taiwan": "Asia/Taipei",
            # 香港（Hong Kong）
            "Hong Kong": "Asia/Hong_Kong",
            "香港": "Asia/Hong_Kong",
            "ほんこん": "Asia/Hong_Kong",
            # シンガポール
            "Singapore": "Asia/Singapore",
            "シンガポール": "Asia/Singapore",
            "しんがぽーる": "Asia/Singapore",
            "Singapura": "Asia/Singapore",  # マレー語表記
            # インド（New Delhi）
            "New Delhi": "Asia/Kolkata",
            "Delhi": "Asia/Kolkata",
            "インド": "Asia/Kolkata",
            "India": "Asia/Kolkata",
            "にゅーでりー": "Asia/Kolkata",
            "नई_दिल्ली": "Asia/Kolkata",  # ニューデリー（ヒンディー語）
            # インドネシア（Jakarta）
            "Jakarta": "Asia/Jakarta",
            "ジャカルタ": "Asia/Jakarta",
            "インドネシア": "Asia/Jakarta",
            "Indonesia": "Asia/Jakarta",
            # タイ（Bangkok）
            "Bangkok": "Asia/Bangkok",
            "バンコク": "Asia/Bangkok",
            "たい": "Asia/Bangkok",
            "タイ": "Asia/Bangkok",
            "Thailand": "Asia/Bangkok",
            "กรุงเทพฯ": "Asia/Bangkok",  # バンコク
            # オーストラリア（Sydney）
            "Sydney": "Australia/Sydney",
            "シドニー": "Australia/Sydney",
            "オーストラリア": "Australia/Sydney",
            "Australia": "Australia/Sydney",
            # ロシア（Moscow）
            "Moscow": "Europe/Moscow",
            "モスクワ": "Europe/Moscow",
            "ロシア": "Europe/Moscow",
            "Russia": "Europe/Moscow",
            "Москва": "Europe/Moscow",  # モスクワ（キリル文字）
            # ドイツ（Berlin）
            "Berlin": "Europe/Berlin",
            "ベルリン": "Europe/Berlin",
            "ドイツ": "Europe/Berlin",
            "Germany": "Europe/Berlin",
            # イタリア（Rome）
            "Rome": "Europe/Rome",
            "ローマ": "Europe/Rome",
            "イタリア": "Europe/Rome",
            "Italy": "Europe/Rome",
            "Roma": "Europe/Rome",
            # スペイン（Madrid）
            "Madrid": "Europe/Madrid",
            "マドリード": "Europe/Madrid",
            "スペイン": "Europe/Madrid",
            "Spain": "Europe/Madrid",
            # オランダ（Amsterdam）
            "Amsterdam": "Europe/Amsterdam",
            "アムステルダム": "Europe/Amsterdam",
            "オランダ": "Europe/Amsterdam",
            "Netherlands": "Europe/Amsterdam",
            # スイス（Zurich）
            "Zurich": "Europe/Zurich",
            "チューリッヒ": "Europe/Zurich",
            "スイス": "Europe/Zurich",
            "Switzerland": "Europe/Zurich",
            "Zürich": "Europe/Zurich",
            # トルコ（Istanbul）
            "Istanbul": "Europe/Istanbul",
            "イスタンブール": "Europe/Istanbul",
            "トルコ": "Europe/Istanbul",
            "Turkey": "Europe/Istanbul",
            "İstanbul": "Europe/Istanbul",
            # UAE（Dubai）
            "Dubai": "Asia/Dubai",
            "ドバイ": "Asia/Dubai",
            "アラブ首長国連邦": "Asia/Dubai",
            "UAE": "Asia/Dubai",
            # 南アフリカ（Cape Town）
            "Cape Town": "Africa/Johannesburg",
            "ケープタウン": "Africa/Johannesburg",
            "南アフリカ": "Africa/Johannesburg",
            "South_Africa": "Africa/Johannesburg",
            "Kaapstad": "Africa/Johannesburg",  # アフリカーンス語（ケープタウン）
            # ブラジル（São Paulo）
            "São_Paulo": "America/Sao_Paulo",
            "Sao_Paulo": "America/Sao_Paulo",
            "サンパウロ": "America/Sao_Paulo",
            "ブラジル": "America/Sao_Paulo",
            "Brazil": "America/Sao_Paulo",  # ポルトガル語
            # メキシコ（Mexico City）
            "Mexico City": "America/Mexico_City",
            "メキシコシティ": "America/Mexico_City",
            "メキシコ": "America/Mexico_City",
            "Mexico": "America/Mexico_City",
            "Ciudad_de_México": "America/Mexico_City",  # スペイン語
            # エジプト（Cairo）
            "Cairo": "Africa/Cairo",
            "カイロ": "Africa/Cairo",
            "エジプト": "Africa/Cairo",
            "Egypt": "Africa/Cairo",
            "القاهرة": "Africa/Cairo",  # カイロ（アラビア語）
            # サウジアラビア（Riyadh）
            "Riyadh": "Asia/Riyadh",
            "リヤド": "Asia/Riyadh",
            "サウジアラビア": "Asia/Riyadh",
            "Saudi Arabia": "Asia/Riyadh",
            "الرياض": "Asia/Riyadh",  # リヤド（アラビア語）
        }

        map = {
            # 日本 🇯🇵
            "東京": "Asia/Tokyo",
            # 韓国 🇰🇷
            "서울": "Asia/Seoul",
            # 中国 🇨🇳
            "北京": "Asia/Shanghai",
            # 台湾 🇹🇼
            "台北": "Asia/Taipei",
            # 香港 🇭🇰
            "香港": "Asia/Hong_Kong",
            # タイ 🇹🇭
            "กรุงเทพฯ": "Asia/Bangkok",  # バンコク
            # インド 🇮🇳
            "नई_दिल्ली": "Asia/Kolkata",  # ニューデリー（ヒンディー語）
            # インドネシア 🇮🇩
            "Jakarta": "Asia/Jakarta",  # インドネシア語でも同じ表記
            # シンガポール 🇸🇬
            "Singapura": "Asia/Singapore",  # マレー語表記
            # オーストラリア 🇦🇺
            "Sydney": "Australia/Sydney",  # 英語（公用語）
            # イギリス 🇬🇧
            "London": "Europe/London",
            # フランス 🇫🇷
            "Paris": "Europe/Paris",
            # ドイツ 🇩🇪
            "Berlin": "Europe/Berlin",
            # イタリア 🇮🇹
            "Roma": "Europe/Rome",
            # スペイン 🇪🇸
            "Madrid": "Europe/Madrid",
            # オランダ 🇳🇱
            "Amsterdam": "Europe/Amsterdam",
            # スイス 🇨🇭
            "Zürich": "Europe/Zurich",
            # トルコ 🇹🇷
            "İstanbul": "Europe/Istanbul",
            # ロシア 🇷🇺
            "Москва": "Europe/Moscow",  # モスクワ（キリル文字）
            # アメリカ 🇺🇸
            "New_York": "America/New_York",  # 英語（公用語）
            # カナダ 🇨🇦
            "Toronto": "America/Toronto",  # 英語（公用語）
            # ブラジル 🇧🇷
            "São_Paulo": "America/Sao_Paulo",  # ポルトガル語
            # メキシコ 🇲🇽
            "Ciudad_de_México": "America/Mexico_City",  # スペイン語
            # エジプト 🇪🇬
            "القاهرة": "Africa/Cairo",  # カイロ（アラビア語）
            # サウジアラビア 🇸🇦
            "الرياض": "Asia/Riyadh",  # リヤド（アラビア語）
            # 南アフリカ 🇿🇦
            "Kaapstad": "Africa/Johannesburg",  # アフリカーンス語（ケープタウン）
        }

        tz_name = city_map.get(city)
        if not tz_name:
            await ctx.send(f"対応している都市は:\n・ {'\n・ '.join(map.keys())}")
            return

        tz = pytz.timezone(tz_name)
        now = datetime.now(tz)
        await ctx.send(f"🕒 {city}の現在時刻: {now.strftime('%Y-%m-%d %H:%M:%S')}")


# CogをBotに登録
async def setup(bot):
    await bot.add_cog(WorldClock(bot))
