import os
import requests
import feedparser
import openai
import discord
import asyncio
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

# APIキーと設定
openai.api_key = os.getenv("OPENAI_API_KEY")
discord_token = os.getenv("DISCORD_TOKEN")
channel_id = int(os.getenv("DISCORD_CHANNEL_ID"))
weather_api_key = os.getenv("OPENWEATHER_API_KEY")

# 現在の天気を取得
def get_weather():
    url = f"https://api.openweathermap.org/data/2.5/weather?q=Tokyo,jp&appid={weather_api_key}&units=metric&lang=ja"
    return requests.get(url).json()

# 降水予報（9時〜24時）を取得
def get_precipitation_forecast():
    url = f"https://api.openweathermap.org/data/2.5/forecast?q=Tokyo,jp&appid={weather_api_key}&units=metric&lang=ja"
    res = requests.get(url).json()
    rain_info = []

    now = datetime.utcnow() + timedelta(hours=9)  # JST
    for forecast in res["list"]:
        forecast_time = datetime.fromtimestamp(forecast["dt"]) + timedelta(hours=9)
        if 9 <= forecast_time.hour <= 24:
            weather_desc = forecast["weather"][0]["description"]
            pop = forecast.get("pop", 0)  # 降水確率 (0.0〜1.0)
            if "rain" in weather_desc or forecast.get("rain"):
                rain_info.append(f"{forecast_time.hour}時〜{forecast_time.hour+3}時：{weather_desc}（降水確率{int(pop * 100)}%）")

    return rain_info

# 傘のアドバイス
def get_umbrella_advice(rain_info):
    if rain_info:
        return "今日は雨の可能性があるので、傘を持っていくと安心です ☂️"
    else:
        return "今日は雨の心配はなさそうです ☀️"

# Yahooニュースの取得
def get_news():
    feed = feedparser.parse("https://news.yahoo.co.jp/rss/topics/top-picks.xml")
    entries = feed.entries[:3]
    return [f"・{entry.title}" for entry in entries]

# ChatGPTでメッセージ生成
async def generate_message(current_weather, rain_info, umbrella_advice, news_list):
    temp = current_weather["main"]["temp"]
    weather_main = current_weather["weather"][0]["description"]
    wind = current_weather["wind"]["speed"]

    rain_summary = "\n".join(rain_info) if rain_info else "降水の予報はありません。"
    news_text = "\n".join(news_list)

    prompt = f"""
おはようございます！今日の天気に関する情報をお届けします。

現在の天気は「{weather_main}」、気温は{temp:.1f}℃、風速は{wind:.1f}m/sです。

服装アドバイス:
・{('寒い' if temp < 15 else '暖かめ' if temp > 25 else '過ごしやすい')}気温なので、{'上着やジャケットを着ましょう' if temp < 15 else '軽装で大丈夫そうです'}

☂️ 今日の傘アドバイス:
{umbrella_advice}

⏰ 今日の雨予報（9時〜24時）:
{rain_summary}

📰 今日の注目ニュース:
{news_text}

今日も素敵な一日をお過ごしください！

powered by ChatGPT + OpenWeather + Yahoo News
"""
    client = openai.OpenAI()
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content

# Discord通知
async def main():
    current_weather = get_weather()
    rain_info = get_precipitation_forecast()
    umbrella_advice = get_umbrella_advice(rain_













