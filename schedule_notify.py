import os
import pickle
import discord
import asyncio
from datetime import datetime, timedelta
from googleapiclient.discovery import build
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID"))

# Googleカレンダーから今日の予定を取得
def get_calendar_events():
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

    service = build('calendar', 'v3', credentials=creds)

    now = datetime.utcnow().isoformat() + 'Z'
    end = (datetime.utcnow() + timedelta(days=1)).isoformat() + 'Z'

    events_result = service.events().list(
        calendarId='primary',
        timeMin=now,
        timeMax=end,
        maxResults=10,
        singleEvents=True,
        orderBy='startTime'
    ).execute()

    events = events_result.get('items', [])

    if not events:
        return ["（予定はありません）"]

    formatted = []
    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        time_str = datetime.fromisoformat(start.replace('Z', '+00:00')).strftime('%Y/%m/%d %H:%M')
        summary = event.get('summary', '（無題）')
        formatted.append(f"・{time_str}：{summary}")
    return formatted

# Discordに送信
async def main():
    events = get_calendar_events()
    schedule_text = "📅 **今日の予定**\n" + "\n".join(events)

    intents = discord.Intents.default()
    client = discord.Client(intents=intents)

    @client.event
    async def on_ready():
        channel = client.get_channel(CHANNEL_ID)
        embed = discord.Embed(
            title="🔔 Googleカレンダー通知",
            description=schedule_text,
            color=0x7289da
        )
        embed.set_footer(text="powered by Google Calendar + ChatGPT")
        await channel.send(content="@everyone", embed=embed)
        await client.close()

    await client.start(DISCORD_TOKEN)

if __name__ == "__main__":
    asyncio.run(main())



