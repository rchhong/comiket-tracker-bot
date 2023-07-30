import logging
import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

from scrape import scrape_url

from sheets import generate_url_to_index, add_new_doujin

# Load API keys
load_dotenv()

# Logger
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
discord.utils.setup_logging(handler = handler, root=False)

# URL to index mapping
url_to_index = generate_url_to_index()

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents, log_handler=handler)

@bot.command()
async def add(ctx, url):
    title, price_in_yen, circle_name, author_name, \
        genre, _, is_r18, image_preview_url = scrape_url(url)

    # Add embed
    embed=discord.Embed(
        url = url,
        title = f'{title} - {circle_name} ({author_name})',
    )

    embed.set_thumbnail(url=image_preview_url)
    embed.add_field(name="Price (¥)", value=price_in_yen, inline=True)
    embed.add_field(name="R18?", value="Yes" if is_r18 else "No", inline=True)
    embed.add_field(name="Genre", value=genre, inline=False)
    if(url in url_to_index):
        await ctx.send(f'{title} has already been added!', embed=embed)
    else:
        add_new_doujin(url_to_index, url, title, circle_name, author_name, genre, is_r18, price_in_yen)
        await ctx.send(f'Added {title}', embed=embed)

bot.run(os.getenv("TOKEN"))
