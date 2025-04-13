import os
import discord
import asyncio
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

discord_token = os.getenv("DISCORD_TOKEN")
channel_id = int(os.getenv("DISCORD_CHANNEL_ID"))

# 仮のスケジュール情報（そのうちGoogle Calendarと連携したくなるやつ）
def get_schedule():
    today = datetime.now().strftime("%Y/%m/%d")
    schedule = [
        "・10:00 チームミーティング",
        "・13:00 ランチミーティング",
        "・16:00 クライアント対応"
    ]
    return f"📅 {today} の予定\n" + "\n".join(schedule)

async def main():
    schedule_text = get_schedule()

    intents = discord.Intents.default()
    client = discord.Client(intents=intents)

    @client.event
    async def on_ready():
        channel = client.get_channel(channel_id)

        embed = discord.Embed(
            title="📌 今日の予定リマインダー",
            description=schedule_text,
            color=0xf1c40f
        )
        embed.set_footer(text="powered by ScheduleBot")
        await channel.send(content="@everyone", embed=embed)
        await client.close()

    await client.start(discord_token)

if __name__ == "__main__":
    asyncio.run(main())
