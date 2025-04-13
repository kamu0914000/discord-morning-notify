import os
import asyncio
import discord
import requests
import feedparser
from datetime import datetime, timedelta
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# API Keys & Settings
openai_api_key = os.getenv("OPENAI_API_KEY")
discord_token = os.getenv("DISCORD_TOKEN")
channel_id = int(os.getenv("DISCORD_CHANNEL_ID"))
weather_api_key = os.getenv("OPENWEATHER_API_KEY")

client_openai = OpenAI(api_key=openai_api_key)

# --- Weather ---
def get_weather():
    url = f"https://api.openweathermap.org/data/2.5/weather?q=Tokyo,jp&appid={weather_api_key}&units=metric&lang=ja"
    response = requests.get(url)
    if response.status_code != 200:
        return "天気情報の取得に失敗しました。", 0
    data = response.json()
    return data["weather"][0]["description"], data["main"]["temp"]

# --- Rain Forecast ---
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

# --- Umbrella Advice ---
def generate_umbrella_advice(hourly_forecasts):
    return (
        "今日は雨の可能性があるので、傘を持って出かけると安心です ☔"
        if any("雨" in f for f in hourly_forecasts)
        else "今日は雨の心配はなさそうです。気持ちのいい一日になりそうですね ☀️"
    )

# --- Outfit Advice ---
def get_outfit_advice(temp):
    if temp < 10:
        return "今日はとても寒いので、厚手のコートやマフラーが必要です🧣🧥"
    elif temp < 15:
        return "肌寒い一日になりそうです。ライトアウターやトレンチコートがあると安心です🧥"
    elif temp < 20:
        return "少し肌寒いかもしれません。薄手のカーディガンなどがあると良いでしょう🧶"
    else:
        return "暖かい一日になりそうです。軽装で快適に過ごせます👕"

# --- News ---
def get_news():
    feed = feedparser.parse("https://news.yahoo.co.jp/rss/topics/top-picks.xml")
    return [f"・{entry.title}" for entry in feed.entries[:3]]

# --- Weekday Mood ---
def get_weekday_label():
    return ["月曜日", "火曜日", "水曜日", "木曜日", "金曜日", "土曜日", "日曜日"][(datetime.utcnow() + timedelta(hours=9)).weekday()]

def get_weekday_mood(weekday):
    mood_map = {
        "月曜日": "少し憂鬱な気持ちと共に、新しい一週間を迎えるトーンで",
        "火曜日": "現実を受け入れつつ、やるべきことをこなす雰囲気で",
        "水曜日": "週の折り返し地点として少し疲れを感じつつも励ますように",
        "木曜日": "少し飽きと疲れが出始める中で淡々と伝えるトーンで",
        "金曜日": "週末が近づいて高揚感を感じさせるように明るく",
        "土曜日": "のんびりとした週末の始まりを感じさせるリラックスしたトーンで",
        "日曜日": "明日が月曜である現実を少し意識しつつ、休息を大切にする雰囲気で"
    }
    return mood_map.get(weekday, "")

# --- Generate Message with GPT ---
def generate_message_with_gpt(weather, temp, umbrella_advice, hourly_rain_forecast, outfit, news):
    weekday = get_weekday_label()
    mood = get_weekday_mood(weekday)
    forecast_text = "\n".join(hourly_rain_forecast)
    news_text = "\n".join(news)
    prompt = f"""
今日は{weekday}です。{mood}
以下の情報をもとに、朝の挨拶メッセージを作成してください：
・天気：{weather}、{temp:.1f}℃
・服装アドバイス：{outfit}
・傘アドバイス：{umbrella_advice}
・降水予報：\n{forecast_text}
・今日のニュース：\n{news_text}
"""
    response = client_openai.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )
    return response.choices[0].message.content

# --- Discord Notification ---
async def main():
    weather, temp = get_weather()
    hourly_forecast = get_hourly_rain_forecast()
    umbrella = generate_umbrella_advice(hourly_forecast)
    outfit = get_outfit_advice(temp)
    news = get_news()
    message = generate_message_with_gpt(weather, temp, umbrella, hourly_forecast, outfit, news)

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
        embed.set_footer(text="powered by GPT-4 + OpenWeather + Yahoo News")
        await channel.send(embed=embed)
        await client.close()

    await client.start(discord_token)

if __name__ == "__main__":
    asyncio.run(main())











