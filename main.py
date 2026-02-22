import discord
from discord.ext import commands
import os
import asyncio

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

async def main():
    await bot.start(os.getenv("DISCORD_TOKEN"))

asyncio.run(main())