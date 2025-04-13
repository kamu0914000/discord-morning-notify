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
    rain_forecast = []
    now = datetime.utcnow() + timedelta(hours=9)
    for forecast in res["list"]:
        forecast_time = datetime.fromtimestamp(forecast["dt"]) + timedelta(hours=9)
        if 9 <= forecast_time.hour <= 24:
            weather = forecast["weather"][0]["description"]
            pop = int(forecast.get("pop", 0) * 100)
            if pop >= 20:
                rain_forecast.append({
                    "time": forecast_time.strftime("%H時"),
                    "weather": weather,
                    "pop": pop
                })
    return rain_forecast

# 傘が必要か判断
def get_umbrella_advice(rain_forecast):
    if rain_forecast:
        times = ', '.join([f["time"] for f in rain_forecast])
        return f"☔ 【雨予報あり】\n{times} に雨の可能性があります。傘を忘れずに！"
    else:
        return "☀️ 今日の雨の心配は少なそうです。"

# Yahooニュースから最新記事を3件取得
def get_news():
    feed = feedparser.parse("https://news.yahoo.co.jp/rss/topics/top-picks.xml")
    entries = feed.entries[:3]
    news_items = [f"・{entry.title}" for entry in entries]
    return '\n'.join(news_items)

# GPTでメッセージ生成
async def generate_message(current_weather, rain_forecast, umbrella_advice, news):
    temp = current_weather['main']['temp']
    weather_main = current_weather['weather'][0]['description']
    wind = current_weather['wind']['speed']

    forecast_text = '\n'.join([
        f"・{f['time']}：{f['weather']}（降水確率{f['pop']}%）"
        for f in rain_forecast
    ])

    prompt = f"""
    今日の東京の天気は「{weather_main}」、気温は{temp:.1f}℃、風速{wind:.1f}m/sです。
    傘のアドバイス: {umbrella_advice}
    今日の雨予報:
    {forecast_text}

    この情報をもとに、親しみやすく、1日を元気に過ごすためのアドバイスを含んだ朝の挨拶メッセージを作って。
    文章は日本語で、300文字程度で、文末に元気な一言を添えて。

    今日のニュース:
    {news}
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
    rain_info = get_precipitation_forecast()
    umbrella_advice = get_umbrella_advice(rain_info)
    news = get_news()
    message = await generate_message(current_weather, rain_info, umbrella_advice, news)

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













