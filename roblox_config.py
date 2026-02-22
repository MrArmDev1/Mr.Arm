import json, os

FILE = "roblox_config.json"

def load():
    if not os.path.exists(FILE):
        with open(FILE, "w") as f:
            json.dump({}, f)
    with open(FILE, "r") as f:
        return json.load(f)

def save(data):
    with open(FILE, "w") as f:
        json.dump(data, f, indent=2)

def add_game(guild_id, universe_id, channel_id):
    data = load()
    guild = data.setdefault(str(guild_id), {})
    games = guild.setdefault("games", {})

    games[str(universe_id)] = {
        "channel_id": channel_id,
        "message_id": None
    }
    save(data)

def get_games(guild_id):
    return load().get(str(guild_id), {}).get("games", {})

def set_message_id(guild_id, universe_id, message_id):
    data = load()
    data[str(guild_id)]["games"][str(universe_id)]["message_id"] = message_id
    save(data)