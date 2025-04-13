import os
import requests
import feedparser
import openai
import discord
import asyncio
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")
discord_token = os.getenv("DISCORD_TOKEN")
channel_id = int(os.getenv("DISCORD_CHANNEL_ID"))
weather_api_key = os.getenv("OPENWEATHER_API_KEY")

def get_weather():
    url = f"https://api.openweathermap.org/data/2.5/weather?q=Tokyo,jp&appid={weather_api_key}&units=metric&lang=ja"
    res = requests.get(url).json()
    return res

def get_precipitation_forecast():
    url = f"https://api.openweathermap.org/data/2.5/forecast?q=Tokyo,jp&appid={weather_api_key}&units=metric&lang=ja"
    res = requests.get(url).json()
    now = datetime.utcnow() + timedelta(hours=9)  # JST
    forecast_list = []
    for forecast in res["list"]:
        forecast_time = datetime.fromtimestamp(forecast["dt"]) + timedelta(hours=9)
        if 9 <= forecast_time.hour <= 24:
            rain = forecast.get("rain", {}).get("3h", 0)
            description = forecast["weather"][0]["description"]
            pop = int(forecast.get("pop", 0) * 100)
            forecast_list.append(f"・{forecast_time.hour}時〜{forecast_time.hour+3}時：{description}（降水確率{pop}%）")
    return forecast_list

def get_news():
    feed = feedparser.parse("https://news.yahoo.co.jp/rss/topics/top-picks.xml")
    entries = feed.entries[:3]
    news_lines = [f"・{entry.title}" for entry in entries]
    return "\n".join(news_lines)

async def generate_message(current_weather, forecast_text, news_text):
    temp = current_weather['main']['temp']
    weather_main = current_weather['weather'][0]['description']
    wind = current_weather['wind']['speed']

    prompt = f"""
    東京の今日の天気は「{weather_main}」、気温は{temp}℃、風速は{wind}m/sです。
    これをもとに：
    - 天気まとめ
    - 服装のアドバイス（親しみやすく）
    を出力。
    そのあと、次のように各項目で区切って書いてください：
    ---
    ☀️ 今日の天気まとめ
    （天気まとめ）
    
    👕 今日の服装アドバイス
    （服装アドバイス）
    
    ☔ 今日の雨予報（9時〜24時）
    {forecast_text}

    📰 今日の注目ニュース
    {news_text}

    最後に：
    みなさんに向けた励ましの一言（30文字以内）
    """

    client = openai.OpenAI()
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content

async def main():
    current_weather = get_weather()
    forecast_lines = get_precipitation_forecast()
    forecast_text = "\n".join(forecast_lines)
    news_text = get_news()
    message = await generate_message(current_weather, forecast_text, news_text)

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

if __name__ == "__main__":
    asyncio.run(main())













