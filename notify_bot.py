import os
import requests
import openai
import asyncio
import discord
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI

# 環境変数の読み込み
load_dotenv()
weather_api_key = os.getenv("OPENWEATHER_API_KEY")
openai_api_key = os.getenv("OPENAI_API_KEY")
discord_token = os.getenv("DISCORD_TOKEN")
channel_id = int(os.getenv("DISCORD_CHANNEL_ID"))

client = OpenAI(api_key=openai_api_key)

# 現在の天気情報取得
def get_weather():
    url = f"http://api.openweathermap.org/data/2.5/weather?q=Tokyo,jp&appid={weather_api_key}&units=metric&lang=ja"
    response = requests.get(url)
    data = response.json()

    if response.status_code != 200:
        return "天気情報の取得に失敗しました。"

    weather = data["weather"][0]["description"]
    temp = data["main"]["temp"]
    return f"現在の天気は「{weather}」、気温は{temp:.1f}℃です。"

# 今日の3時間ごとの天気予報取得
def get_forecast():
    url = f"http://api.openweathermap.org/data/2.5/forecast?q=Tokyo,jp&appid={weather_api_key}&units=metric&lang=ja"
    response = requests.get(url)
    data = response.json()

    if response.status_code != 200:
        return ""

    today = datetime.utcnow().date()
    forecast_data = [
        entry for entry in data["list"]
        if datetime.fromtimestamp(entry["dt"]).date() == today
           and entry["dt_txt"].split(" ")[1][:2] in ["09", "12", "15", "18", "21"]
    ]

    return "\n".join([f'{entry["dt_txt"][11:16]} {entry["weather"][0]["description"]} {entry["main"]["temp"]:.1f}℃' for entry in forecast_data])

# GPTで天気予報を要約
def generate_forecast_summary(forecast_text):
    prompt = f"""
以下は東京都心の今日の天気予報です（3時間ごとの天気と気温）：
{forecast_text}

この情報をもとに、親しみやすく自然な口調で、朝から夜までの天気や気温の様子を一文でまとめてください。元気が出る一言も添えてください。
"""
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content

# 傘のアドバイス生成
def get_umbrella_advice(forecast_text):
    if "雨" in forecast_text:
        return "午後から雨が降るかもしれません。お出かけの際は傘をお忘れなく☂️"
    else:
        return "今日は雨の心配はなさそうです。気持ちのいい一日になりますように☀️"

# ニュース取得（YahooニュースRSS）
def get_news():
    import feedparser
    rss_url = "https://news.yahoo.co.jp/rss/topics/top-picks.xml"
    feed = feedparser.parse(rss_url)
    news_list = [entry.title for entry in feed.entries[:3]]
    return "\n".join([f"・{item}" for item in news_list])

# メッセージ生成
async def generate_message():
    weather = get_weather()
    forecast = get_forecast()
    forecast_summary = generate_forecast_summary(forecast)
    advice = get_umbrella_advice(forecast)
    news = get_news()

    return f"おはようございます！\n{weather}\n\n🌤 今日の天気まとめ\n{forecast_summary}\n\n☂️ 傘のアドバイス\n{advice}\n\n📰 今日のニュース\n{news}"

# Discord通知
async def main():
    message = await generate_message()

    intents = discord.Intents.default()
    client_bot = discord.Client(intents=intents)

    @client_bot.event
    async def on_ready():
        channel = client_bot.get_channel(channel_id)

        embed = discord.Embed(
            title="☀️ 今日の朝通知",
            description=message,
            color=0x1abc9c
        )
        embed.set_footer(text="powered by ChatGPT + OpenWeather + Yahoo News")

        await channel.send(content="☀️ 今日の朝通知", embed=embed)
        await client_bot.close()

    await client_bot.start(discord_token)

asyncio.run(main())


