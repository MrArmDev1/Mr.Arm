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

def set_status_config(guild_id, universe_id, channel_id):
    data = _load()
    guild = data.setdefault(str(guild_id), {})
    guild["universe_id"] = universe_id
    guild["channel_id"] = channel_id
    guild.setdefault("message_id", None)
    guild.setdefault("group_id", None)
    _save(data)

def set_message_id(guild_id, message_id):
    data = _load()
    if str(guild_id) in data:
        data[str(guild_id)]["message_id"] = message_id
        _save(data)

def set_group_id(guild_id, group_id):
    data = _load()
    guild = data.setdefault(str(guild_id), {})
    guild["group_id"] = group_id
    _save(data)

def get_status_config(guild_id):
    return _load().get(str(guild_id))