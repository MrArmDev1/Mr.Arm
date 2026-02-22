# ----- ROBLOX STATUS -----

def set_status_config(guild_id, universe_id, channel_id):
    data = _load()
    guild = data.setdefault(str(guild_id), {})
    guild["roblox_status"] = {
        "universe_id": universe_id,
        "channel_id": channel_id,
        "message_id": None
    }
    _save(data)

def get_status_config(guild_id):
    return _load().get(str(guild_id), {}).get("roblox_status")

def set_message_id(guild_id, message_id):
    data = _load()
    guild = data.setdefault(str(guild_id), {})
    if "roblox_status" in guild:
        guild["roblox_status"]["message_id"] = message_id
    _save(data)