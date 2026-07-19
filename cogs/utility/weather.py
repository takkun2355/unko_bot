import logging

logger = logging.getLogger(__name__)
import asyncio
import json
import pathlib
import traceback
from datetime import datetime, timedelta, timezone

import aiohttp
from dateutil import parser
from discord.ext import commands


class Weather(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.prefectures = {}
        self.load_prefectures()

        # 天気コードとアイコン
        self.weather_icons = {
            0: "☀",
            1: "🌤",
            2: "⛅",
            3: "🌥",
            45: "🌫",
            48: "🌫",
            51: "🌦",
            53: "🌧",
            55: "🌧",
            56: "🌦",
            57: "🌦",
            61: "🌧",
            63: "🌧",
            65: "🌧",
            71: "🌨",
            73: "🌨",
            75: "❄",
            80: "🌦",
            81: "🌧",
            82: "🌧",
            95: "⛈",
            96: "⛈",
            99: "⛈",
        }

        # WMO天気コードに対応する日本語名称
        self.weather_names = {
            0: "快晴",
            1: "晴れ",
            2: "一部曇り",
            3: "曇り",
            45: "霧",
            48: "着氷性の霧",
            51: "軽度の霧雨",
            53: "中程度の霧雨",
            55: "重度の霧雨",
            56: "軽度の凍てつく霧雨",
            57: "重度の凍てつく霧雨",
            61: "小雨",
            63: "雨",
            65: "大雨",
            66: "軽度の凍る雨",
            67: "重度の凍る雨",
            71: "小雪",
            73: "雪",
            75: "大雪",
            77: "霧雪",
            80: "小雨（にわか雨）",
            81: "にわか雨",
            82: "激しいにわか雨",
            85: "軽いにわか雪",
            86: "激しいにわか雪",
            95: "雷雨",
            96: "軽度の雹を伴う雷雨",
            99: "重度の雹を伴う雷雨",
        }

        # 気象庁の警報コードマッピング
        self.jma_warning_codes = {
            "02": "大雨注意報",
            "03": "大雨警報",
            "04": "洪水注意報",
            "05": "洪水警報",
            "06": "強風注意報",
            "07": "暴風警報",
            "08": "大雪注意報",
            "09": "大雪警報",
            "10": "波浪注意報",
            "11": "波浪警報",
            "12": "高潮注意報",
            "13": "高潮警報",
            "14": "雷注意報",
            "15": "融雪注意報",
            "16": "濃霧注意報",
            "17": "乾燥注意報",
            "18": "なだれ注意報",
            "19": "低温注意報",
            "20": "霜注意報",
            "21": "着氷注意報",
            "22": "着雪注意報",
            "23": "送電線等着雪注意報",
            "32": "大雨特別警報",
            "33": "大雪特別警報",
            "35": "暴風特別警報",
            "36": "波浪特別警報",
            "37": "高潮特別警報",
        }

    def load_prefectures(self):
        """weather.json から地域データを読み込む"""
        file_path = "weather.json"
        if pathlib.Path(file_path).exists():
            try:
                with pathlib.Path(file_path).open(encoding="utf-8") as f:
                    self.prefectures = json.load(f)
                    logger.info("[Weather] Loaded prefectures data successfully from weather.json.")
            except Exception:
                logger.info("[Weather] ERROR: Failed to load weather.json.")
                logger.info(traceback.format_exc())
        else:
            logger.info(
                "[Weather] ERROR: weather.json not found! Please make sure weather.json exists in the root directory."
            )

    def find_prefecture(self, city):
        city_lower = city.lower()

        # 完全一致優先
        for key, val in self.prefectures.items():
            all_names = val.get("names", []) + [key]

            for n in all_names:
                if city_lower == n.lower():
                    return val, key

        # 部分一致
        for key, val in self.prefectures.items():
            all_names = val.get("names", []) + [key]

            for n in all_names:
                n_lower = n.lower()

                if city_lower in n_lower:
                    return val, key

        return None, None

    def get_wind_direction_jp(self, deg):
        """風向の角度(数値)から日本語の16方位に変換"""
        if deg is None:
            return "不明"
        directions = [
            "北",
            "北北東",
            "北東",
            "東北東",
            "東",
            "東南東",
            "南東",
            "南南東",
            "南",
            "南南西",
            "南西",
            "西南西",
            "西",
            "西北西",
            "北西",
            "北北西",
        ]
        idx = int((deg + 11.25) % 360 / 22.5)
        return directions[idx]

    async def fetch_weather_api(self, session, url, name, pref_data):
        """Open-MeteoのAPIを非同期で取得"""
        try:
            async with session.get(url, timeout=10) as resp:
                resp.raise_for_status()
                data = await resp.json()
                return {"name": name, "data": data, "pref": pref_data}
        except Exception:
            logger.info(f"[Weather Debug] Open-Meteo fetch failed for {name}:")
            logger.info(traceback.format_exc())
            return None

    async def get_jma_warnings(self, session, jma_code, name):
        """気象庁APIから警報・注意報を非同期取得し分類"""
        url = f"https://www.jma.go.jp/bosai/warning/data/warning/{jma_code}.json"
        try:
            async with session.get(url, timeout=5) as resp:
                res = await resp.json()
                warnings = []
                advisories = []
                for item in res:
                    for area_group in item.get("areaTypes", []):
                        if area_group.get("areaType") in ["class10s", "class20s"]:
                            for area in area_group.get("areas", []):
                                for warn in area.get("warnings", []):
                                    code = str(warn.get("code")).zfill(2)
                                    status = warn.get("status")
                                    if status in ["発表", "継続", "特別警報から警報"]:
                                        wname = self.jma_warning_codes.get(code)
                                        if wname:
                                            if "警報" in wname or "特別警報" in wname:
                                                if wname not in warnings:
                                                    warnings.append(wname)
                                            else:
                                                if wname not in advisories:
                                                    advisories.append(wname)
                return {"name": name, "warnings": warnings, "advisories": advisories}
        except Exception:
            logger.info(f"[Weather Debug] JMA Warning API error for code {jma_code} ({name}):")
            logger.info(traceback.format_exc())
            return {"name": name, "warnings": [], "advisories": []}

    async def get_typhoon_info(self, session):
        """気象庁の「防災台風データAPI」から台風情報をJMA公式仕様で正確に取得"""
        list_url = "https://www.jma.go.jp/bosai/typhoon/data/tc_list.json"
        try:
            async with session.get(list_url, timeout=5) as resp:
                resp.raise_for_status()
                res_list = await resp.json()
                if not res_list or not isinstance(res_list, list):
                    return None

                typhoons = []
                for tc in res_list:
                    event_id = tc.get("eventId")
                    if not event_id:
                        continue

                    # 各台風の最新の解析データ（JMA specifications）を取得
                    spec_url = f"https://www.jma.go.jp/bosai/typhoon/data/{event_id}/specifications.json"
                    async with session.get(spec_url, timeout=5) as spec_resp:
                        spec_resp.raise_for_status()
                        specs = await spec_resp.json()
                        if not specs or not isinstance(specs, list):
                            continue

                        # part -> jp が "実況" になっているものを最新の実況値として特定
                        latest_spec = None
                        for spec in specs:
                            part_data = spec.get("part", {})
                            if isinstance(part_data, dict) and part_data.get("jp") == "実況":
                                latest_spec = spec
                                break
                        if not latest_spec:
                            latest_spec = specs[0]

                        # 台風番号の特定
                        tc_number = event_id[-2:]  # 例: "TC2606" -> 6号
                        try:
                            num = int(tc_number)
                        except Exception:
                            num = tc_number

                        # 台風名（英語表記とかな表記をマージ）
                        name = tc.get("name", "Unnamed")
                        name_kana = tc.get("nameKana", "")
                        display_name = f"{name} ({name_kana})" if name_kana else name

                        # 気圧の取得（正確な気象庁階層: pressure -> center -> hPa）
                        pressure_data = latest_spec.get("pressure", {})
                        pressure = "不明"
                        if isinstance(pressure_data, dict):
                            center_data = pressure_data.get("center", {})
                            if isinstance(center_data, dict):
                                pressure = center_data.get("hPa", "不明")

                        # 風速の取得（正確な気象庁階層: maximumWind -> sustained -> m/s）
                        max_wind_data = latest_spec.get("maximumWind", {})
                        wind_ms = 0
                        if isinstance(max_wind_data, dict):
                            sustained_data = max_wind_data.get("sustained", {})
                            if isinstance(sustained_data, dict):
                                wind_ms = sustained_data.get("m/s", 0)

                        wind_kmh = round(wind_ms * 3.6, 1)

                        typhoons.append({
                            "num": num,
                            "name": display_name,
                            "pressure": pressure,
                            "wind_ms": wind_ms,
                            "wind_kmh": wind_kmh,
                        })
                return typhoons
        except Exception:
            logger.info("[Weather Debug] JMA Typhoon API error (New Endpoint Parser):")
            logger.info(traceback.format_exc())
            return None

    async def send_long_message(self, ctx, text):
        """文字数制限対策としてのメッセージ分割送信"""
        if not text or not text.strip():
            return
        for i in range(0, len(text), 1900):
            await ctx.send(text[i : i + 1900])

    @commands.command()
    async def weather(self, ctx, *args):
        if not self.prefectures:
            await ctx.send(" 地域データが読み込まれていません。weather.jsonが正しく配置されているか確認してください。")
            return

        try:
            JST = timezone(timedelta(hours=9))
            now_jst = datetime.now(JST)

            detailed = False
            is_japan = False

            if not args:
                is_japan = True
            else:
                args_list = list(args)
                if args_list[0].lower() == "details":
                    detailed = True
                    args_list = args_list[1:]

                if not args_list:
                    is_japan = True
                else:
                    city = " ".join(args_list)
                    japan_aliases = [
                        "日本",
                        "japan",
                        "にほん",
                        "ニホン",
                        "にっぽん",
                        "ニッポン",
                        "ﾆﾎﾝ",
                        "ﾆｯﾎﾟﾝ",
                        "nihon",
                        "nippon",
                    ]
                    if city.lower() in japan_aliases:
                        is_japan = True
                    else:
                        pref, key_name = self.find_prefecture(city)
                        if not pref:
                            await ctx.send(f" 地名 `{city}` に該当する都道府県が見つかりません！")
                            return

            # 「日本」指定時は、東京、大阪、愛知、福岡の4拠点を対象にする
            if is_japan:
                japan_data = self.prefectures.get("日本", {})
                query_cities = japan_data.get("display_prefectures", ["東京都", "大阪府", "福岡県", "愛知県"])
            else:
                if pref.get("type") == "region":
                    query_cities = pref.get("children", [])

                    if not query_cities:
                        await ctx.send(" 地域に都道府県が登録されていません")
                        return
                else:
                    query_cities = [key_name]

            async with aiohttp.ClientSession() as session:
                # 天気データの並行取得タスク
                weather_tasks = []
                for cname in query_cities:
                    pref_data = self.prefectures.get(cname)

                    if not pref_data:
                        continue

                    if "lat" not in pref_data or "lon" not in pref_data:
                        continue

                    url = (
                        f"https://api.open-meteo.com/v1/forecast?"
                        f"latitude={pref_data['lat']}"
                        f"&longitude={pref_data['lon']}"
                        f"&current=temperature_2m,relative_humidity_2m,"
                        f"weather_code,wind_speed_10m,wind_direction_10m"
                        f"&hourly=temperature_2m,relative_humidity_2m,"
                        f"precipitation,precipitation_probability,"
                        f"weather_code,wind_speed_10m,"
                        f"wind_direction_10m,pressure_msl"
                        f"&timezone=Asia/Tokyo"
                    )

                    weather_tasks.append(self.fetch_weather_api(session, url, cname, pref_data))

                # 警報・注意報の並行取得タスク
                warning_tasks = []
                for cname in query_cities:
                    pref_data = self.prefectures.get(cname)
                    if pref_data and "jma" in pref_data and "forecast" in pref_data["jma"]:
                        warning_tasks.append(self.get_jma_warnings(session, pref_data["jma"]["forecast"], cname))

                # 最新規格の台風情報取得タスク
                typhoon_task = self.get_typhoon_info(session)

                # 各種タスクの同時並行実行
                weather_results = await asyncio.gather(*weather_tasks, return_exceptions=True)
                warning_results = await asyncio.gather(*warning_tasks, return_exceptions=True)
                typhoons = await typhoon_task

                # 警報データのマッピング
                warnings_map = {}
                for r in warning_results:
                    if r and isinstance(r, dict) and "name" in r:
                        warnings_map[r["name"]] = (r["warnings"], r["advisories"])

                # ==========================================
                # セクション1: 現在の天気
                # ==========================================
                current_weather_msg = ""
                for r in weather_results:
                    if not r or isinstance(r, Exception):
                        continue
                    name = r["name"]
                    data = r["data"]
                    cw = data.get("current", {})
                    if not cw:
                        continue

                    temp = cw.get("temperature_2m")
                    wind_speed = cw.get("wind_speed_10m")
                    wind_dir = cw.get("wind_direction_10m")
                    weather_code = cw.get("weather_code")

                    hourly = data.get("hourly", {})
                    times = hourly.get("time", [])
                    humidities = hourly.get("relative_humidity_2m", [])
                    pressures_hourly = hourly.get("pressure_msl", [])

                    now_hour = now_jst.replace(minute=0, second=0, microsecond=0, tzinfo=None)

                    # 最も近い時間（closest_index）の計算
                    if times:
                        closest_index = min(
                            range(len(times)),
                            key=lambda i: abs(parser.parse(times[i]).replace(tzinfo=None) - now_hour),
                        )
                        humidity = cw.get("relative_humidity_2m") if closest_index < len(humidities) else None
                        pressure = pressures_hourly[closest_index] if closest_index < len(pressures_hourly) else None
                    else:
                        humidity, pressure = None, None

                    weather_code = cw.get("weather_code")

                    icon = self.weather_icons.get(weather_code, "❓")
                    weather_name = self.weather_names.get(weather_code, "不明")
                    wind_dir_jp = self.get_wind_direction_jp(wind_dir)

                    current_weather_msg += f"### :white_sun_small_cloud: **{name} の現在の天気**\n"
                    current_weather_msg += f"気温: {temp}°C\n"
                    current_weather_msg += f"湿度: {humidity if humidity is not None else '不明'}%\n"
                    current_weather_msg += f"風速: {wind_speed} km/h\n"
                    current_weather_msg += f"風向: {wind_dir}° ({wind_dir_jp})\n"
                    current_weather_msg += f"気圧: {pressure if pressure is not None else '不明'} hPa\n"
                    current_weather_msg += f"天気: {icon} {weather_name}\n\n"

                if current_weather_msg:
                    await self.send_long_message(ctx, current_weather_msg)

                # ==========================================
                # セクション2: 詳細情報（今日・明日の6時間ごと）
                # ==========================================
                if detailed:
                    for r in weather_results:
                        if not r or isinstance(r, Exception):
                            continue
                        name = r["name"]
                        data = r["data"]
                        hourly = data.get("hourly", {})
                        times = hourly.get("time", [])
                        temps = hourly.get("temperature_2m", [])
                        precs_prob = hourly.get("precipitation_probability", [])
                        codes = hourly.get("weather_code", [])
                        wind_speeds = hourly.get("wind_speed_10m", [])
                        wind_dirs = hourly.get("wind_direction_10m", [])
                        pressures = hourly.get("pressure_msl", [])
                        humidities = hourly.get("relative_humidity_2m", [])

                        today_date = now_jst.date()
                        tomorrow_date = today_date + timedelta(days=1)

                        detailed_msg = f"### :bar_chart: **詳細情報（{name}・今日・明日の6時間ごと）**\n"
                        last_shown_date = None
                        has_data = False

                        for t_str, temp_val, prob, code, ws, wd, pres, hum in zip(
                            times,
                            temps,
                            precs_prob,
                            codes,
                            wind_speeds,
                            wind_dirs,
                            pressures,
                            humidities,
                        ):
                            dt = parser.parse(t_str)

                            if dt.date() in [today_date, tomorrow_date]:
                                if dt.hour % 6 == 0:
                                    has_data = True
                                    if dt.date() != last_shown_date:
                                        detailed_msg += f"#### **{dt.year}年**\n"
                                        detailed_msg += f"#### **{dt.month:02d}月{dt.day:02d}日**\n"
                                        last_shown_date = dt.date()

                                    start_hour = dt.strftime("%H:%M")
                                    end_dt = dt + timedelta(hours=6)
                                    end_hour = end_dt.strftime("%H:%M")

                                    icon_hour = self.weather_icons.get(code, "❓")
                                    weather_name_hour = self.weather_names.get(code, "不明")
                                    wind_dir_hour_jp = self.get_wind_direction_jp(wd)

                                    detailed_msg += (
                                        f"{start_hour} - {end_hour} {temp_val}℃ / 降水確率: {prob}% / "
                                        f"風速: {ws}km/h 風向き: {wd}°（{wind_dir_hour_jp}）/ 気圧: {pres}hPa {icon_hour} {weather_name_hour}\n"
                                    )

                        if has_data:
                            await self.send_long_message(ctx, detailed_msg)

                # ==========================================
                # セクション3: 気象情報（注意報・警報）
                # ==========================================
                warnings_msg = "**- 気象情報 -**\n"
                if len(warnings_msg) > len("**- 気象情報 -**\n"):
                    await self.send_long_message(ctx, warnings_msg)
                for cname in query_cities:
                    if cname in warnings_map:
                        warnings, advisories = warnings_map[cname]
                        warnings_msg += f"【{cname}】\n"
                        warnings_msg += "警報\n"
                        if warnings:
                            for w in warnings:
                                warnings_msg += f"- {w}\n"
                        else:
                            warnings_msg += "- 現在発表されている警報はありません\n"

                        warnings_msg += "注意報\n"
                        if advisories:
                            for a in advisories:
                                warnings_msg += f"- {a}\n"
                        else:
                            warnings_msg += "- 現在発表されている注意報はありません\n"
                        warnings_msg += "\n"

                await self.send_long_message(ctx, warnings_msg)

                # ==========================================
                # セクション4: 台風情報
                # ==========================================
                typhoon_msg = "### **台風情報**\n"
                if typhoons:
                    for ty in typhoons:
                        typhoon_msg += f"- 台風{ty['num']}号（{ty['name']}）が発生中\n"
                        typhoon_msg += "降水: - mm\n"
                        typhoon_msg += f"風速: {ty['wind_kmh']}km/h, {ty['wind_ms']}m/s\n"
                        typhoon_msg += f"気圧: {ty['pressure']}hPa\n"
                else:
                    typhoon_msg += "- 現在、発表されている台風情報はありません\n"

                await self.send_long_message(ctx, typhoon_msg)

        except Exception as e:
            logger.info("[Weather Debug] Core command error:")
            logger.info(traceback.format_exc())
            await ctx.send(f" 天気情報の取得に失敗しました: {e}")


async def setup(bot):
    await bot.add_cog(Weather(bot))
