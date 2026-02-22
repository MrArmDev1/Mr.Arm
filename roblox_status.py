import discord
from discord.ext import commands, tasks
from discord import app_commands
import aiohttp
from datetime import datetime
import guild_config

UPDATE_INTERVAL = 300  # 5 นาที


class RobloxStatus(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ---------- ROBLOX API ----------
    async def fetch_game(self, universe_id):
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"https://games.roblox.com/v1/games?universeIds={universe_id}"
            ) as r:
                if r.status != 200:
                    return None
                data = await r.json()
                return data["data"][0] if data["data"] else None

    async def fetch_group(self, group_id):
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"https://groups.roblox.com/v1/groups/{group_id}"
            ) as r:
                if r.status != 200:
                    return None
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

        if group:
            embed.add_field(
                name="👨‍👩‍👧‍👦 Group",
                value=(
                    f"**{group['name']}**\n"
                    f"Members: {group['memberCount']}\n"
                    f"[View Group](https://www.roblox.com/groups/{group['id']})"
                ),
                inline=False
            )

        updated = int(
            datetime.fromisoformat(
                game["updated"].replace("Z", "")
            ).timestamp()
        )
        embed.add_field(name="🔄 Updated", value=f"<t:{updated}:R>", inline=False)
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
    async def setup(self, interaction, universe_id: int, channel: discord.TextChannel):
        guild_config.set_status_config(
            interaction.guild.id,
            universe_id,
            channel.id
        )
        await interaction.response.send_message(
            "✅ Roblox status configured",
            ephemeral=True
        )

    @app_commands.command(
        name="roblox_add_game_group",
        description="Link Roblox group to current game"
    )
    @app_commands.describe(
        group_id="Roblox Group ID"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def add_group(self, interaction, group_id: int):
        guild_config.set_group(interaction.guild.id, group_id)
        await interaction.response.send_message(
            "✅ Roblox group linked to game",
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

                group = None
                if config.get("group_id"):
                    group = await self.fetch_group(config["group_id"])

                embed = self.build_embed(game, group)

                try:
                    if config.get("message_id"):
                        msg = await channel.fetch_message(config["message_id"])
                        await msg.edit(embed=embed)
                    else:
                        sent = await channel.send(embed=embed)
                        guild_config.set_message_id(guild.id, sent.id)
                except:
                    sent = await channel.send(embed=embed)
                    guild_config.set_message_id(guild.id, sent.id)

        except Exception as e:
            print("❌ RobloxStatus error:", e)

    @update_status.before_loop
    async def before_update(self):
        await self.bot.wait_until_ready()
        print("✅ Roblox status loop running")


async def setup(bot):
    cog = RobloxStatus(bot)
    await bot.add_cog(cog)
    cog.update_status.start()