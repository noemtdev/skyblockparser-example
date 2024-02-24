from discord.ext import commands
from constants import HYPIXEL_API_KEY

class Cog(commands.Cog):
    def __init__(self):
        self.hypixel_api_key = HYPIXEL_API_KEY
