import logging
import os
import asyncio


import discord
from discord.ext import commands
from dotenv import load_dotenv

from currency import Currency
from scrape import scrape_url
from sheets import generate_url_to_index, add_new_doujin, generate_user_to_index, add_user_to_doujin

# Load API keys
load_dotenv()

# Logger
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
discord.utils.setup_logging(handler=handler, root=False)

# URL to index mapping
url_to_index = generate_url_to_index()
# Lock for updating the index mapping for urls
url_to_index_lock = asyncio.Lock()

# user to index mapping
username_to_index = generate_user_to_index()
# Lock for updating the index mapping for users
username_to_index_lock = asyncio.Lock()


# Requires message_content intent to work
intents = discord.Intents.default()
intents.message_content = True

# Currency setup
CURRENCY_API_KEY = os.getenv("CURRENCY_API_KEY")
assert CURRENCY_API_KEY is not None
currency = Currency(CURRENCY_API_KEY)

# Buttons setup
class ActionButtons(discord.ui.View):
    def __init__(self, title: str, url: str):
        super().__init__()
        self.title = title
        self.url = url

    @discord.ui.button(label="Add", style=discord.ButtonStyle.green)
    async def add_button_action(self, interaction: discord.Interaction, button: discord.ui.Button):
        id, username = interaction.user.id, interaction.user.name
        async with username_to_index_lock:
            await add_user_to_doujin(username_to_index, url_to_index, username, self.url)
        await interaction.response.send_message(f"Added <@{id}> to {self.title}")


    @discord.ui.button(label="Remove", style=discord.ButtonStyle.red)
    async def remove_button_action(self, interaction: discord.Interaction, button: discord.ui.Button):
        user = interaction.user
        await interaction.response.send_message(f"Removed <@{user.id}> from {self.title}")

bot = commands.Bot(command_prefix='!', intents=intents, log_handler=handler)

@bot.command()
async def add(ctx: discord.ext.commands.Context, url):
    title, price_in_yen, circle_name, author_name, \
        genre, _, is_r18, image_preview_url = scrape_url(url)

    # Add buttons
    view = ActionButtons(title, url)

    # Add embed
    embed=discord.Embed(
        url = url,
        title = f'{title} - {circle_name} ({author_name})',
    )
    embed.set_thumbnail(url=image_preview_url)
    embed.add_field(name="Price (¥)", value=price_in_yen, inline=True)
    embed.add_field(name="Price ($)", value="{:.2f}".format(currency.convert_to(price_in_yen)), inline=True)
    embed.add_field(name="R18?", value="Yes" if is_r18 else "No", inline=True)
    embed.add_field(name="Genre", value=genre, inline=False)
    if(url in url_to_index):
        await ctx.send(f'{title} has already been added!', embed=embed, view=view)
    else:
        async with url_to_index_lock:
            await add_new_doujin(url_to_index, url, title, circle_name, author_name, genre, is_r18, price_in_yen)
        await ctx.send(f'Added {title}', embed=embed, view=view)

DISCORD_TOKEN = os.getenv("TOKEN")
assert DISCORD_TOKEN is not None

bot.run(DISCORD_TOKEN)
