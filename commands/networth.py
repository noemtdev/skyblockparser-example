import discord
from discord import slash_command, option
from discord.ext import commands
from util.cog import Cog
from util.profile_autocomplete import get_profiles, get_uuid, gamemode_to_emoji
from skyblockparser.profile import SkyblockParser
from numerize.numerize import numerize
from util.views import NetworthProfileSelector


def get_embed(text, bot: commands.Bot):
    embed = discord.Embed(
        description=text,
        color=discord.Color.blurple()
    ).set_author(name=bot.user.name, icon_url=bot.user.avatar.url if bot.user.avatar else bot.user.default_avatar.url)
    return embed


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


class Networth(Cog):
    def __init__(self, bot):
        self.bot = bot
        super().__init__()

    @slash_command(
        name="networth",
        description="Get the networth of a player",
    )
    @option(
        name="player",
        description="The player to get the networth of",
        required=True,
        type=str,
    )
    @option(
        name="profile",
        description="The profile to get the networth of",
        required=False,
        type=str,
        autocomplete=get_profiles
    )
    async def networth(self, ctx, name: str, profile: str = "selected"):
        await ctx.defer()

        _uuid = await get_uuid(self.bot.session, name, True)
        if _uuid == "Invalid username.":
            return await ctx.respond(embed=get_embed("Invalid username.", self.bot))
        

        uuid = _uuid["id"]
        username = _uuid["name"]

        cached_data = self.bot.cache.get(uuid)
        if not cached_data:
            async with self.bot.session.get(f"https://api.hypixel.net/v2/skyblock/profiles?key={self.hypixel_api_key}&uuid={uuid}") as request:
                data = await request.json()
                if data["success"] is False:
                    return await ctx.respond(embed=get_embed("Something went wrong.", self.bot))

                if data["profiles"] is None:
                    return await ctx.respond(embed=get_embed("No profiles found.", self.bot))
                
            parser = SkyblockParser(data, uuid, self.hypixel_api_key)

        else:
            parser = cached_data["uuid"]
            
        order = ["armor", "equipment", "wardrobe", "inventory", "enderchest", "storage", "personal_vault", "pets", "museum"]
        # possible types: "armor", "equipment", "wardrobe", "inventory", "enderchest", "storage", "personal_vault", "pets", "museum", "fishing_bag", "potion_bag", "candy_inventory", "essence", "sacks"

        self.bot.cache[uuid] = parser

        profile.replace(" 🏝", "").replace(" ♻", "").replace(" 🎲", "")
        if profile.endswith(" "):
            profile = profile[:-1]

        profile_data = parser.select_profile(profile)
        await profile_data.init()

        networth = profile_data.networth_data
        embed = discord.Embed(color=discord.Color.blurple())

        profile_type = profile_data.profile_type
        profile_type = gamemode_to_emoji(profile_type)
        cute_name = profile_data.cute_name

        suffix = ""
        if profile_type != " ":
            suffix = f" {profile_type}"

        formatted_username = f"{username}'s"
        if username.endswith("s"):
            formatted_username = f"{username}'"

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

        await ctx.respond(embed=embed, view=NetworthProfileSelector(username, self.bot, parser))


def setup(bot):
    bot.add_cog(Networth(bot))
