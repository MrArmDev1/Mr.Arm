import discord
from discord.ext import commands, tasks
import aiohttp
from datetime import datetime, timezone
import os

# ========= CONFIG =========
TOKEN = os.getenv("DISCORD_TOKEN")  # ตั้งชื่อ ENV ให้ตรงใน Railway

UPDATE_MINUTES = 5

CHANNEL_ID = 1466099906526842962  # ตั้งค่าห้องไว้แล้ว

GAMES = [
    {
        "name": "Anime Guardians",
        "place_id": 17282336195,
        "group_id": 10749844,
        "message_id": None
    },
    {
        "name": "Anime Reversal",
        "place_id": 8966502575,
        "group_id": 414406594,
        "message_id": None
    }
]
# ==========================

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    auto_update.start()

@bot.command()
@commands.has_permissions(administrator=True)
async def sendnow(ctx):
    await update_games(force=True)
    await ctx.send("✅ ส่งข้อมูลเกมทันทีเรียบร้อย")

async def update_games(force=False):
    channel = bot.get_channel(CHANNEL_ID)
    if not channel:
        print("❌ ไม่เจอ Channel")
        return

    async with aiohttp.ClientSession() as session:
        for game in GAMES:

            # -------- GAME API --------
            game_api = f"https://games.roblox.com/v1/games?placeIds={game['place_id']}"
            async with session.get(game_api) as r:
                game_json = await r.json()

            if "data" not in game_json or not game_json["data"]:
                print(f"[WARN] ไม่มีข้อมูลเกม {game['place_id']}")
                continue

            g = game_json["data"][0]

            # -------- GROUP API --------
            group_api = f"https://groups.roblox.com/v1/groups/{game['group_id']}"
            async with session.get(group_api) as r:
                group = await r.json()

            # -------- THUMBNAIL --------
            thumb_api = (
                f"https://thumbnails.roblox.com/v1/places/gameicons"
                f"?placeIds={game['place_id']}&size=512x512&format=Png"
            )
            async with session.get(thumb_api) as r:
                thumb_json = await r.json()
                thumb = None
                if "data" in thumb_json and thumb_json["data"]:
                    thumb = thumb_json["data"][0]["imageUrl"]

            embed = discord.Embed(
                title=f"🔥 {game['name']}",
                color=discord.Color.green(),
                timestamp=datetime.now(timezone.utc)
            )

            embed.add_field(name="STATUS", 
                            value="🟢 ONLINE" if g["playing"] > 0 else "🔴 OFFLINE",
                            inline=False)
            embed.add_field(name="👥 Active Players", 
                            value=f"{g['playing']:,}")
            embed.add_field(name="👣 Visits", 
                            value=f"{g['visits']:,}")
            embed.add_field(name="⭐ Favorites", 
                            value=f"{g['favoritedCount']:,}")
            embed.add_field(name="🎮 Max Players", 
                            value=g["maxPlayers"])

            embed.add_field(
                name="🔗 Game",
                value=f"[คลิกเพื่อเล่น](https://www.roblox.com/games/{game['place_id']})",
                inline=False
            )

            embed.add_field(
                name="👥 Group",
                value=(
                    f"[{group.get('name','Unknown Group')}]"
                    f"(https://www.roblox.com/groups/{game['group_id']})\n"
                    f"Members: **{group.get('memberCount',0):,}**"
                ),
                inline=False
            )

            if thumb:
                embed.set_thumbnail(url=thumb)

            embed.set_footer(text="Updated")

            # -------- SEND or EDIT --------
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
    await update_games()

bot.run(TOKEN)