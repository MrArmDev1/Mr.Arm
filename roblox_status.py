import discord
from discord.ext import commands, tasks
import aiohttp
import json
from datetime import datetime, timezone

DATA_FILE = "data.json"

def load():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

class RobloxStatus(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.loop.start()

    def cog_unload(self):
        self.loop.cancel()

    # ---------- COMMANDS ----------
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setchannel(self, ctx, channel: discord.TextChannel):
        data = load()
        data["channel_id"] = channel.id
        save(data)
        await ctx.send(f"✅ ตั้งห้องเป็น {channel.mention}")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def addgame(self, ctx, name, place_id: int, group_id: int):
        data = load()
        data["games"].append({
            "name": name,
            "place_id": place_id,
            "group_id": group_id,
            "message_id": None
        })
        save(data)
        await ctx.send(f"✅ เพิ่มเกม **{name}** แล้ว")

    # ---------- LOOP ----------
    @tasks.loop(minutes=5)
    async def loop(self):
        data = load()
        if not data["channel_id"]:
            return

        channel = self.bot.get_channel(data["channel_id"])
        if not channel:
            return

        async with aiohttp.ClientSession() as session:
            for game in data["games"]:

                # -------- GAME INFO --------
                game_api = f"https://games.roblox.com/v1/games?placeIds={game['place_id']}"
                async with session.get(game_api) as r:
                    g = (await r.json())["data"][0]

                # -------- GROUP INFO --------
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

        save(data)

    @loop.before_loop
    async def before(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(RobloxStatus(bot))