import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

TOKEN = os.getenv("DISCORD_TOKEN")

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

async def main():
    await bot.load_extension("roblox_status")
    await bot.start(TOKEN)

import asyncio
asyncio.run(main())