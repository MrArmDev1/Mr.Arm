import discord
from discord.ext import commands, tasks
from discord import app_commands
import aiohttp
from datetime import datetime
import json
import os

UPDATE_INTERVAL = 300  # 5 นาที
DATA_FILE = "roblox_status.json"

# ---------- STORAGE ----------
def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

def set_game_group(guild_id, universe_id, group_id, channel_id):
    data = load_data()
    data[str(guild_id)] = {
        "universe_id": universe_id,
        "group_id": group_id,
        "channel_id": channel_id,
        "message_id": None
    }
    save_data(data)

def set_message_id(guild_id, message_id):
    data = load_data()
    if str(guild_id) in data:
        data[str(guild_id)]["message_id"] = message_id
        save_data(data)

def get_config(guild_id):
    return load_data().get(str(guild_id))


# ---------- COG ----------
class RobloxStatus(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.update_status.start()

    def cog_unload(self):
        self.update_status.cancel()

    # ---------- ROBLOX API ----------
    async def fetch_game(self, universe_id):
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"https://games.roblox.com/v1/games?universeIds={universe_id}"
            ) as r:
                data = await r.json()
                return data["data"][0]

    async def fetch_group(self, group_id):
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"https://groups.roblox.com/v1/groups/{group_id}"
            ) as r:
                return await r.json()

    # ---------- EMBED ----------
    def build_embed(self, game, group):
        players = game["playing"]
        status = "🟢 ONLINE" if players > 0 else "🔴 OFFLINE"

        embed = discord.Embed(
            title=game["name"],
            description=f"**STATUS:** {status}",
            color=discord.Color.green() if players > 0 else discord.Color.red()
        )

        embed.add_field(name="👥 Active Players", value=players)
        embed.add_field(name="👣 Visits", value=game["visits"])
        embed.add_field(name="⭐ Favorites", value=game["favoritedCount"])
        embed.add_field(name="🎮 Max Players", value=game["maxPlayers"])
        embed.add_field(name="👥 Group Members", value=group["memberCount"])

        updated = int(datetime.fromisoformat(
            game["updated"].replace("Z", "")
        ).timestamp())

        embed.add_field(
            name="🔄 Updated",
            value=f"<t:{updated}:R>",
            inline=False
        )

        embed.add_field(
            name="🔗 Links",
            value=(
                f"[🎮 Join Game](https://www.roblox.com/games/{game['rootPlaceId']})\n"
                f"[👥 Group](https://www.roblox.com/groups/{group['id']})"
            ),
            inline=False
        )

        if game.get("iconImageAssetId"):
            embed.set_thumbnail(
                url=f"https://www.roblox.com/asset-thumbnail/image?assetId={game['iconImageAssetId']}&width=420&height=420&format=png"
            )

        embed.set_footer(text=f"Universe ID: {game['id']}")
        return embed

    # ---------- SLASH COMMAND ----------
    @app_commands.command(
        name="roblox_add_game_group",
        description="Add Roblox game + group status to a channel"
    )
    @app_commands.describe(
        universe_id="Roblox Universe ID",
        group_id="Roblox Group ID",
        channel="Channel to show status"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def add_game_group(
        self,
        interaction: discord.Interaction,
        universe_id: int,
        group_id: int,
        channel: discord.TextChannel
    ):
        set_game_group(interaction.guild.id, universe_id, group_id, channel.id)
        await interaction.response.send_message(
            "✅ Roblox game + group status configured",
            ephemeral=True
        )

    # ---------- LOOP ----------
    @tasks.loop(seconds=UPDATE_INTERVAL)
    async def update_status(self):
        for guild in self.bot.guilds:
            config = get_config(guild.id)
            if not config:
                continue

            channel = guild.get_channel(config["channel_id"])
            if not channel:
                continue

            try:
                game = await self.fetch_game(config["universe_id"])
                group = await self.fetch_group(config["group_id"])
                embed = self.build_embed(game, group)

                if config["message_id"]:
                    msg = await channel.fetch_message(config["message_id"])
                    await msg.edit(embed=embed)
                else:
                    sent = await channel.send(embed=embed)
                    set_message_id(guild.id, sent.id)
            except:
                pass

    @update_status.before_loop
    async def before_update(self):
        await self.bot.wait_until_ready()


async def setup(bot):
    await bot.add_cog(RobloxStatus(bot))