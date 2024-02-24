import discord
from discord.ext import commands, tasks
import os, aiohttp

from constants import DISCORD_BOT_TOKEN


class Bot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.command_prefix = ">"
        self.owner_ids = []
        self.token = DISCORD_BOT_TOKEN
        self.session = None
        self.cache = {}

        for filename in os.listdir("commands"):
            if filename.endswith(".py"):
                self.load_extension(f"commands.{filename[:-3]}")

    @tasks.loop(seconds=60)
    async def clear_cache(self):
        self.cache = {}

    async def on_ready(self):
        self.clear_cache.start()
        self.session = aiohttp.ClientSession()
        print(f"Logged in as {self.user}")

    def run(self):
        self.loop.create_task(self.start(self.token))
        self.loop.run_forever()


intents = discord.Intents.default()
bot = Bot(command_prefix=">", intents=intents)

bot.run()