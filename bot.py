import logging
import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

from scrape import scrape_url


load_dotenv()

# Logger
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')

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
    await ctx.send(f'Added {title}', embed=embed)

bot.run(os.getenv("TOKEN"))
