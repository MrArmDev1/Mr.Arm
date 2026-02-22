import discord
from discord.ext import commands
import os

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

async def main():
    async with bot:
        await bot.load_extension("roblox_status")
        await bot.start(os.getenv("TOKEN"))

import asyncio
asyncio.run(main())
