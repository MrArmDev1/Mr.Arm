import discord
from discord.ext import commands, tasks
from discord import app_commands
import aiohttp
from datetime import datetime

from roblox_config import add_game, get_games, set_message_id

UPDATE_INTERVAL = 300

class JoinGameView(discord.ui.View):
    def __init__(self, place_id):
        super().__init__(timeout=None)
        self.add_item(
            discord.ui.Button(
                label="▶ Join Game",
                url=f"https://www.roblox.com/games/{place_id}",
                style=discord.ButtonStyle.link
            )
        )

class RobloxStatus(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.loop.start()

    def cog_unload(self):
        self.loop.cancel()

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
                f"?universeIds={universe_id}&size=512x512&format=Png&isCircular=false"
            ) as r:
                return (await r.json())["data"][0]["imageUrl"]

    def build_embed(self, game, thumbnail):
        players = game["playing"]
        status = "🟢 ONLINE" if players > 0 else "🔴 OFFLINE"

        embed = discord.Embed(
            title=game["name"],
            description=f"**STATUS:** {status}",
            color=discord.Color.green() if players > 0 else discord.Color.red()
        )

        embed.add_field(name="👥 Players", value=players)
        embed.add_field(name="👣 Visits", value=game["visits"])
        embed.add_field(name="⭐ Favorites", value=game["favoritedCount"])
        embed.add_field(name="🎮 Max Players", value=game["maxPlayers"])

        updated = int(datetime.fromisoformat(
            game["updated"].replace("Z", "")
        ).timestamp())

        embed.add_field(
            name="🔄 Updated",
            value=f"<t:{updated}:R>",
            inline=False
        )

        embed.set_thumbnail(url=thumbnail)
        return embed

    # ---------- SLASH COMMAND ----------
    @app_commands.command(
        name="roblox_add_game",
        description="Add Roblox game status to this server"
    )
    @app_commands.describe(
        universe_id="Roblox Universe ID",
        channel="Channel to show status"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def add_game_cmd(self, interaction, universe_id: int, channel: discord.TextChannel):
        add_game(interaction.guild.id, universe_id, channel.id)
        await interaction.response.send_message(
            "✅ Game added to status system",
            ephemeral=True
        )

    # ---------- LOOP ----------
    @tasks.loop(seconds=UPDATE_INTERVAL)
    async def loop(self):
        for guild in self.bot.guilds:
            games = get_games(guild.id)

            for universe_id, cfg in games.items():
                channel = guild.get_channel(cfg["channel_id"])
                if not channel:
                    continue

                try:
                    game = await self.fetch_game(universe_id)
                    thumb = await self.fetch_thumbnail(universe_id)

                    embed = self.build_embed(game, thumb)
                    view = JoinGameView(game["rootPlaceId"])

                    if cfg["message_id"]:
                        msg = await channel.fetch_message(cfg["message_id"])
                        await msg.edit(embed=embed, view=view)
                    else:
                        sent = await channel.send(embed=embed, view=view)
                        set_message_id(guild.id, universe_id, sent.id)

                except Exception as e:
                    print("Roblox error:", e)

    @loop.before_loop
    async def before(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(RobloxStatus(bot))