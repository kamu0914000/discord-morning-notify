import os
import openai
import discord
import asyncio
import requests
import feedparser
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

openai_api_key = os.getenv("OPENAI_API_KEY")
discord_token = os.getenv("DISCORD_TOKEN")
channel_id = int(os.getenv("DISCORD_CHANNEL_ID"))
weather_api_key = os.getenv("OPENWEATHER_API_KEY")

# 現在の天気取得
def get_weather():
    url = f"https://api.openweathermap.org/data/2.5/weather?q=Tokyo,jp&appid={weather_api_key}&units=metric&lang=ja"
    response = requests.get(url)
    if response.status_code != 200:
        return "天気情報の取得に失敗しました。"
    data = response.json()
    weather = data["weather"][0]["description"]
    temp = data["main"]["temp"]
    return weather, temp

# 時間帯ごとの降水確率取得（9時〜24時）
def get_hourly_rain_forecast():
    url = f"https://api.openweathermap.org/data/2.5/forecast?q=Tokyo,jp&appid={weather_api_key}&units=metric&lang=ja"
    response = requests.get(url)
    forecast_data = response.json()

    forecasts = []
    now = datetime.utcnow() + timedelta(hours=9)
    for entry in forecast_data["list"]:
        forecast_time = datetime.strptime(entry["dt_txt"], "%Y-%m-%d %H:%M:%S")
        if 9 <= forecast_time.hour <= 24 and forecast_time.date() == now.date():
            hour_label = f"{forecast_time.hour}時〜{forecast_time.hour+3}時"
            rain = entry["weather"][0]["description"]
            pop = int(entry.get("pop", 0) * 100)
            forecasts.append(f"・{hour_label}：{rain}（降水確率{pop}%）")
    return forecasts

# 傘のアドバイス生成
def generate_umbrella_advice(hourly_forecasts):
    needs_umbrella = any("雨" in forecast for forecast in hourly_forecasts)
    if needs_umbrella:
        return "今日は雨の可能性があるので、傘を持って出かけると安心です ☔"
    else:
        return "今日は雨の心配はなさそうです。気持ちのいい一日になりそうですね ☀️"

# 気温に基づく服装アドバイス
def get_outfit_advice(temp):
    if temp < 10:
        return "今日はとても寒いので、厚手のコートやマフラーが必要です🧣🧥"
    elif temp < 15:
        return "肌寒い一日になりそうです。ライトアウターやトレンチコートがあると安心です🧥"
    elif temp < 20:
        return "少し肌寒いかもしれません。薄手のカーディガンなどがあると良いでしょう🧶"
    else:
        return "暖かい一日になりそうです。軽装で快適に過ごせます👕"

# ニュース取得
def get_news():
    url = "https://news.yahoo.co.jp/rss/topics/top-picks.xml"
    feed = feedparser.parse(url)
    entries = feed.entries[:3]
    return [f"・{entry.title}" for entry in entries]

# メッセージ生成
def generate_message(weather, temp, umbrella_advice, hourly_rain_forecast, outfit, news):
    forecast_text = "\n".join(hourly_rain_forecast)
    news_text = "\n".join(news)
    return f"""
おはようございます！

☀️ 現在の天気は「{weather}」、気温は{temp:.1f}℃です。

{outfit}

🌤️ 今日の天気まとめ
{umbrella_advice}

⏰ 今日の雨予報（9時〜24時）
{forecast_text}

📰 今日の注目ニュース
{news_text}

それでは素敵な1日をお過ごしください！
"""

# Discordに送信
async def main():
    weather, temp = get_weather()
    hourly_rain_forecast = get_hourly_rain_forecast()
    umbrella_advice = generate_umbrella_advice(hourly_rain_forecast)
    outfit = get_outfit_advice(temp)
    news = get_news()
    message = generate_message(weather, temp, umbrella_advice, hourly_rain_forecast, outfit, news)

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









