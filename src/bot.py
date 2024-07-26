"""Contains the Discord Bot."""

import logging
import os

import discord
from discord.ext import commands

from src.doujin_dao import DoujinDAO
from src.user_dao import UserDAO
from src.currency import Currency
from src.scrape import DoujinScraper
from src.utils import generate_doujin_embed


# Logger
handler = logging.FileHandler(filename="discord.log", encoding="utf-8", mode="w")
discord.utils.setup_logging(handler=handler, root=False)

# Requires message_content intent to work
intents = discord.Intents.default()
intents.message_content = True

# Currency setup
CURRENCY_API_KEY = os.getenv("CURRENCY_API_KEY")
assert CURRENCY_API_KEY is not None
currency = Currency(CURRENCY_API_KEY)

doujin_scraper = DoujinScraper()
doujin_dao = DoujinDAO(os.getenv("DATABASE_URL"))
user_dao = UserDAO(os.getenv("DATABASE_URL"), doujin_dao)


bot = commands.Bot(command_prefix="!", intents=intents, log_handler=handler)


@bot.command(brief="Adds a reservation to doujin to the database")
async def add(ctx: commands.Context, url: str):
    """Command to add a doujin reservation for a user.

    Parameters
    ----------
    ctx : commands.Context
        Discord.py command context.
    url : str
        Melonbooks URL to create a reservation for.

    """

    # TODO: Force updates to doujin/user metadata after a interval of time
    try:
        # Get doujin data if this is the first time
        doujin = doujin_dao.get_doujin_by_url(url)
        if not doujin:
            (
                title,
                price_in_yen,
                circle_name,
                author_names,
                genres,
                events,
                is_r18,
                image_preview_url,
            ) = doujin_scraper.scrape_url(url)
            doujin = doujin_dao.add_doujin(
                url,
                title,
                price_in_yen,
                circle_name,
                author_names,
                genres,
                events,
                is_r18,
                image_preview_url,
            )

    except Exception as e:
        await ctx.send(f"Error: {e}")
        raise e

    try:
        discord_id = ctx.author.id
        user = user_dao.get_user_by_discord_id(discord_id)
        # Creates user on first interaction
        if not user:
            # Add reservation
            name = (
                ctx.author.global_name
                if ctx.author.global_name
                else ctx.author.display_name
            )

            user = user_dao.add_user(discord_id, name)

        if user.has_reserved(doujin._id):
            # Already reserved, print message
            message = f"<@{ctx.author.id}> has already reserved {doujin.title}"
        else:
            # Add reservation
            user_dao.add_reservation(user, doujin)
            message = f"Added reserveration {doujin.title} for <@{ctx.author.id}>"

    except Exception as e:
        await ctx.send(f"Error: {e}")
        raise e

    embed = generate_doujin_embed(doujin, currency)
    await ctx.send(message, embed=embed)


@bot.command(brief="Removes a reservation to doujin to the database")
async def rm(ctx: commands.Context, url: str):
    """Command to rm a doujin reservation for a user.

    Parameters
    ----------
    ctx : commands.Context
        Discord.py command context.
    url : str
        Melonbooks URL to create a reservation for.

    """

    # TODO: Force updates to doujin/user metadata after a interval of time
    try:
        doujin = doujin_dao.get_doujin_by_url(url)
        if not doujin:
            raise Exception("Cannot remove doujin that doesn't exist in the database.")
    except Exception as e:
        await ctx.send(f"Error: {e}")
        raise e

    try:
        discord_id = ctx.author.id
        user = user_dao.get_user_by_discord_id(discord_id)
        # Creates user on first interaction
        if not user:
            raise Exception(
                "Cannot remove doujin from user that doesn't exist in the database."
            )

        if not user.has_reserved(doujin._id):
            # Already reserved, print message
            message = (
                f"<@{ctx.author.id}> has not reserved {doujin.title}, cannot remove."
            )
        else:
            # Add reservation
            user_dao.remove_reservation(user, doujin)
            message = f"Removed reserveration {doujin.title} for <@{ctx.author.id}>"

    except Exception as e:
        await ctx.send(f"Error: {e}")
        raise e

    embed = generate_doujin_embed(doujin, currency)
    await ctx.send(message, embed=embed)
