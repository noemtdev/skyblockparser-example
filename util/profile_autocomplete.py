import aiohttp
import discord
from constants import HYPIXEL_API_KEY


def gamemode_to_emoji(gamemode):
    if gamemode == "island":
        return "🏝"
    
    elif gamemode in ["normal", None]:
        return ""
    
    elif gamemode == "ironman":
        return "♻"
    
    elif gamemode == "bingo":
        return "🎲"
    
    else:
        return "Unknown"


async def get_uuid(session, username, username_too=False):
    async with session.get(f"https://api.mojang.com/users/profiles/minecraft/{username}") as resp:
        if resp.status in [204, 404]:
            return "Invalid username."
        
        elif resp.status == 200:
            if username_too:
                return await resp.json()
            
            data = await resp.json()
            return data["id"]
    

async def get_profiles(ctx: discord.AutocompleteContext):

    async with aiohttp.ClientSession() as session:
        username = ctx.options["name"]
        uuid = await get_uuid(session, username)
        if uuid == "Invalid username.":
            return ["Invalid username."]
    
        async with session.get(f"https://api.hypixel.net/v2/skyblock/profiles?key={HYPIXEL_API_KEY}&uuid={uuid}") as resp:
            data = await resp.json()
            if data["success"] is False:
                return ["Something went wrong."]
            else:

                if data["profiles"] is None:
                    return ["No profiles found."]
                
                else:
                    return [f"{profile['cute_name']} {gamemode_to_emoji(profile.get('game_mode'))}" for profile in data["profiles"]]