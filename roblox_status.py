import discord
from discord.ext import commands, tasks
from discord import app_commands
import aiohttp
from datetime import datetime

import roblox_config

UPDATE_INTERVAL = 300  # 5 minutes

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

class RobloxStatus(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.update_loop.start()

    def cog_unload(self):
        self.update_loop.cancel()

    async def fetch_game(self, universe_id):
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"https://games.roblox.com/v1/games?universeIds={universe_id}"
            ) as r:
                return (await r.json())["data"][0]

    async def fetch_thumbnail(self, universe_id):
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"https://thumbnails.roblox.com/v1/games/icons?universeIds={universe_id}&size=512x512&format=Png"
            ) as r:
                return (await r.json())["data"][0]["imageUrl"]

    async def fetch_group(self, group_id):
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"https://groups.roblox.com/v1/groups/{group_id}"
            ) as r:
                return await r.json()

    def build_embed(self, game, group, thumb):
        players = game["playing"]
        status = "🟢 ONLINE" if players > 0 else "🔴 OFFLINE"

        embed = discord.Embed(
            title=game["name"],
            description=f"**STATUS:** {status}",
            color=discord.Color.green() if players > 0 else discord.Color.red()
        )

        embed.set_thumbnail(url=thumb)

        embed.add_field(name="👥 Active Players", value=players)
        embed.add_field(name="👣 Visits", value=game["visits"])
        embed.add_field(name="⭐ Favorites", value=game["favoritedCount"])
        embed.add_field(name="🏢 Group", value=f"[{group['name']}](https://www.roblox.com/communities/{group['id']})")
        embed.add_field(name="👤 Group Members", value=group["memberCount"])

        updated = int(datetime.fromisoformat(game["updated"].replace("Z", "")).timestamp())
        embed.add_field(name="🔄 Updated", value=f"<t:{updated}:R>", inline=False)

        return embed

    @app_commands.command(
        name="roblox_add_game_group",
        description="Add Roblox game + group status to a channel"
    )
    @app_commands.describe(
        universe_id="Roblox Universe ID",
        group_id="Roblox Group ID",
        channel="Channel to send status"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def add_game(
        self,
        interaction: discord.Interaction,
        universe_id: int,
        group_id: int,
        channel: discord.TextChannel
    ):
        roblox_config.add_game(
            interaction.guild.id,
            universe_id,
            group_id,
            channel.id
        )
        await interaction.response.send_message(
            "✅ Roblox game + group added",
            ephemeral=True
        )

    @tasks.loop(seconds=UPDATE_INTERVAL)
    async def update_loop(self):
        for guild in self.bot.guilds:
            games = roblox_config.get_games(guild.id)
            for universe_id, cfg in games.items():
                channel = guild.get_channel(cfg["channel_id"])
                if not channel:
                    continue

                game = await self.fetch_game(cfg["universe_id"])
                group = await self.fetch_group(cfg["group_id"])
                thumb = await self.fetch_thumbnail(cfg["universe_id"])

                embed = self.build_embed(game, group, thumb)
                view = JoinGameView(f"https://www.roblox.com/games/{game['rootPlaceId']}")

                try:
                    if cfg["message_id"]:
                        msg = await channel.fetch_message(cfg["message_id"])
                        await msg.edit(embed=embed, view=view)
                    else:
                        sent = await channel.send(embed=embed, view=view)
                        roblox_config.set_message_id(
                            guild.id,
                            cfg["universe_id"],
                            sent.id
                        )
                except:
                    sent = await channel.send(embed=embed, view=view)
                    roblox_config.set_message_id(
                        guild.id,
                        cfg["universe_id"],
                        sent.id
                    )

    @update_loop.before_loop
    async def before_loop(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(RobloxStatus(bot))