import os
import discord
from discord.ext import commands
import asyncio

# ---------- TOKEN ----------
TOKEN = os.getenv("DISCORD_TOKEN")  # Railway / .env

# ---------- INTENTS ----------
intents = discord.Intents.default()
intents.message_content = True   # ❗ สำคัญมาก (prefix command)
intents.guilds = True
intents.members = True

# ---------- BOT ----------
bot = commands.Bot(
    command_prefix="!",   # ใช้ !setchannel !addgame
    intents=intents
)

# ---------- EVENTS ----------
@bot.event
async def on_ready():
    print(f"🤖 Logged in as {bot.user} ({bot.user.id})")

# ---------- LOAD EXTENSIONS ----------
EXTENSIONS = [
    "roblox_status"   # ชื่อไฟล์ roblox_status.py
]

async def load_extensions():
    for ext in EXTENSIONS:
        try:
            await bot.load_extension(ext)
            print(f"✅ Loaded {ext}.py")
        except Exception as e:
            print(f"❌ Failed to load {ext}.py → {e}")

# ---------- START ----------
async def main():
    if not TOKEN:
        print("❌ DISCORD_TOKEN not found")
        return

    async with bot:
        await load_extensions()
        await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())