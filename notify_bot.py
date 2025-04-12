import os
import openai
import discord
import asyncio
import requests
import feedparser
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
discord_token = os.getenv("DISCORD_TOKEN")
channel_id = int(os.getenv("DISCORD_CHANNEL_ID"))
weather_api_key = os.getenv("OPENWEATHER_API_KEY")

# 現在の天気を取得（東京都固定）
def get_current_weather():
    url = f"https://api.openweathermap.org/data/2.5/weather?q=Tokyo,jp&appid={weather_api_key}&units=metric&lang=ja"
    data = requests.get(url).json()
    description = data['weather'][0]['description']
    temp = round(data['main']['temp'], 1)
    return description, temp

# 服装アドバイスを生成
def get_clothing_advice(temp):
    if temp < 10:
        return "かなり寒いので、コートや厚手の上着をおすすめします🧣"
    elif temp < 16:
        return "肌寒い一日になりそうです。ライトアウターやトレンチコートがあると安心です🧥"
    elif temp < 22:
        return "過ごしやすい気温です。長袖シャツや薄手のジャケットがおすすめです👔"
    elif temp < 27:
        return "暖かく快適な陽気です。シャツ一枚でも大丈夫そうです👕"
    else:
        return "暑い一日になりそうです。半袖＆帽子で熱中症対策を☀️🧢"

# 降水確率を取得（3時間ごとの予報）
def get_rain_forecast():
    url = f"https://api.openweathermap.org/data/2.5/forecast?q=Tokyo,jp&appid={weather_api_key}&units=metric&lang=ja"
    data = requests.get(url).json()
    forecast_text = []
    for item in data['list'][:8]:  # 24時間分（3時間×8）
        dt = datetime.fromtimestamp(item['dt']) + timedelta(hours=9)
        time_range = f"{dt.hour}時〜{(dt.hour + 3)%24}時"
        weather_desc = item['weather'][0]['description']
        rain = item.get('pop', 0)
        if rain >= 0.3:
            forecast_text.append(f"・{time_range}：{weather_desc}（降水確率{int(rain * 100)}%）")
    return forecast_text

# 傘の要不要をざっくり判断
def get_umbrella_advice(rain_forecast):
    if rain_forecast:
        return "今日は雨の時間帯があります。傘を持って出かけると安心です ☂️"
    else:
        return "今日は雨の心配はなさそうです。傘は必要なさそうですね！"

# ニュース取得
def get_news():
    url = "https://news.yahoo.co.jp/rss/topics/top-picks.xml"
    feed = feedparser.parse(url)
    entries = feed.entries[:3]
    return [f"・{entry.title}" for entry in entries]

# ChatGPTに要約させる
def generate_message(description, temp, clothing_advice, forecast, umbrella_advice, news):
    prompt = f"""
おはようございます！

☀️ 現在の天気は「{description}」、気温は{temp}℃です。
👕 {clothing_advice}

🌤️ 今日の天気まとめ
{umbrella_advice}

⏰ 時間帯ごとの雨予報
{chr(10).join(forecast) if forecast else '雨の予報はありません。'}

📰 今日の注目ニュース
{chr(10).join(news)}

それでは素敵な1日をお過ごしください！
"""
    return prompt

# Discord通知
async def main():
    description, temp = get_current_weather()
    clothing_advice = get_clothing_advice(temp)
    rain_forecast = get_rain_forecast()
    umbrella_advice = get_umbrella_advice(rain_forecast)
    news = get_news()

    message = generate_message(description, temp, clothing_advice, rain_forecast, umbrella_advice, news)

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

if __name__ == "__main__":
    asyncio.run(main())







