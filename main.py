import discord
from discord.ext import commands, tasks
import aiohttp
import json
import os
from datetime import datetime, timezone

TOKEN = os.getenv("DISCORD_TOKEN")
DATA_FILE = "data.json"

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ----------------- DATA -----------------
def load_data():
    if not os.path.exists(DATA_FILE):
        return {"channel_id": None, "games": []}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

# ----------------- COMMANDS -----------------
@bot.command()
@commands.has_permissions(administrator=True)
async def setchannel(ctx, channel: discord.TextChannel):
    data = load_data()
    data["channel_id"] = channel.id
    save_data(data)
    await ctx.send(f"✅ ตั้งห้องเป็น {channel.mention}")

@bot.command()
@commands.has_permissions(administrator=True)
async def addgame(ctx, name, place_id: int, group_id: int):
    data = load_data()
    data["games"].append({
        "name": name,
        "place_id": place_id,
        "group_id": group_id,
        "message_id": None
    })
    save_data(data)
    await ctx.send(f"✅ เพิ่มเกม **{name}** แล้ว")

@bot.command()
async def sendnow(ctx):
    await update_games(force=True)
    await ctx.send("✅ ส่งข้อมูลเกมทันทีเรียบร้อย")

# ----------------- UPDATE LOOP -----------------
@tasks.loop(minutes=5)
async def auto_update():
    await update_games()

async def update_games(force=False):
    data = load_data()
    if not data["channel_id"]:
        return

    channel = bot.get_channel(data["channel_id"])
    if not channel:
        return

    async with aiohttp.ClientSession() as session:
        for game in data["games"]:
            try:
                # -------- GAME API --------
                game_api = f"https://games.roblox.com/v1/games?placeIds={game['place_id']}"
                async with session.get(game_api) as r:
                    res = await r.json()

                if not res.get("data"):
                    continue

                g = res["data"][0]

                playing = g.get("playing", 0)

                status = "🟢 ONLINE" if playing > 0 else "🔴 OFFLINE"

                # -------- GROUP API --------
                group_api = f"https://groups.roblox.com/v1/groups/{game['group_id']}"
                async with session.get(group_api) as r:
                    group = await r.json()

                # -------- THUMBNAIL --------
                thumb_api = (
                    "https://thumbnails.roblox.com/v1/places/gameicons"
                    f"?placeIds={game['place_id']}&size=512x512&format=Png"
                )
                async with session.get(thumb_api) as r:
                    thumb = (await r.json())["data"][0]["imageUrl"]

                # -------- EMBED --------
                embed = discord.Embed(
                    title=f"🔥 {game['name']}",
                    color=discord.Color.green() if playing > 0 else discord.Color.red(),
                    timestamp=datetime.now(timezone.utc)
                )

                embed.add_field(name="STATUS", value=status, inline=False)
                embed.add_field(name="👥 Active Players", value=f"{playing:,}")
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
                    value=f"[{group['name']}](https://www.roblox.com/groups/{game['group_id']})\nMembers: **{group['memberCount']:,}**",
                    inline=False
                )

                embed.set_thumbnail(url=thumb)
                embed.set_footer(text="Updated")

                # -------- SEND / EDIT --------
                if game["message_id"]:
                    try:
                        msg = await channel.fetch_message(game["message_id"])
                        await msg.edit(embed=embed)
                    except:
                        msg = await channel.send(embed=embed)
                        game["message_id"] = msg.id
                else:
                    msg = await channel.send(embed=embed)
                    game["message_id"] = msg.id

            except Exception as e:
                print(f"[WARN] {game['name']} error:", e)

    save_data(data)

# ----------------- EVENTS -----------------
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    auto_update.start()

bot.run(TOKEN)