"""Entry point for the python file to create the bot."""

import os

from src.bot import bot

# Load environment variables

DISCORD_TOKEN = os.getenv("TOKEN")
assert DISCORD_TOKEN is not None

bot.run(DISCORD_TOKEN)
