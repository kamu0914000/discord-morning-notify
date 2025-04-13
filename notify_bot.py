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
    res = requests.get(url).json()
    return res

# 時系列の降水予報を取得（9時〜24時）
def get_precipitation_forecast():
    url = f"https://api.openweathermap.org/data/2.5/forecast?q=Tokyo,jp&appid={weather_api_key}&units=metric&lang=ja"
    res = requests.get(url).json()
    hourly_rain_info = []
    now = datetime.utcnow() + timedelta(hours=9)  # JST

    for forecast in res["list"]:
        forecast_time = datetime.fromtimestamp(forecast["dt"]) + timedelta(hours=9)
        if 9 <= forecast_time.hour <= 24:
            time_str = f"{forecast_time.hour}時〜{forecast_time.hour+3}時"
            weather_desc = forecast["weather"][0]["description"]
            rain_chance = forecast.get("pop", 0) * 100
            entry = (forecast_time, f"・{time_str}：{weather_desc}（降水確率{round(rain_chance)}%）")
            hourly_rain_info.append(entry)

    # 時系列順に並び替え
    hourly_rain_info.sort(key=lambda x: x[0])
    return [e[1] for e in hourly_rain_info]

# Yahooニュースを取得
def get_news():
    feed = feedparser.parse("https://news.yahoo.co.jp/rss/topics/top-picks.xml")
    if feed.entries:
        entries = feed.entries[:3]
        return "\n".join([f"・{entry.title}" for entry in entries])
    return "・ニュース情報の取得に失敗しました"

# GPTでメッセージ生成
async def generate_message(current_weather, rain_list, news_text):
    temp = current_weather['main']['temp']
    weather_main = current_weather['weather'][0]['description']
    wind = current_weather['wind']['speed']

    rain_block = "\n".join(rain_list)

    prompt = f"""
東京の現在の天気は「{weather_main}」、気温は{temp:.1f}℃、風速は{wind:.2f}m/sです。
今日の服装アドバイス、天気のまとめ、雨の時系列予報（9〜24時）、ニュース、最後の一言を含むDiscord通知メッセージを作ってください。
親しみやすく、丁寧な日本語で。

【形式】
🌤 今日の天気まとめ
（例）東京は今日は「晴れ」となっています。気温は◯度で、風はやや強めです。外出の際は◯◯に注意です。

👕 今日の服装アドバイス
（例）ライトアウターや防水ジャケットがおすすめです。気温や風にも備えましょう。

🌧️ 今日の雨予報（9時〜24時）
（例）・9時〜12時：曇りがち（降水確率30%）
　　　・12時〜15時：小雨（降水確率70%）...

📰 今日の注目ニュース
{news_text}

（最後に一言）"""

    client = openai.OpenAI()
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

# Discordに送信
async def main():
    current_weather = get_weather()
    rain_list = get_precipitation_forecast()
    news_text = get_news()
    message = await generate_message(current_weather, rain_list, news_text)

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














