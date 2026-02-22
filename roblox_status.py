import discord
from discord.ext import commands, tasks
from discord import app_commands
import aiohttp
from datetime import datetime
import guild_config

UPDATE_INTERVAL = 300  # 5 นาที


class JoinGameView(discord.ui.View):
    def __init__(self, universe_id):
        super().__init__(timeout=None)
        self.add_item(
            discord.ui.Button(
                label="🎮 Join Game",
                style=discord.ButtonStyle.link,
                url=f"https://www.roblox.com/games/{universe_id}"
            )
        )


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

    # ---------- EMBED (เดิม + เพิ่ม thumbnail) ----------
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

        # 🖼 Thumbnail เกม
        if game.get("thumbnail"):
            embed.set_thumbnail(url=game["thumbnail"])

        embed.set_footer(text=f"Universe ID: {game['id']}")
        return embed

    # ---------- COMMANDS ----------
    @app_commands.command(
        name="roblox_add_game",
        description="Add Roblox game status"
    )
    @app_commands.describe(
        universe_id="Roblox Universe ID",
        channel="Channel to show status"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def add_game(self, interaction, universe_id: int, channel: discord.TextChannel):
        guild_config.add_game(
            interaction.guild.id,
            universe_id,
            channel.id
        )
        await interaction.response.send_message(
            "✅ Game added",
            ephemeral=True
        )

    @app_commands.command(
        name="roblox_add_game_group",
        description="Link group to a Roblox game"
    )
    @app_commands.describe(
        universe_id="Roblox Universe ID",
        group_id="Roblox Group ID"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def add_group(self, interaction, universe_id: int, group_id: int):
        guild_config.set_game_group(
            interaction.guild.id,
            universe_id,
            group_id
        )
        await interaction.response.send_message(
            "✅ Group linked to game",
            ephemeral=True
        )

    # ---------- LOOP ----------
    @tasks.loop(seconds=UPDATE_INTERVAL)
    async def update_status(self):
        try:
            for guild in self.bot.guilds:
                games = guild_config.get_games(guild.id)
                if not games:
                    continue

                for universe_id, cfg in games.items():
                    channel = guild.get_channel(cfg["channel_id"])
                    if not channel:
                        continue

                    game = await self.fetch_game(int(universe_id))
                    if not game:
                        continue

                    group = None
                    if cfg.get("group_id"):
                        group = await self.fetch_group(cfg["group_id"])

                    embed = self.build_embed(game, group)
                    view = JoinGameView(universe_id)

                    try:
                        if cfg.get("message_id"):
                            msg = await channel.fetch_message(cfg["message_id"])
                            await msg.edit(embed=embed, view=view)
                        else:
                            sent = await channel.send(embed=embed, view=view)
                            guild_config.set_message_id(
                                guild.id,
                                universe_id,
                                sent.id
                            )
                    except:
                        sent = await channel.send(embed=embed, view=view)
                        guild_config.set_message_id(
                            guild.id,
                            universe_id,
                            sent.id
                        )

        except Exception as e:
            print("❌ RobloxStatus error:", e)

    @update_status.before_loop
    async def before_update(self):
        await self.bot.wait_until_ready()
        print("✅ Roblox multi-game status loop running")


async def setup(bot):
    cog = RobloxStatus(bot)
    await bot.add_cog(cog)
    cog.update_status.start()