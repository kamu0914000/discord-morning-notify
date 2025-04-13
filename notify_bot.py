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

# 天気を取得（東京固定）
def get_weather():
    url = f"https://api.openweathermap.org/data/2.5/weather?q=Tokyo,jp&appid={weather_api_key}&units=metric&lang=ja"
    res = requests.get(url).json()
    return res

# 降水予報（9時〜24時）を取得
def get_precipitation_forecast():
    url = f"https://api.openweathermap.org/data/2.5/forecast?q=Tokyo,jp&appid={weather_api_key}&units=metric&lang=ja"
    res = requests.get(url).json()
    rain_hours = []
    now = datetime.utcnow() + timedelta(hours=9)  # JST
    for forecast in res["list"]:
        forecast_time = datetime.fromtimestamp(forecast["dt"]) + timedelta(hours=9)
        if 9 <= forecast_time.hour <= 23:
            if "rain" in forecast and forecast["rain"].get("3h", 0) > 0:
                rain_hours.append(forecast_time.strftime("%H:%M"))
    return rain_hours

# 傘が必要か判断
def get_umbrella_advice(rain_hours):
    if rain_hours:
        return f"\n☔ 【9時から24時の間に雨予報あり】\n以下の時間帯に雨の可能性があります：{', '.join(rain_hours)}。傘を持っていこう！"
    else:
        return "\n☀️ 本日は雨の予報はないようです！傘はいらないかも。"

# Yahooニュースから最新記事を1つ取得
def get_news():
    feed = feedparser.parse("https://news.yahoo.co.jp/rss/topics/top-picks.xml")
    if feed.entries:
        entry = feed.entries[0]
        return f"{entry.title} - {entry.link}"
    return "ニュース情報の取得に失敗しました"

# GPTでメッセージ生成
async def generate_message(current_weather, forecast, umbrella_advice, news):
    temp = current_weather['main']['temp']
    weather_main = current_weather['weather'][0]['description']
    wind = current_weather['wind']['speed']

    prompt = f"""
今日の天気は「{weather_main}」、気温は{temp}℃、風速は{wind}m/sです。
{umbrella_advice}

この情報をもとに、親しみやすく自然な日本語で、以下の内容を含む文章を作ってください：

1. 今日の天気の全体的な説明（朝〜夜までの様子）
2. 気温に応じたおすすめの服装（例：ライトアウター、パーカー、コートなど）
3. 傘が必要かどうかのアドバイス
4. ニュースも1〜2文で簡単に紹介

文章は150文字〜400文字程度でお願いします。
自然な挨拶文から始めて、ポジティブな締めで終えてください。

最新ニュース: {news}
"""

    client = openai.OpenAI()
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content

# Discordに送信
async def main():
    current_weather = get_weather()
    rain_forecast = get_precipitation_forecast()
    umbrella_advice = get_umbrella_advice(rain_forecast)
    news_text = get_news()
    message = await generate_message(current_weather, rain_forecast, umbrella_advice, news_text)

    intents = discord.Intents.default()
    client = discord.Client(intents=intents)

    @client.event
    async def on_ready():
        channel = client.get_channel(channel_id)

        embed = discord.Embed(
            title="☀️ 今日の朝通知",
            description=message,
            color=0x1abc9c
        )
        embed.set_footer(text="powered by ChatGPT + OpenWeather + Yahoo News")

        await channel.send(content="@everyone", embed=embed)
        await client.close()

    await client.start(discord_token)

# 実行
if __name__ == "__main__":
    asyncio.run(main())












