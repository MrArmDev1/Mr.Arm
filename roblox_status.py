import discord
from discord.ext import commands, tasks
from discord import app_commands
import aiohttp
from datetime import datetime
import guild_config

UPDATE_INTERVAL = 300  # 5 minutes


class RobloxStatus(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ---------- ROBLOX API ----------
    async def fetch_game(self, universe_id: int):
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"https://games.roblox.com/v1/games?universeIds={universe_id}"
            ) as r:
                if r.status != 200:
                    return None

                data = await r.json()
                if not data.get("data"):
                    return None

                return data["data"][0]

    def build_embed(self, game: dict):
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
        embed.add_field(name="🏷 Genre", value=game["genre"] or "All")

        updated = int(
            datetime.fromisoformat(
                game["updated"].replace("Z", "")
            ).timestamp()
        )

        embed.add_field(
            name="🔄 Updated",
            value=f"<t:{updated}:R>",
            inline=False
        )

        embed.set_footer(text=f"Universe ID: {game['id']}")
        return embed

    # ---------- SLASH COMMAND ----------
    @app_commands.command(
        name="roblox_status_setup",
        description="Setup Roblox server status system"
    )
    @app_commands.describe(
        universe_id="Roblox Universe ID",
        channel="Channel to show server status"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def setup(
        self,
        interaction: discord.Interaction,
        universe_id: int,
        channel: discord.TextChannel
    ):
        guild_config.set_status_config(
            interaction.guild.id,
            universe_id,
            channel.id
        )

        await interaction.response.send_message(
            "✅ Roblox server status configured",
            ephemeral=True
        )

    # ---------- LOOP ----------
    @tasks.loop(seconds=UPDATE_INTERVAL)
    async def update_status(self):
        try:
            for guild in self.bot.guilds:
                config = guild_config.get_status_config(guild.id)
                if not config:
                    continue

                channel = guild.get_channel(config["channel_id"])
                if not channel:
                    continue

                game = await self.fetch_game(config["universe_id"])
                if not game:
                    continue

                embed = self.build_embed(game)

                try:
                    if config.get("message_id"):
                        msg = await channel.fetch_message(config["message_id"])
                        await msg.edit(embed=embed)
                    else:
                        sent = await channel.send(embed=embed)
                        guild_config.set_message_id(guild.id, sent.id)
                except discord.NotFound:
                    sent = await channel.send(embed=embed)
                    guild_config.set_message_id(guild.id, sent.id)

        except Exception as e:
            print("❌ RobloxStatus loop error:", e)

    @update_status.before_loop
    async def before_update(self):
        await self.bot.wait_until_ready()
        print("✅ Roblox status loop started")


async def setup(bot: commands.Bot):
    cog = RobloxStatus(bot)
    await bot.add_cog(cog)
    cog.update_status.start()