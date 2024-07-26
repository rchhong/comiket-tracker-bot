from src.currency import Currency
from src.doujin import Doujin
from discord import Embed


def generate_doujin_embed(doujin: Doujin, currency: Currency) -> Embed:
    """Generates the embed that displays various doujin metadata.

    Parameters
    ----------
    doujin : Doujin
        Doujin embed
    currency : Currency
        Current API wrapper

    Returns
    -------
    Embed
        Discord Embed

    """
    price_in_usd = currency.convert_to(doujin.price_in_yen)
    price_in_usd_formatted = "{:.2f}".format(price_in_usd)

    # Add embed
    embed = Embed(
        url=doujin.url,
        title=f"{doujin.title} - {doujin.circle_name} ({','.join(doujin.author_names)})",
    )
    embed.set_thumbnail(url=doujin.image_preview_url)
    embed.add_field(name="Price (¥)", value=doujin.price_in_yen, inline=True)
    embed.add_field(name="Price ($)", value=price_in_usd_formatted, inline=True)
    embed.add_field(name="R18?", value="Yes" if doujin.is_r18 else "No", inline=True)
    embed.add_field(name="Genre", value=",".join(doujin.genres), inline=False)

    return embed
