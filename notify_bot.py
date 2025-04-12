import os
import openai
import discord
import asyncio
import requests
import feedparser
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
discord_token = os.getenv("DISCORD_TOKEN")
channel_id = int(os.getenv("DISCORD_CHANNEL_ID"))
weather_api_key = os.getenv("OPENWEATHER_API_KEY")


def get_weather():
    url = f"http://api.openweathermap.org/data/2.5/weather?q=Tokyo,jp&appid={weather_api_key}&units=metric&lang=ja"
    response = requests.get(url)
    data = response.json()

    if response.status_code != 200:
        return "天気情報の取得に失敗しました。"

    description = data["weather"][0]["description"]
    temp = data["main"]["temp"]
    return f"現在の天気は「{description}」、気温は{temp:.1f}℃です。"


def get_forecast():
    url = f"https://api.openweathermap.org/data/2.5/forecast?q=Tokyo,jp&appid={weather_api_key}&units=metric&lang=ja"
    response = requests.get(url)
    data = response.json()

    if response.status_code != 200:
        return "天気予報の取得に失敗しました。"

    today_forecast = [item for item in data["list"] if "12:00:00" in item["dt_txt"] or "15:00:00" in item["dt_txt"] or "18:00:00" in item["dt_txt"]]

    if not today_forecast:
        return "今日の天気予報は取得できませんでした。"

    desc_list = [item["weather"][0]["description"] for item in today_forecast]
    temp_list = [item["main"]["temp"] for item in today_forecast]

    desc_summary = "、".join(desc_list)
    min_temp = min(temp_list)
    max_temp = max(temp_list)

    return f"今日は東京でも {desc_summary} の天気で、気温は {min_temp:.1f}〜{max_temp:.1f}℃ になりそうです。"


def check_rain():
    url = f"https://api.openweathermap.org/data/2.5/forecast?q=Tokyo,jp&appid={weather_api_key}&units=metric&lang=ja"
    response = requests.get(url)
    data = response.json()

    if response.status_code != 200:
        return "傘の情報取得に失敗しました。"

    today_forecast = [item for item in data["list"] if "09:00:00" in item["dt_txt"] or "12:00:00" in item["dt_txt"] or "15:00:00" in item["dt_txt"]]
    for item in today_forecast:
        weather = item["weather"][0]["main"]
        if "雨" in weather or "Rain" in weather:
            return "今日は雨の可能性があります。念のため傘を持って行ってください☔"

    return "今日は雨の心配はなさそうです。気持ちのいい一日になりますように☀️"


def get_news():
    url = "https://news.yahoo.co.jp/rss/topics/top-picks.xml"
    feed = feedparser.parse(url)
    top_entries = feed.entries[:3]
    return "\n".join([f"・{entry.title}" for entry in top_entries])


def generate_message(current_weather, forecast, umbrella_advice, news_text):
    prompt = f"""
あなたは朝の天気ニュースを伝えるアシスタントです。
以下の情報をもとに、親しみやすい口調でコンパクトにまとめてください。

【現在の天気】
{current_weather}

【今日の天気（朝〜夜）】
{forecast}

【傘のアドバイス】
{umbrella_advice}

【今日のニュース】
{news_text}

文章は簡潔に、明るく、読みやすくしてください。
"""
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "あなたは親しみやすい天気ニュースアシスタントです。"},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content


async def main():
    current_weather = get_weather()
    forecast = get_forecast()
    umbrella_advice = check_rain()
    news_text = get_news()

    message = await generate_message(current_weather, forecast, umbrella_advice, news_text)

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






