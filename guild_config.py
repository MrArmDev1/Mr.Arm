import json
import os

FILE = "guild_config.json"


def _load():
    if not os.path.exists(FILE):
        with open(FILE, "w") as f:
            json.dump({}, f)
    with open(FILE, "r") as f:
        return json.load(f)


def _save(data):
    with open(FILE, "w") as f:
        json.dump(data, f, indent=2)


# ---------- ROBLOX STATUS (MULTI GAME) ----------

def add_game(guild_id, universe_id, channel_id):
    data = _load()
    guild = data.setdefault(str(guild_id), {})
    roblox = guild.setdefault("roblox_status", {})
    games = roblox.setdefault("games", {})

    games[str(universe_id)] = {
        "channel_id": channel_id,
        "message_id": None,
        "group_id": None
    }

    _save(data)


def set_game_group(guild_id, universe_id, group_id):
    data = _load()
    game = (
        data.get(str(guild_id), {})
        .get("roblox_status", {})
        .get("games", {})
        .get(str(universe_id))
    )

    if game is not None:
        game["group_id"] = group_id
        _save(data)


def set_message_id(guild_id, universe_id, message_id):
    data = _load()
    game = (
        data.get(str(guild_id), {})
        .get("roblox_status", {})
        .get("games", {})
        .get(str(universe_id))
    )

    if game is not None:
        game["message_id"] = message_id
        _save(data)


def get_games(guild_id):
    return (
        _load()
        .get(str(guild_id), {})
        .get("roblox_status", {})
        .get("games", {})
    )