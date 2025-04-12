import os
import openai
import discord
import asyncio
import requests
import feedparser
from dotenv import load_dotenv

# .envの読み込み
load_dotenv()

discord_token = os.getenv("DISCORD_TOKEN")
channel_id = int(os.getenv("DISCORD_CHANNEL_ID"))
weather_api_key = os.getenv("OPENWEATHER_API_KEY")

# 東京都心の天気を取得
def get_weather():
    url = f"http://api.openweathermap.org/data/2.5/weather?q=Tokyo,jp&appid={weather_api_key}&units=metric&lang=ja"
    response = requests.get(url)
    data = response.json()
    if response.status_code != 200:
        return "天気情報の取得に失敗しました。"

    desc = data["weather"][0]["description"]
    temp = data["main"]["temp"]
    temp_min = data["main"]["temp_min"]
    temp_max = data["main"]["temp_max"]
    return f"{desc}、現在の気温は{temp}℃（最高{temp_max}℃ / 最低{temp_min}℃）です。"

# ニュース（YahooトピックRSS）を取得
def get_news():
    feed = feedparser.parse("https://news.yahoo.co.jp/rss/topics/top-picks.xml")
    top_articles = [f"・{entry.title}" for entry in feed.entries[:3]]
    return "\n".join(top_articles)

# GPTで通知文を生成
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

async def generate_message(weather_text, news_text):
    prompt = (
        "以下の情報を元に、朝のDiscord通知メッセージを自然な口調で作ってください。\n"
        "1. 天気情報\n"
        f"{weather_text}\n"
        "2. 今日の注目ニュース\n"
        f"{news_text}\n"
        "テンションは明るめで、見た人が『よし今日も頑張ろう』と思えるようにしてください。"
    )

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content


# Discordに送信
async def main():
    weather = get_weather()
    news = get_news()
    message = await generate_message(weather, news)

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

# 👇 ここは on_ready の外に置く！
await client.start(discord_token)


asyncio.run(main())
