from src.bot import bot
import os

# Load environment variables

DISCORD_TOKEN = os.getenv("TOKEN")
assert DISCORD_TOKEN is not None

bot.run(DISCORD_TOKEN)
