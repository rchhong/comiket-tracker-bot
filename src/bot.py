"""Contains the Discord Bot."""

import logging
import os

import discord
from discord.ext import commands

from src.dao import DAO
from src.currency import Currency
from src.scrape import DoujinScraper
from src.utils import generate_doujin_embed, list_doujins, export_doujin_data


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

# Melonbook Scraper
doujin_scraper = DoujinScraper()

# Database setup
database_url = os.getenv("DATABASE_URL")
assert database_url is not None
dao = DAO(database_url, currency)


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
        doujin = dao.get_doujin_by_url(url)
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
            doujin = dao.add_doujin(
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
        user = dao.get_user_by_discord_id(discord_id)
        # Creates user on first interaction
        if not user:
            # Add reservation
            name = (
                ctx.author.global_name
                if ctx.author.global_name
                else ctx.author.display_name
            )

            user = dao.add_user(discord_id, name)

        if user.has_reserved(doujin._id):
            # Already reserved, print message
            message = f"<@{ctx.author.id}> has already reserved {doujin.title}"
        else:
            # Add reservation
            dao.add_reservation(user, doujin)
            message = f"Added reserveration {doujin.title} for <@{ctx.author.id}>"

    except Exception as e:
        await ctx.send(f"Error: {e}")
        raise e

    await generate_doujin_embed(ctx, message, doujin, currency)


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
        doujin = dao.get_doujin_by_url(url)
        if not doujin:
            raise Exception("Cannot remove doujin that doesn't exist in the database.")
    except Exception as e:
        await ctx.send(f"Error: {e}")
        raise e

    try:
        discord_id = ctx.author.id
        user = dao.get_user_by_discord_id(discord_id)
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
            dao.remove_reservation(user, doujin)
            message = f"Removed reserveration {doujin.title} for <@{ctx.author.id}>"

    except Exception as e:
        await ctx.send(f"Error: {e}")
        raise e

    await generate_doujin_embed(ctx, message, doujin, currency)


@bot.command(brief="Lists all doujin reservation made by the user")
async def ls(ctx: commands.Context, user: discord.Member | None = None):
    """List all doujins reserved by a user.

    Parameters
    ----------
    ctx : commands.Context
        Discord Context

    user : discord.Member | None
        The discord user to show the doujin reservations for.
        If None (i.e. the command is ran without an argument), the target will be the user who sent the message.

    """
    if user is not None:
        discord_id = user.id
        message = f"List of doujins added by <@{user.id}>"
    else:
        discord_id = ctx.author.id
        message = "List of added Doujins"
    discord_id = user.id if user is not None else ctx.author.id
    reservations = []
    try:
        user_data = dao.get_user_by_discord_id(discord_id)
        # Creates user on first interaction
        if user_data:
            reservations = user_data.reservations

    except Exception as e:
        await ctx.send(f"Error: {e}")
        raise e

    await list_doujins(message, ctx, reservations)


# @bot.command(brief="Show doujin details given a list of Ids")
# async def show(ctx: commands.Context):
#     pass


@bot.command(brief="Export doujin reservations to a CSV")
async def export(ctx: commands.Context):
    all_user_data = dao.retrieve_all_users()
    all_doujin_data = dao.retrieve_all_doujin()

    await export_doujin_data(ctx, all_user_data, all_doujin_data)
