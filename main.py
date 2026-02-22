import os
import asyncio
import discord
from discord.ext import commands

# ---------- CONFIG ----------
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.message_content = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)

# ---------- EVENTS ----------
@bot.event
async def on_ready():
    print(f"🤖 Logged in as {bot.user} ({bot.user.id})")

    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} slash commands")
    except Exception as e:
        print(f"❌ Slash command sync failed: {e}")

# ---------- LOAD EXTENSIONS ----------
EXTENSIONS = [
    "roblox_status"  # 👈 ระบบ Roblox (หลายเกม + ปุ่ม Join + Thumbnail)
]

async def load_extensions():
    for ext in EXTENSIONS:
        try:
            await bot.load_extension(ext)
            print(f"📦 Loaded {ext}.py")
        except Exception as e:
            print(f"⚠️ Failed to load {ext}.py → {e}")

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
