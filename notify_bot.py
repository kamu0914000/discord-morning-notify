import os
import openai
import discord
import asyncio
import requests
import feedparser
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

openai_api_key = os.getenv("OPENAI_API_KEY")
discord_token = os.getenv("DISCORD_TOKEN")
channel_id = int(os.getenv("DISCORD_CHANNEL_ID"))
weather_api_key = os.getenv("OPENWEATHER_API_KEY")

# 現在の天気情報を取得
def get_current_weather():
    url = f"https://api.openweathermap.org/data/2.5/weather?q=Tokyo,jp&appid={weather_api_key}&units=metric&lang=ja"
    response = requests.get(url)
    data = response.json()
    if response.status_code != 200:
        return None
    weather = data["weather"][0]["description"]
    temp = data["main"]["temp"]
    return weather, temp

# 今日の天気予報を取得
def get_today_forecast():
    url = f"https://api.openweathermap.org/data/2.5/forecast?q=Tokyo,jp&appid={weather_api_key}&units=metric&lang=ja"
    response = requests.get(url)
    data = response.json()
    if response.status_code != 200:
        return None

    forecasts = [entry for entry in data["list"] if "09:00:00" in entry["dt_txt"] or "12:00:00" in entry["dt_txt"] or "18:00:00" in entry["dt_txt"]]

    weather_summary = []
    rain_expected = False
    for entry in forecasts:
        time = entry["dt_txt"].split(" ")[1][:5]
        desc = entry["weather"][0]["description"]
        temp = round(entry["main"]["temp"])
        weather_summary.append(f"{time}時：{desc}（{temp}℃）")
        if "rain" in entry["weather"][0]["main"].lower():
            rain_expected = True

    return weather_summary, rain_expected

# ニュース取得
def get_news():
    url = "https://news.yahoo.co.jp/rss/topics/top-picks.xml"
    feed = feedparser.parse(url)
    entries = feed.entries[:3]
    return [entry.title for entry in entries]

# GPTでメッセージ生成
async def generate_message(current_weather, temp, forecast, rain_expected, news):
    prompt = f"""
おはようございます！
現在の天気は「{current_weather}」、気温は{temp}℃です。

🌤 今日の天気まとめ
{', '.join(forecast)}

☂️ 傘のアドバイス
{"今日は雨の可能性があるので、傘を持って出かけてね！" if rain_expected else "今日は雨の心配はなさそうです。気持ちのいい一日になりますように☀️"}

📰 今日のニュース
・{news[0]}
・{news[1]}
・{news[2]}
"""

    client = openai.OpenAI(api_key=openai_api_key)
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "あなたは親しみやすくて丁寧な朝の案内役です。"},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content

# Discordに送信
async def main():
    weather, temp = get_current_weather()
    forecast, rain_expected = get_today_forecast()
    news = get_news()
    message = await generate_message(weather, temp, forecast, rain_expected, news)

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

        await channel.send(content="☀️ 今日の朝通知", embed=embed)
        await client.close()

    await client.start(discord_token)

asyncio.run(main())





