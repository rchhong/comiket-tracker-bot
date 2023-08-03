import logging
import os
import asyncio
import textwrap

import discord
from discord.ext import commands
from dotenv import load_dotenv
from currency import Currency
from scrape import scrape_url
from sheets import generate_url_to_index, add_new_doujin, \
    generate_user_to_index, add_user_to_doujin, \
    add_user_to_spreadsheet, remove_user_from_doujin, \
    get_user_doujins, frontload_doujins_fromdb


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

print("url_to_index", url_to_index)
print("username_to_index", username_to_index)

db_dict = frontload_doujins_fromdb(url_to_index)

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
        userid, username = interaction.user.id, interaction.user.name
        if username not in username_to_index:
            async with username_to_index_lock:
                await add_user_to_spreadsheet(username_to_index, username)

        add_user_to_doujin(username_to_index, url_to_index, username, self.url)
        await interaction.response.send_message(f"Added <@{userid}> to {self.title}", ephemeral=True)


    @discord.ui.button(label="Remove", style=discord.ButtonStyle.red)
    async def remove_button_action(self, interaction: discord.Interaction, button: discord.ui.Button):
        userid, username = interaction.user.id, interaction.user.name
        if username not in username_to_index:
            await interaction.response.send_message(f"Error: <@{userid}> is not added to the database.  Please add something before trying to remove.")

        remove_user_from_doujin(username_to_index, url_to_index, username, self.url)
        await interaction.response.send_message(f"Removed <@{userid}> from {self.title}", ephemeral=True)
        
        
bot = commands.Bot(command_prefix='!', intents=intents, log_handler=handler)

@bot.command()
async def add(ctx: commands.Context, url):
    title, price_in_yen, circle_name, author_name, \
        genre, _, is_r18, image_preview_url = scrape_url(url)

    price_in_usd = currency.convert_to(price_in_yen)
    price_in_usd_formatted = "{:.2f}".format(price_in_usd)

    # Add buttons
    view = ActionButtons(title, url)

    # Add embed
    embed=discord.Embed(
        url = url,
        title = f'{title} - {circle_name} ({author_name})',
    )
    embed.set_thumbnail(url=image_preview_url)
    embed.add_field(name="Price (¥)", value=price_in_yen, inline=True)
    embed.add_field(name="Price ($)", value=price_in_usd_formatted, inline=True)
    embed.add_field(name="R18?", value="Yes" if is_r18 else "No", inline=True)
    embed.add_field(name="Genre", value=genre, inline=False)
    if(url in url_to_index):
        await ctx.send(f'{title} has already been added!', embed=embed, view=view)
    else:
        async with url_to_index_lock:
            await add_new_doujin(url_to_index, url, title, circle_name, author_name, genre, is_r18, price_in_yen, price_in_usd_formatted)
        await ctx.send(f'Added {title}', embed=embed, view=view)

@bot.command()
async def list(ctx: commands.Context):  
    res = await get_user_doujins(url_to_index, username_to_index, str (ctx.author))
    
    embeds = []
    list_string = ""
    
    page = 0
    list_string = ""
    cur_embed=discord.Embed()
    
    price_yen_total = 0
    for x in res:
        if len(list_string) > 600:
            cur_embed.add_field(name=f'Page: {page + 1}', value = list_string)
            list_string = ""
            page += 1
            if page % 3 == 0:
                # cur_embed.description = f'Embed {int (page/4) + 1}'
                embeds.append(cur_embed)
                
                cur_embed = discord.Embed()
            
        url = x[0]
        title = db_dict[url][1]
        temp = f'¥{db_dict[url][6]} - [{title[:10] + "..." if len(title) > 12 else title}]({url})\n'
        try:
            price_yen_total += int (db_dict[url][6])
        except ValueError:
            try: 
                price_yen_total += int (db_dict[url][6][1:])
            except ValueError:
                currency.logger.error("Yen is invalid")
        list_string += temp
    embeds.append(cur_embed)
    
    prev = 0
    total = 0
    has_sent = False
    for ind, embed in enumerate (embeds):
        embed = cur_embed
        # embed would be the discord.Embed instance
        fields = [embed.title, embed.description, embed.footer.text, embed.author.name]

        total += sum ([len (str (field.value)) for field in embed.fields])
        print(total)   
        if total > 5000:
            await ctx.reply(content=f"List of added Doujins{' Continued' if has_sent else ''}: ", embeds = embeds[prev:ind])
            prev = ind
            total = sum ([len (str (field.value)) for field in embed.fields])
            has_sent = True
    if total != 0:
        await ctx.reply(content=f"List of added Doujins{' Continued' if has_sent else ''}: ", embeds = embeds[prev:])
    await ctx.reply(content=f'Total cost: ¥{price_yen_total}, ${currency.convert_to(price_yen_total)}')
    

DISCORD_TOKEN = os.getenv("TOKEN")
assert DISCORD_TOKEN is not None

bot.run(DISCORD_TOKEN)
