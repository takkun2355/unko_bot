import discord
from discord.ext import commands
import requests
from datetime import datetime, timedelta
from dateutil import parser

class Weather(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # 47都道府県のデータ（例: 緯度・経度・検索名）
        self.prefectures = {
            "北海道": {"lat": 43.06417, "lon": 141.34694,
                       "names": ["ほっかいどう","ホッカイドウ","北海道","Hokkaido"]},
            "青森県": {"lat": 40.82444, "lon": 140.74,
                       "names": ["あおもりけん","アオモリケン","青森","Aomori"]},
            "岩手県": {"lat": 39.70361, "lon": 141.1525,
                       "names": ["いわてけん","イワテケン","岩手","Iwate"]},
            "宮城県": {"lat": 38.26889, "lon": 140.87194,
                       "names": ["みやぎけん","ミヤギケン","宮城","Miyagi"]},
            "秋田県": {"lat": 39.71861, "lon": 140.1025,
                       "names": ["あきたけん","アキタケン","秋田","Akita"]},
            "山形県": {"lat": 38.24056, "lon": 140.36333,
                       "names": ["やまがたけん","ヤマガタケン","山形","Yamagata"]},
            "福島県": {"lat": 37.75, "lon": 140.46778,
                       "names": ["ふくしまけん","フクシマケン","福島","Fukushima"]},
            "茨城県": {"lat": 36.34139, "lon": 140.44667,
                       "names": ["いばらきけん","イバラキケン","茨城","Ibaraki"]},
            "栃木県": {"lat": 36.56583, "lon": 139.88361,
                       "names": ["とちぎけん","トチギケン","栃木","Tochigi"]},
            "群馬県": {"lat": 36.39111, "lon": 139.06083,
                       "names": ["ぐんまけん","グンマケン","群馬","Gunma"]},
            "埼玉県": {"lat": 35.85694, "lon": 139.64889,
                       "names": ["さいたまけん","サイタマケン","埼玉","Saitama"]},
            "千葉県": {"lat": 35.60472, "lon": 140.12333,
                       "names": ["ちばけん","チバケン","千葉","Chiba"]},
            "東京都": {"lat": 35.68944, "lon": 139.69167,
                       "names": ["とうきょうと","トウキョウト","東京","Tokyo","都","東京都"]},
            "神奈川県": {"lat": 35.44778, "lon": 139.6425,
                       "names": ["かながわけん","カナガワケン","神奈川","Kanagawa"]},
            "新潟県": {"lat": 37.90222, "lon": 139.02361,
                       "names": ["にいがたけん","ニイガタケン","新潟","Niigata"]},
            "富山県": {"lat": 36.69528, "lon": 137.21139,
                       "names": ["とやまけん","トヤマケン","富山","Toyama"]},
            "石川県": {"lat": 36.59444, "lon": 136.62556,
                       "names": ["いしかわけん","イシカワケン","石川","Ishikawa"]},
            "福井県": {"lat": 36.06528, "lon": 136.22194,
                       "names": ["ふくいけん","フクイケン","福井","Fukui"]},
            "山梨県": {"lat": 35.66389, "lon": 138.56833,
                       "names": ["やまなしけん","ヤマナシケン","山梨","Yamanashi"]},
            "長野県": {"lat": 36.65139, "lon": 138.18111,
                       "names": ["ながのけん","ナガノケン","長野","Nagano"]},
            "岐阜県": {"lat": 35.39111, "lon": 136.72222,
                       "names": ["ぎふけん","ギフケン","岐阜","Gifu"]},
            "静岡県": {"lat": 34.97556, "lon": 138.38278,
                       "names": ["しずおかけん","シズオカケン","静岡","Shizuoka"]},
            "愛知県": {"lat": 35.18028, "lon": 136.90667,
                       "names": ["あいちけん","アイチケン","愛知","Aichi"]},
            "三重県": {"lat": 34.73028, "lon": 136.50861,
                       "names": ["みえけん","ミエケン","三重","Mie"]},
            "滋賀県": {"lat": 35.00444, "lon": 135.86833,
                       "names": ["しがけん","シガケン","滋賀","Shiga"]},
            "京都府": {"lat": 35.02139, "lon": 135.75556,
                       "names": ["きょうとふ","キョウトフ","京都","Kyoto"]},
            "大阪府": {"lat": 34.68639, "lon": 135.52,
                       "names": ["おおさかふ","オオサカフ","大阪","Osaka"]},
            "兵庫県": {"lat": 34.69139, "lon": 135.18306,
                       "names": ["ひょうごけん","ヒョウゴケン","兵庫","Hyogo"]},
            "奈良県": {"lat": 34.68528, "lon": 135.83278,
                       "names": ["ならけん","ナラケン","奈良","Nara"]},
            "和歌山県": {"lat": 34.22611, "lon": 135.1675,
                       "names": ["わかやまけん","ワカヤマケン","和歌山","Wakayama"]},
            "鳥取県": {"lat": 35.5, "lon": 134.235,
                       "names": ["とっとりけん","トットリケン","鳥取","Tottori"]},
            "島根県": {"lat": 35.47222, "lon": 133.05056,
                       "names": ["しまねけん","シマネケン","島根","Shimane"]},
            "岡山県": {"lat": 34.66167, "lon": 133.935,
                       "names": ["おかやまけん","オカヤマケン","岡山","Okayama"]},
            "広島県": {"lat": 34.39639, "lon": 132.45944,
                       "names": ["ひろしまけん","ヒロシマケン","広島","Hiroshima"]},
            "山口県": {"lat": 34.18583, "lon": 131.47139,
                       "names": ["やまぐちけん","ヤマグチケン","山口","Yamaguchi"]},
            "徳島県": {"lat": 34.06583, "lon": 134.55944,
                       "names": ["とくしまけん","トクシマケン","徳島","Tokushima"]},
            "香川県": {"lat": 34.34028, "lon": 134.04333,
                       "names": ["かがわけん","カガワケン","香川","Kagawa"]},
            "愛媛県": {"lat": 33.84167, "lon": 132.76611,
                       "names": ["えひめけん","エヒメケン","愛媛","Ehime"]},
            "高知県": {"lat": 33.55972, "lon": 133.53111,
                       "names": ["こうちけん","コウチケン","高知","Kochi"]},
            "福岡県": {"lat": 33.60639, "lon": 130.41806,
                       "names": ["ふくおかけん","フクオカケン","福岡","Fukuoka"]},
            "佐賀県": {"lat": 33.24944, "lon": 130.29889,
                       "names": ["さがけん","サガケン","佐賀","Saga"]},
            "長崎県": {"lat": 32.74472, "lon": 129.87361,
                       "names": ["ながさきけん","ナガサキケン","長崎","Nagasaki"]},
            "熊本県": {"lat": 32.78972, "lon": 130.74167,
                       "names": ["くまもとけん","クマモトケン","熊本","Kumamoto"]},
            "大分県": {"lat": 33.23972, "lon": 131.60944,
                       "names": ["おおいたけん","オオイタケン","大分","Oita"]},
            "宮崎県": {"lat": 31.91111, "lon": 131.42389,
                       "names": ["みやざきけん","ミヤザキケン","宮崎","Miyazaki"]},
            "鹿児島県": {"lat": 31.56028, "lon": 130.55778,
                       "names": ["かごしまけん","カゴシマケン","鹿児島","Kagoshima"]},
            "沖縄県": {"lat": 26.2125, "lon": 127.68111,
                       "names": ["おきなわけん","オキナワケン","沖縄","Okinawa"]}
        }

        # 天気コードとアイコン
        self.weather_icons = {
            0: "☀️", 1: "🌤", 2: "⛅", 3: "🌥", 45: "🌫", 48: "🌫",
            51: "🌦", 53: "🌧", 55: "🌧", 56: "🌦", 57: "🌦",
            61: "🌧", 63: "🌧", 65: "🌧", 71: "🌨", 73: "🌨", 75: "❄️",
            80: "🌦", 81: "🌧", 82: "🌧", 95: "⛈", 96: "⛈", 99: "⛈"
        }

    def find_prefecture(self, city):
        city_lower = city.lower()
        for key, val in self.prefectures.items():
            all_names = val["names"] + [key]
            if city_lower in [n.lower() for n in all_names]:
                return val, key
        return None, None

    @commands.command()
    async def weather(self, ctx, *args):
        if not args:
            await ctx.send("❌ 都道府県名を指定してください！")
            return

        detailed = False
        if args[0].lower() == "details":
            detailed = True
            args = args[1:]
            if not args:
                await ctx.send("❌ Details モードでは都道府県名を指定してください！")
                return

        city = " ".join(args)
        pref, key_name = self.find_prefecture(city)
        if not pref:
            await ctx.send(f"❌ 都道府県 `{city}` が見つかりません！")
            return

        url = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={pref['lat']}&longitude={pref['lon']}&current_weather=true"
            f"&hourly=temperature_2m,relativehumidity_2m,precipitation,weathercode,windspeed_10m,winddirection_10m,pressure_msl"
            f"&timezone=Asia/Tokyo"
        )

        try:
            res = requests.get(url, timeout=10).json()
            cw = res.get("current_weather", {})
            if not cw:
                await ctx.send("❌ 現在の天気情報が取得できませんでした。")
                return

            # 現在の天気
            temp = cw.get("temperature")
            wind_speed = cw.get("windspeed")
            wind_dir = cw.get("winddirection")
            weather_code = cw.get("weathercode")
            pressure = cw.get("pressure")

            # 現在湿度取得
            humidity = None
            hourly = res.get("hourly", {})
            times = hourly.get("time", [])
            humidities = hourly.get("relativehumidity_2m", [])
            now_hour = datetime.now().replace(minute=0, second=0, microsecond=0)
            for t, h in zip(times, humidities):
                dt = parser.parse(t)
                if dt.hour == now_hour.hour and dt.date() == now_hour.date():
                    humidity = h
                    break

            icon = self.weather_icons.get(weather_code, "❓")

            msg = f"🌤 **{key_name} の現在の天気**\n"
            msg += f"気温: {temp}°C\n"
            msg += f"湿度: {humidity if humidity is not None else '不明'}%\n"
            msg += f"風速: {wind_speed} km/h\n"
            msg += f"風向: {wind_dir}°\n"
            msg += f"気圧: {pressure} hPa\n"
            msg += f"天気: {icon}\n"

            if detailed:
                # 詳細表示
                temps = hourly.get("temperature_2m", [])
                precs = hourly.get("precipitation", [])
                codes = hourly.get("weathercode", [])
                wind_speeds = hourly.get("windspeed_10m", [])
                wind_dirs = hourly.get("winddirection_10m", [])
                pressures = hourly.get("pressure_msl", [])
                humidities = hourly.get("relativehumidity_2m", [])

                msg += "\n📊 **詳細情報（今日・明日の6時間ごと）**\n"
                for t_str, temp_val, prec, code, ws, wd, pres, hum in zip(times, temps, precs, codes, wind_speeds, wind_dirs, pressures, humidities):
                    dt = parser.parse(t_str)
                    if dt.date() in [datetime.today().date(), (datetime.today() + timedelta(days=1)).date()]:
                        hour_label = dt.strftime("%H:%M")
                        icon_hour = self.weather_icons.get(code, "❓")
                        msg += (f"{dt.date()} {hour_label} - {temp_val}°C / 降水: {prec}mm / 湿度: {hum}% / "
                                f"風速: {ws}km/h 風向: {wd}° / 気圧: {pres}hPa {icon_hour}\n")

            await ctx.send(msg)

        except Exception as e:
            await ctx.send(f"❌ 天気情報の取得に失敗しました: {e}")

async def setup(bot):
    await bot.add_cog(Weather(bot))
