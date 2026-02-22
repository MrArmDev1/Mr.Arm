import discord
from discord.ext import commands, tasks
from discord import app_commands
import aiohttp
import json
import os
from datetime import datetime

UPDATE_INTERVAL = 300  # 5 นาที
CONFIG_FILE = "roblox_config.json"


# ================== CONFIG ==================
def load_config():
    if not os.path.exists(CONFIG_FILE):
        return {}
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_config(data):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


def add_game_group(guild_id, universe_id, group_id, channel_id):
    data = load_config()
    gid = str(guild_id)

    if gid not in data:
        data[gid] = []

    data[gid].append({
        "universe_id": universe_id,
        "group_id": group_id,
        "channel_id": channel_id,
        "message_id": None
    })

    save_config(data)


# ================== VIEW ==================
class JoinGameView(discord.ui.View):
    def __init__(self, game_link):
        super().__init__(timeout=None)
        self.add_item(
            discord.ui.Button(
                label="🎮 Join Game",
                url=game_link,
                style=discord.ButtonStyle.link
            )
        )


# ================== COG ==================
class RobloxStatus(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.update_status.start()  # ✅ FIX: ชื่อ loop ต้องตรง

    def cog_unload(self):
        self.update_status.cancel()

    # ---------- ROBLOX API ----------
    async def fetch_game(self, universe_id):
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"https://games.roblox.com/v1/games?universeIds={universe_id}"
            ) as r:
                return (await r.json())["data"][0]

    async def fetch_thumbnail(self, universe_id):
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"https://thumbnails.roblox.com/v1/games/icons"
                f"?universeIds={universe_id}&size=512x512&format=Png"
            ) as r:
                return (await r.json())["data"][0]["imageUrl"]

    async def fetch_group(self, group_id):
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"https://groups.roblox.com/v1/groups/{group_id}"
            ) as r:
                return await r.json()

    # ---------- EMBED ----------
    def build_embed(self, game, group, thumbnail):
        players = game["playing"]
        status = "🟢 ONLINE" if players > 0 else "🔴 OFFLINE"

        embed = discord.Embed(
            title=game["name"],
            description=f"**STATUS:** {status}",
            color=discord.Color.green() if players > 0 else discord.Color.red()
        )

        embed.set_thumbnail(url=thumbnail)

        embed.add_field(name="👥 Active Players", value=players)
        embed.add_field(name="👣 Visits", value=game["visits"])
        embed.add_field(name="⭐ Favorites", value=game["favoritedCount"])
        embed.add_field(name="🎮 Max Players", value=game["maxPlayers"])
        embed.add_field(name="🏷 Genre", value=game["genre"] or "All")

        embed.add_field(
            name="👪 Group",
            value=f"[{group['name']}](https://www.roblox.com/groups/{group['id']})\n"
                  f"Members: {group['memberCount']}",
            inline=False
        )

        updated = int(datetime.fromisoformat(
            game["updated"].replace("Z", "")
        ).timestamp())

        embed.add_field(
            name="🔄 Updated",
            value=f"<t:{updated}:R>",
            inline=False
        )

        return embed

    # ---------- SLASH COMMAND ----------
    @app_commands.command(
        name="roblox_add_game_group",
        description="Add Roblox game + group status"
    )
    @app_commands.describe(
        universe_id="Roblox Universe ID",
        group_id="Roblox Group ID",
        channel="Channel to send status"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def add_game_group_cmd(
        self,
        interaction: discord.Interaction,
        universe_id: int,
        group_id: int,
        channel: discord.TextChannel
    ):
        add_game_group(interaction.guild.id, universe_id, group_id, channel.id)
        await interaction.response.send_message(
            "✅ Roblox game + group added",
            ephemeral=True
        )

    # ---------- LOOP ----------
    @tasks.loop(seconds=UPDATE_INTERVAL)
    async def update_status(self):
        print("🔄 update_status loop running")

        data = load_config()
        for guild_id, games in data.items():
            guild = self.bot.get_guild(int(guild_id))
            if not guild:
                continue

            for cfg in games:
                channel = guild.get_channel(cfg["channel_id"])
                if not channel:
                    continue

                game = await self.fetch_game(cfg["universe_id"])
                group = await self.fetch_group(cfg["group_id"])
                thumbnail = await self.fetch_thumbnail(cfg["universe_id"])

                embed = self.build_embed(game, group, thumbnail)
                view = JoinGameView(
                    f"https://www.roblox.com/games/{game['rootPlaceId']}"
                )

                try:
                    if cfg["message_id"]:
                        msg = await channel.fetch_message(cfg["message_id"])
                        await msg.edit(embed=embed, view=view)
                    else:
                        sent = await channel.send(embed=embed, view=view)
                        cfg["message_id"] = sent.id
                        save_config(data)
                except:
                    sent = await channel.send(embed=embed, view=view)
                    cfg["message_id"] = sent.id
                    save_config(data)

    @update_status.before_loop
    async def before_update(self):
        await self.bot.wait_until_ready()


async def setup(bot):
    await bot.add_cog(RobloxStatus(bot))