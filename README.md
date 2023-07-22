# Comiket Discord Bot
This bot automatically facilitates the adding of doujin to a sheet, to which users can express interest in purchasing them.
Made for Comiket.

# Setup
1. `pip3 install -r requirements.txt`
2. Generate a Discord API Token
    1. Create a new application [here](https://discord.com/developers/applications).  Make sure to record the token.  If you forgot, navigate to Bot and reset the token
    2. Enable Message Content Intent (Bot -> Message Content Intent)
3. Go to https://currency.getgeoapi.com/ and create and account and get an API key
4. Create a `.env` file as follows
```
TOKEN="<discord token>"
CURRENCY_API_KEY="<Currency API Key>"
```
4. Invite the bot to your server by generating an OAuth2 link (OAuth2 -> URL Generator), selecting the `bot` scope and enabling the following permissions:
* Send Messages - this allows for the bot to show a preview of the doujin in the chat
* Embed Links  - this allows for the bot to show a preview of the doujin in the chat
5. Copy the generated link into your browser and invite the bot to your server.  Add doujins to track using `!add <melonbooks_url>`.