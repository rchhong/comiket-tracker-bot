"""Contains the Discord Bot."""

import logging
import os

import discord
from discord.ext import commands

from src.currency import Currency
from src.scrape import DoujinScraper

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


bot = commands.Bot(command_prefix="!", intents=intents, log_handler=handler)


@bot.command(brief="Adds a doujin to the database")
async def add(ctx: commands.Context, url: str):
    """Command to add a duojin reservation for a user.

    Parameters
    ----------
    ctx : commands.Context
        Discord.py command context.
    url : str
        Melonbooks URL to create a reservation for.

    """
    doujin = doujin_scraper.scrape_url(url)

    price_in_usd = currency.convert_to(doujin.price_in_yen)
    price_in_usd_formatted = "{:.2f}".format(price_in_usd)

    # Add embed
    embed = discord.Embed(
        url=url,
        title=f"{doujin.title} - {doujin.circle_name} ({doujin.author_names})",
    )
    embed.set_thumbnail(url=doujin.image_preview_url)
    embed.add_field(name="Price (¥)", value=doujin.price_in_yen, inline=True)
    embed.add_field(name="Price ($)", value=price_in_usd_formatted, inline=True)
    embed.add_field(name="R18?", value="Yes" if doujin.is_r18 else "No", inline=True)
    embed.add_field(name="Genre", value=doujin.genres, inline=False)

    await ctx.send(f"Added {doujin.title}", embed=embed)
