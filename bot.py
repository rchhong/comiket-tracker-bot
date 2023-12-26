import logging
import os
import asyncio
import textwrap

from typing import List, Any, Dict, Tuple
import discord
from discord.ext import commands
from dotenv import load_dotenv
from currency import Currency
from scrape import scrape_url
from sheets import generate_url_to_index, add_new_doujin, \
    generate_user_to_index, add_user_to_doujin, \
    add_user_to_spreadsheet, remove_user_from_doujin, \
    get_user_doujins, frontload_doujins_fromdb, \
    add_to_db, does_user_have_doujin, who_has_doujin
import math

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

@bot.command(brief="Adds a doujin to the database")
async def add(ctx: commands.Context, url):
    doujin = scrape_url(url)
    
    add_to_db(doujin, url, url_to_index, db_dict)
    
    title, price_in_yen, circle_name, author_name, \
        genre, _, is_r18, image_preview_url = doujin

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


async def list_doujins(ctx: commands.Context, doujins: List[Dict[str, Any]]) -> None:
    embeds = []
    list_string = ""
    
    page = 0
    list_string = ""
    cur_embed=discord.Embed()
    
    price_yen_total = 0
    for row in doujins:
        id = row['id']
        x = row['data']
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
        temp = f'{id} - ¥{db_dict[url][6]} - [{title[:10] + "..." if len(title) > 12 else title}]({url})\n'
        try:
            price_yen_total += int (db_dict[url][6])
        except ValueError:
            try: 
                price_yen_total += int (db_dict[url][6][1:])
            except ValueError:
                currency.logger.error("Yen is invalid")
        list_string += temp
    cur_embed.add_field(name=f'Page: {page + 1}', value = list_string)
    list_string = ""
    page += 1
    embeds.append(cur_embed)
    
    prev = 0
    total = 0
    has_sent = False
    for ind, embed in enumerate (embeds):
        embed = cur_embed
        # embed would be the discord.Embed instance
        fields = [embed.title, embed.description, embed.footer.text, embed.author.name]

        total += sum ([len (str (field.value)) for field in embed.fields])
        if total > 5000:
            await ctx.reply(content=f"List of added Doujins{' Continued' if has_sent else ''}: ", embeds = embeds[prev:ind])
            prev = ind
            total = sum ([len (str (field.value)) for field in embed.fields])
            has_sent = True
    if total != 0:
        await ctx.reply(content=f"List of added Doujins{' Continued' if has_sent else ''}: ", embeds = embeds[prev:])
    price_usd = "{:.2f}".format(currency.convert_to(price_yen_total))
    await ctx.reply(content=f'Total cost: ¥{price_yen_total}, ${price_usd}')

@bot.command(brief="Shows what the user does have")
async def list(ctx: commands.Context):  
    res = await get_user_doujins(url_to_index, username_to_index, str (ctx.author))
    await list_doujins(ctx, res)
 
@bot.command(brief="Shows what the user does NOT have")
async def list_inv(ctx: commands.Context):
    res = await get_user_doujins(url_to_index, username_to_index, str (ctx.author))
    ids = [x['id'] for x in res]
    print (ids)
    inv = [{'id':value - 2, 'data' : (key, "")} for key, value in url_to_index.items() if value - 2 not in ids]
    await list_doujins(ctx, inv)
  
@bot.command()
async def list_images(ctx: commands.Context, page = None, count = None):
    if page is None:
        page = 1
    
    try:
        page = int(page)
    except ValueError:
        page = 1
        
    if count is None:
        count = 1
    
    try:
        count = int(count)
    except ValueError:
        count = 1
        
        
    res = await get_user_doujins(url_to_index, username_to_index, str (ctx.author))
    
    if page * 4 > len(res):
        page = 1
    
    page -= 1
    
    embeds = []
    ind = 0
    for ind, row in enumerate (res[page*4:(page+count)*4]):
        id = row['id']
        x = row['data']
        cur_embed = discord.Embed()
        url = x[0]        
        cur_embed.set_image (url=db_dict[url][8]).url = "http://www.google.com"
        embeds.append(cur_embed)
        
        if ind % 4 == 3:
            await ctx.reply(content=f"List as Pictures for Page {page + 1 + int(ind/4)} of {math.ceil (len(res) / 4)}: ", embeds = embeds)
            embeds = []

        
    if len(embeds) > 0:
        await ctx.reply(content=f"List as Pictures for Page {page + 1 + int(ind/4)} of {math.ceil (len(res) / 4)}: ", embeds = embeds)
    
@bot.command(brief="Adds an array of indicies (use list)", description= "example usage: !qadd 0 1 2 3 4")
async def qadd (ctx: commands.Context, *args):
    flip = dict((v - 2,k) for k,v in url_to_index.items())
    username = str (ctx.author)
    cur_embed=discord.Embed()

    success = []
    failed = []
    already = []
    
    for id in args:
        try:
            id = int(id)
        except ValueError:
            failed.append(f"{id} - {db_dict[flip[id]][1]}")
            await ctx.reply(f"{id} is not an integer")
            continue
        
        if id >= len (url_to_index):
            failed.append(f"{id} - {db_dict[flip[id]][1]}")
            continue
        
        has_doujin = False
        try:
            has_doujin = does_user_have_doujin (username_to_index, url_to_index, username, flip[id])
        except:
            failed.append(f"{id} - {db_dict[flip[id]][1]}")
            await ctx.reply(f"{id} errored in accessing database")
        
        if (has_doujin):
            already.append(f"{id} - {db_dict[flip[id]][1]}")
            continue
            
        if username not in username_to_index:
            async with username_to_index_lock:
                await add_user_to_spreadsheet(username_to_index, username)

        add_user_to_doujin(username_to_index, url_to_index, username, flip[id])    
        success.append(f"{id} - {db_dict[flip[id]][1]}")
        
    cur_embed.add_field(name=f'Added', value = "\n".join(success))
    cur_embed.add_field(name=f'Already Added', value = "\n".join(already))
    cur_embed.add_field(name=f'Failed', value = "\n".join(failed))

    await ctx.reply(content="Result", embeds = [cur_embed])

@bot.command(brief="Removes an array of indicies (use list)", description= "example usage: !qrm 0 1 2 3 4")
async def qrm (ctx: commands.Context, *args):
    flip = dict((v - 2,k) for k,v in url_to_index.items())
    username = str (ctx.author)
    cur_embed=discord.Embed()

    success = []
    failed = []
    already = []
    
    for id in args:
        try:
            id = int(id)
        except ValueError:
            failed.append(f"{id} - {db_dict[flip[id]][1]}")
            await ctx.reply(f"{id} is not an integer")
            continue
        
        if id >= len (url_to_index):
            failed.append(f"{id} - {db_dict[flip[id]][1]}")
            continue
        
        has_doujin = True
        try:
            has_doujin = does_user_have_doujin (username_to_index, url_to_index, username, flip[id])
        except:
            failed.append(f"{id} - {db_dict[flip[id]][1]}")
            await ctx.reply(f"{id} errored in accessing database")
        
        if (not has_doujin):
            already.append(f"{id} - {db_dict[flip[id]][1]}")
            continue
            
        if username not in username_to_index:
            async with username_to_index_lock:
                await add_user_to_spreadsheet(username_to_index, username)

        remove_user_from_doujin(username_to_index, url_to_index, username, flip[id])    
        success.append(f"{id} - {db_dict[flip[id]][1]}")
        
    cur_embed.add_field(name=f'Removed', value = "\n".join(success))
    cur_embed.add_field(name=f'Did Not Have', value = "\n".join(already))
    cur_embed.add_field(name=f'Failed', value = "\n".join(failed))

    await ctx.reply(content="Result", embeds = [cur_embed])            

@bot.command(brief="Shows the doujin linked by id (use list)", description= "example usage: !show 1")
async def show (ctx: commands.Context, ind):
    ind = int (ind)
    flip = dict((v - 2,k) for k,v in url_to_index.items())
    url, title, circle_name, author_name, genre, is_r18, price_in_yen, event, image_preview_url = db_dict[flip[ind]]
    # Add embed
    embed=discord.Embed(
        url = url,
        title = f'{title} - {circle_name} ({author_name})',
    )
    embed.set_thumbnail(url=image_preview_url)
    embed.add_field(name="Price (¥)", value=price_in_yen, inline=True)
    embed.add_field(name="Price ($)", value=currency.convert_to(float (price_in_yen)), inline=True)
    embed.add_field(name="R18?", value="Yes" if is_r18 else "No", inline=True)
    embed.add_field(name="Genre", value=genre, inline=False)
    
    embed.add_field(name="users", value=", ".join(who_has_doujin(username_to_index, url_to_index,url)), inline=False)
    await ctx.send(f'Doujin -  {title}', embed=embed, view=ActionButtons(title, url))

DISCORD_TOKEN = os.getenv("TOKEN")
assert DISCORD_TOKEN is not None

bot.run(DISCORD_TOKEN)
