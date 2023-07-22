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
    title, price_in_yen, circle_name, author_name, genre, event, is_r18 = scrape_url(url)
    await ctx.send(f'{title} {price_in_yen} {circle_name} {author_name} {genre} {event} {is_r18}')

bot.run(os.getenv("TOKEN"))
