from dotenv import load_dotenv
from src.bot import bot
import os

load_dotenv()

# Load environment variables

DISCORD_TOKEN = os.getenv("TOKEN")
assert DISCORD_TOKEN is not None

bot.run(DISCORD_TOKEN)
