import discord
from discord.ext import commands, tasks
from discord.ui import View, select
from skyblockparser.profile import SkyblockParser
from numerize.numerize import numerize
from util.profile_autocomplete import gamemode_to_emoji


def generate_embed_networth_field(items, total_value, name):
    items_string = ""
    for item in enumerate(items):
        if item[0] == 5:
            items_string += f"**... {len(items) - 5} more**"
            break

        suffix = ""
        for calc in item[1]["calculation"]:
            if calc["id"] == "RECOMBOBULATOR_3000":
                suffix += f"⬆️"  # recomb emoji

        items_string += f"→ {count(item[1])} {suffix} (**{numerize(item[1]['price'])}**)\n"

    return {
        "name": f"{name} ({numerize(total_value)})",
        "value": items_string,
        "inline": False
    }


def count(item):
    if item.get("count", 1) == 1:
        return item.get("name")

    else:
        return f"`{item['count']}x` {item.get('name')}"

class NetworthProfileSelector(View):
    def __init__(self, username, bot, parser: SkyblockParser, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser = parser
        self.bot = bot

        self.profiles = parser.get_profiles()
        self.children[0].options = [discord.SelectOption(label=profile, value=profile) for profile in self.profiles]
        self.counter = 0
        self.trigger_timeout.start()
        self.username = username

    @tasks.loop(seconds=180)
    async def trigger_timeout(self):
        self.counter += 1
        if self.counter == 2:
            for child in self.children:
                child.disabled = True

            self.bot.authing[str(self.user.id)] = {}

            try:
                await self.message.edit_original_response(view=self)
                self.stop()

            except discord.errors.NotFound:
                self.stop()
                return
            
    @select(
        placeholder="Select a profile",
    )
    async def select_profile(self, select:discord.ui.Select, interaction:discord.Interaction):
        await interaction.response.defer()

        order = ["armor", "equipment", "wardrobe", "inventory", "enderchest", "storage", "personal_vault", "pets", "museum"]
        # possible types: "armor", "equipment", "wardrobe", "inventory", "enderchest", "storage", "personal_vault", "pets", "museum", "fishing_bag", "potion_bag", "candy_inventory", "essence", "sacks"

        profile_data = self.parser.select_profile(select.values[0])
        await profile_data.init()

        networth = profile_data.networth_data
        embed = discord.Embed(color=discord.Color.blurple())

        profile_type = profile_data.profile_type
        profile_type = gamemode_to_emoji(profile_type)
        cute_name = profile_data.cute_name

        suffix = ""
        if profile_type != " ":
            suffix = f" {profile_type}"

        formatted_username = f"{self.username}'s"
        if self.username.endswith("s"):
            formatted_username = f"{self.username}'"

        embed.title = f"{formatted_username} {cute_name} Profile{suffix}"

        networth_total = networth.get("networth", 0)
        embed.description = f"Networth: **{format(int(networth_total), ',d')}** (**{numerize(networth_total)}**)"
        purse = networth.get("purse", 0)
        bank = networth.get("bank", 0)

        networth_types = networth.get("types")
        if not networth_types:
            networth_types = {}

        sacks = networth_types.get("sacks", 0)
        essence = networth_types.get("essence", 0)

        embed.add_field(
            name="Coins",
            value=numerize(purse + bank),
        )

        embed.add_field(
            name="Sacks",
            value=numerize(sacks["total"]),
        )

        embed.add_field(
            name="Essence",
            value=numerize(essence["total"]),
        )

        for networth_type in order:
            type_data = networth_types[networth_type]
            total_value = type_data.get("total", 0)
            items = type_data.get("items", [])

            field = generate_embed_networth_field(items, total_value, networth_type.replace("_", " ").title())
            embed.add_field(**field)

        await interaction.edit_original_response(embed=embed)