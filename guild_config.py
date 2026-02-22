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

# ---------- ROBLOX STATUS ----------

def set_status_config(guild_id, universe_id, channel_id):
    data = _load()
    guild = data.setdefault(str(guild_id), {})
    guild["roblox_status"] = {
        "universe_id": universe_id,
        "channel_id": channel_id,
        "message_id": None,
        "group_id": None
    }
    _save(data)

def set_group(guild_id, group_id):
    data = _load()
    guild = data.setdefault(str(guild_id), {})
    if "roblox_status" in guild:
        guild["roblox_status"]["group_id"] = group_id
    _save(data)

def get_status_config(guild_id):
    return _load().get(str(guild_id), {}).get("roblox_status")

def set_message_id(guild_id, message_id):
    data = _load()
    guild = data.setdefault(str(guild_id), {})
    if "roblox_status" in guild:
        guild["roblox_status"]["message_id"] = message_id
    _save(data)