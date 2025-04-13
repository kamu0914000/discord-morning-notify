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
    rain_info = []
    now = datetime.utcnow() + timedelta(hours=9)
    for forecast in res["list"]:
        forecast_time = datetime.fromtimestamp(forecast["dt"]) + timedelta(hours=9)
        if 9 <= forecast_time.hour < 24:
            weather = forecast["weather"][0]["description"]
            pop = int(forecast.get("pop", 0) * 100)
            hour_block = f"{forecast_time.hour:02d}時〜{(forecast_time.hour+3)%24:02d}時"
            rain_info.append(f"・{hour_block}：{weather}（降水確率{pop}%）")
    return rain_info

# 傘が必要か判断
def get_umbrella_advice(rain_info):
    if any("雨" in r for r in rain_info):
        return "今日は傘が必要です。降水の時間帯にご注意ください。"
    else:
        return "今日は雨の心配は少なそうです☀"

# Yahooニュースから最新記事を3件取得
def get_news():
    feed = feedparser.parse("https://news.yahoo.co.jp/rss/topics/top-picks.xml")
    entries = feed.entries[:3]
    news_lines = [f"・{entry.title}" for entry in entries]
    return "\n".join(news_lines)

# GPTでメッセージ生成
async def generate_message(current_weather, rain_info, umbrella_advice, news):
    temp = current_weather['main']['temp']
    weather_main = current_weather['weather'][0]['description']
    wind = current_weather['wind']['speed']

    prompt = f"""
以下の条件をもとに、以下の形式でDiscord通知用の文章を日本語で作成してください：

☀️ 今日の天気
- 天気の説明（{weather_main}）
- 気温（{temp}℃）
- 風速（{wind}m/s）
- 傘のアドバイス（{umbrella_advice}）

🧥 今日の服装アドバイス
- 気温・風を踏まえたおすすめの服装

🌧️ 今日の雨予報（9時〜24時）
{chr(10).join(rain_info)}

📰 今日の注目ニュース
{news}

最後に、元気が出る一言で締めてください。
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
    news_text = get_news()
    message = await generate_message(current_weather, rain_info, umbrella_advice, news_text)

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














