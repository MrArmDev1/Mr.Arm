import discord
from discord.ext import commands, tasks
import aiohttp
from datetime import datetime, timezone

# ================== ตั้งค่าเกมตรงนี้ ==================
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

CHANNEL_ID = None  # จะตั้งจากคำสั่งใน Discord
# =====================================================

class RobloxStatus(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.update_loop.start()

    def cog_unload(self):
        self.update_loop.cancel()

    # ----------------- คำสั่ง -----------------
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setchannel(self, ctx, channel: discord.TextChannel):
        global CHANNEL_ID
        CHANNEL_ID = channel.id
        await ctx.send(f"✅ ตั้งห้องอัปเดตเป็น {channel.mention}")

    @commands.command()
    async def update(self, ctx):
        await self.send_update(force=True)
        await ctx.send("🔄 อัปเดตข้อมูลทันทีแล้ว")

    # ----------------- LOOP -----------------
    @tasks.loop(minutes=5)
    async def update_loop(self):
        await self.send_update(force=False)

    async def send_update(self, force=False):
        if not CHANNEL_ID:
            return

        channel = self.bot.get_channel(CHANNEL_ID)
        if not channel:
            return

        async with aiohttp.ClientSession() as session:
            for game in GAMES:

                # Game info
                game_api = f"https://games.roblox.com/v1/games?placeIds={game['place_id']}"
                async with session.get(game_api) as r:
                    g = (await r.json())["data"][0]

                # Group info
                group_api = f"https://groups.roblox.com/v1/groups/{game['group_id']}"
                async with session.get(group_api) as r:
                    group = await r.json()

                # Thumbnail
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
                    value=f"[{group['name']}](https://www.roblox.com/groups/{game['group_id']})\n"
                          f"Members: **{group['memberCount']:,}**",
                    inline=False
                )

                embed.set_thumbnail(url=thumb)
                embed.set_footer(text="Updated")

                # ส่ง / แก้ไขข้อความเดิม
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

    @update_loop.before_loop
    async def before_loop(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(RobloxStatus(bot))