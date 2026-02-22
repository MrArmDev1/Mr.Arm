import discord
from discord.ext import commands, tasks
import aiohttp
from datetime import datetime, timezone
import os

# ========= CONFIG =========
TOKEN = os.getenv("TOKEN")  # ใส่ Token ใน Railway
UPDATE_MINUTES = 5

GAMES = [
    {
        "name": "Anime Guardian",
        "place_id": 17282336195,
        "group_id": 10749844,
        "message_id": None
    },
    {
        "name": "Anime Reversal",
        "place_id": 85535589075948,
        "group_id": 414406594,
        "message_id": None
    }
]

CHANNEL_ID = None
# ==========================

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    auto_update.start()


# ---------- COMMANDS ----------
@bot.command()
@commands.has_permissions(administrator=True)
async def setchannel(ctx):
    global CHANNEL_ID
    CHANNEL_ID = ctx.channel.id
    await ctx.send(f"✅ ตั้งห้องนี้เป็นห้อง Game Status แล้ว")


@bot.command()
@commands.has_permissions(administrator=True)
async def sendnow(ctx):
    if not CHANNEL_ID:
        await ctx.send("❌ ยังไม่ได้ตั้งห้อง ใช้ !setchannel ก่อน")
        return

    await update_games(force=True)
    await ctx.send("✅ ส่งข้อมูลเกมทันทีเรียบร้อย")


# ---------- UPDATE LOGIC ----------
async def update_games(force=False):
    global CHANNEL_ID
    channel = bot.get_channel(CHANNEL_ID)
    if not channel:
        return

    async with aiohttp.ClientSession() as session:
        for game in GAMES:

            game_api = f"https://games.roblox.com/v1/games?placeIds={game['place_id']}"
            async with session.get(game_api) as r:
                g = (await r.json())["data"][0]

            group_api = f"https://groups.roblox.com/v1/groups/{game['group_id']}"
            async with session.get(group_api) as r:
                group = await r.json()

            thumb_api = (
                "https://thumbnails.roblox.com/v1/places/gameicons"
                f"?placeIds={game['place_id']}&size=512x512&format=Png"
            )
            async with session.get(thumb_api) as r:
                thumb = (await r.json())["data"][0]["imageUrl"]

            embed = discord.Embed(
                title=f"🔥 {game['name']}",
                color=discord.Color.green(),
                timestamp=datetime.now(timezone.utc)
            )

            embed.add_field(name="STATUS", value="🟢 ONLINE", inline=False)
            embed.add_field(name="👥 Active Players", value=f"{g['playing']:,}")
            embed.add_field(name="👣 Visits", value=f"{g['visits']:,}")
            embed.add_field(name="⭐ Favorites", value=f"{g['favoritedCount']:,}")
            embed.add_field(name="🎮 Max Players", value=g["maxPlayers"])

            embed.add_field(
                name="🔗 Game",
                value=f"[Click to play](https://www.roblox.com/games/{game['place_id']})",
                inline=False
            )

            embed.add_field(
                name="👥 Group",
                value=(
                    f"[{group['name']}](https://www.roblox.com/groups/{game['group_id']})\n"
                    f"Members: **{group['memberCount']:,}**"
                ),
                inline=False
            )

            embed.set_thumbnail(url=thumb)
            embed.set_footer(text="Updated")

            if game["message_id"]:
                try:
                    msg = await channel.fetch_message(game["message_id"])
                    await msg.edit(embed=embed)
                    continue
                except:
                    pass

            msg = await channel.send(embed=embed)
            game["message_id"] = msg.id


@tasks.loop(minutes=UPDATE_MINUTES)
async def auto_update():
    if CHANNEL_ID:
        await update_games()


bot.run(TOKEN)
