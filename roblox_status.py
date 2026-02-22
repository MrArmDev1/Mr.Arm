import discord
from discord.ext import commands, tasks
from discord import app_commands
import aiohttp
from datetime import datetime

from roblox_config import (
    set_status_config,
    set_message_id,
    set_group_id,
    get_status_config
)

UPDATE_INTERVAL = 300  # 5 นาที

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
    def build_embed(self, game, group=None):
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

        embed.add_field(
            name="🔗 Game",
            value=f"[Click to play](https://www.roblox.com/games/{game['rootPlaceId']})",
            inline=False
        )

        if group:
            embed.add_field(
                name="👥 Group",
                value=(
                    f"[{group['name']}](https://www.roblox.com/groups/{group['id']})\n"
                    f"Members: **{group['memberCount']:,}**"
                ),
                inline=False
            )

        updated = int(
            datetime.fromisoformat(game["updated"].replace("Z", "")).timestamp()
        )

        embed.add_field(
            name="🔄 Updated",
            value=f"<t:{updated}:R>",
            inline=False
        )

        embed.set_footer(text=f"Universe ID: {game['id']}")
        return embed

    # ---------- SLASH COMMANDS ----------
    @app_commands.command(
        name="roblox_status_setup",
        description="Setup Roblox server status"
    )
    @app_commands.describe(
        universe_id="Roblox Universe ID",
        channel="Channel to show status"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def setup(
        self,
        interaction: discord.Interaction,
        universe_id: int,
        channel: discord.TextChannel
    ):
        set_status_config(interaction.guild.id, universe_id, channel.id)
        await interaction.response.send_message(
            "✅ Roblox status system configured",
            ephemeral=True
        )

    @app_commands.command(
        name="roblox_group_set",
        description="Link Roblox group to server status"
    )
    @app_commands.describe(
        group_id="Roblox Group ID"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def set_group(
        self,
        interaction: discord.Interaction,
        group_id: int
    ):
        set_group_id(interaction.guild.id, group_id)
        await interaction.response.send_message(
            "✅ Roblox group linked",
            ephemeral=True
        )

    # ---------- LOOP ----------
    @tasks.loop(seconds=UPDATE_INTERVAL)
    async def update_status(self):
        for guild in self.bot.guilds:
            config = get_status_config(guild.id)
            if not config:
                continue

            channel = guild.get_channel(config["channel_id"])
            if not channel:
                continue

            try:
                game = await self.fetch_game(config["universe_id"])

                group = None
                if config.get("group_id"):
                    group = await self.fetch_group(config["group_id"])

                embed = self.build_embed(game, group)

                if config.get("message_id"):
                    msg = await channel.fetch_message(config["message_id"])
                    await msg.edit(embed=embed)
                else:
                    sent = await channel.send(embed=embed)
                    set_message_id(guild.id, sent.id)

            except Exception as e:
                print(f"[RobloxStatus] Error: {e}")

    @update_status.before_loop
    async def before_update(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(RobloxStatus(bot))