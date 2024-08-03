"""Contains the Discord Bot."""

import logging
import os

import discord
from bson.objectid import ObjectId
from discord.ext import commands

from src.currency import Currency
from src.dao import DAO
from src.scrape import DoujinScraper
from src.utils import export_doujin_data, generate_doujin_embed, list_doujins

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


@bot.command(
    brief="Add reservations to doujin to the database.  Doujin can be referred to by ID or URL"
)
async def add(ctx: commands.Context, *args: str):
    """Command to add a (multiple) doujin(s) reservation for a user.

    Arguments can be Melonbooks or Doujin IDs

    Parameters
    ----------
    ctx : commands.Context
        Discord.py command context.
    args : tuple(str)
        Melonbook URL or IDS to create a reservation(s) for.

    """
    to_add = []
    for arg in args:
        # parse URL
        try:
            if "melonbooks" in arg:
                # Get doujin data if this is the first time
                doujin = dao.get_doujin_by_url(arg)
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
                    ) = doujin_scraper.scrape_url(arg)
                    doujin = dao.add_doujin(
                        arg,
                        title,
                        price_in_yen,
                        circle_name,
                        author_names,
                        genres,
                        events,
                        is_r18,
                        image_preview_url,
                    )

            else:
                doujin_id = ObjectId(arg)
                doujin = dao.get_doujin_by_id_with_reservation_data(doujin_id)
                if doujin is None:
                    raise Exception(f"Unable to find doujin with id {doujin_id}")

        except Exception as e:
            await ctx.send(f"Error: {e}")
            raise e

        to_add.append(doujin)

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

    except Exception as e:
        await ctx.send(f"Error: {e}")
        raise e

    for doujin in to_add:
        if user.has_reserved(doujin._id):
            # Already reserved, print message
            message = f"<@{ctx.author.id}> has already reserved {doujin.title}"
        else:
            # Add reservation
            dao.add_reservation(user, doujin)
            message = f"Added reserveration {doujin.title} for <@{ctx.author.id}>"

        await generate_doujin_embed(ctx, message, doujin)


@bot.command(
    brief="Remove reservations to doujin to the database.  Doujin must be referred to using their ID."
)
async def rm(ctx: commands.Context, *args: str):
    """Command to remove a doujin reservation for a user.

    Parameters
    ----------
    ctx : commands.Context
        Discord.py command context.
    args : tuple(str)
        IDs to remove a reservation(s) for.

    """
    # TODO: Force updates to doujin/user metadata after a interval of time
    to_add = []
    for arg in args:
        try:
            doujin = dao.get_doujin_by_id_with_reservation_data(ObjectId(arg))
            if doujin is None:
                raise Exception(f"Unable to find doujin with url: {arg}")
            to_add.append(doujin)
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

    except Exception as e:
        await ctx.send(f"Error: {e}")
        raise e

    try:
        for doujin in to_add:
            if not user.has_reserved(doujin._id):
                # Already reserved, print message
                message = f"<@{ctx.author.id}> has not reserved {doujin.title}, cannot remove."
            else:
                # Add reservation
                dao.remove_reservation(user, doujin)
                message = f"Removed reserveration {doujin.title} for <@{ctx.author.id}>"
            await ctx.reply(message)

    except Exception as e:
        await ctx.send(f"Error: {e}")
        raise e


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
        else:
            reservations = []

    except Exception as e:
        await ctx.send(f"Error: {e}")
        raise e

    await list_doujins(message, ctx, reservations)


@bot.command(brief="Show doujin details given an ID")
async def show(ctx: commands.Context, *args: str):
    """Show data related to a doujin given an Id.

    Parameters
    ----------
    ctx : commands.Context
        Discord context
    args : str
        List of IDs

    """
    to_show = []
    for arg in args:
        try:
            doujin = dao.get_doujin_by_id_with_reservation_data(ObjectId(arg))
            if doujin is None:
                raise Exception(f"Unable to find doujin with id {arg}")

            to_show.append(doujin)
        except Exception as e:
            await ctx.send(f"Error: {e}")
            raise e

    for doujin in to_show:
        if doujin is not None:
            await generate_doujin_embed(ctx, "", doujin)
        else:
            await ctx.send("Error: unable to find doujin with that ID")


@bot.command(brief="Export doujin reservations to a CSV")
async def export(ctx: commands.Context):
    """Export doujin data into a CSV.

    Parameters
    ----------
    ctx : commands.Context
        Discord Context

    """
    all_user_data = dao.retrieve_all_users()
    all_doujin_data = dao.retrieve_all_doujin()

    await export_doujin_data(ctx, all_user_data, all_doujin_data)
