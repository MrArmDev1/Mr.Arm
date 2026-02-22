import json
import os

FILE = "roblox_config.json"

def _load():
    if not os.path.exists(FILE):
        with open(FILE, "w") as f:
            json.dump({}, f)
    with open(FILE, "r") as f:
        return json.load(f)

def _save(data):
    with open(FILE, "w") as f:
        json.dump(data, f, indent=2)

def add_game(guild_id, universe_id, group_id, channel_id):
    data = _load()
    guild = data.setdefault(str(guild_id), {})
    guild[str(universe_id)] = {
        "universe_id": universe_id,
        "group_id": group_id,
        "channel_id": channel_id,
        "message_id": None
    }
    _save(data)

def get_games(guild_id):
    return _load().get(str(guild_id), {})

def set_message_id(guild_id, universe_id, message_id):
    data = _load()
    data[str(guild_id)][str(universe_id)]["message_id"] = message_id
    _save(data)