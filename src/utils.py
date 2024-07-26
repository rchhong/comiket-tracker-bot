"""Contains various utility functions, mostly dealing with the generation of discord messages."""

from datetime import datetime, UTC
from pathlib import Path
import csv

import discord
from src.reservation import Reservation
from src.currency import Currency
from src.doujin import Doujin
from src.user import User
from discord import Embed
from discord.ext.commands import Context


async def generate_doujin_embed(
    ctx: Context, message: str, doujin: Doujin, currency: Currency
):
    """Generate the embed that displays various doujin metadata.

    Parameters
    ----------
    ctx: Context
        Discord context
    message: str
        Message to include with the embed
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
    embed.add_field(name="Id", value=doujin._id, inline=False)

    await ctx.reply(message, embed=embed)


async def list_doujins(
    message: str, ctx: Context, reservations: list[Reservation], currency: Currency
) -> None:
    """Generate the embed that list the doujins a user has reserved.

    Parameters
    ----------
    message : str
        Message to accompany the embed
    ctx : Context
        Discord context
    reservations : list[Reservation]
        List of reservations
    currency : Currency
        Currency API wrapper

    """
    embeds = []
    list_string = ""
    page = 0
    cur_embed = Embed()

    price_yen_total = 0
    for index, reservation in enumerate(reservations):
        doujin = reservation.doujin
        if len(list_string) > 600:
            cur_embed.add_field(name=f"Page: {page + 1}", value=list_string)
            list_string = ""
            page += 1
            if page % 1 == 0:
                # cur_embed.description = f'Embed {int (page/4) + 1}'
                embeds.append(cur_embed)
                cur_embed = Embed()

        url = doujin.url
        title = doujin.title
        line = f'{index + 1}. ¥{doujin.price_in_yen} - [{title[:10] + "..." if len(title) > 12 else title}]({url}) ({doujin._id})\n'

        price_yen_total += doujin.price_in_yen
        list_string += line

    cur_embed.add_field(name=f"Page: {page + 1}", value=list_string)
    list_string = ""
    page += 1
    embeds.append(cur_embed)

    prev = 0
    total = 0
    has_sent = False
    for ind, embed in enumerate(embeds):
        embed = cur_embed
        total += sum([len(str(field.value)) for field in embed.fields])
        if total > 5000:
            await ctx.reply(
                content=f"{message}{' Continued' if has_sent else ''}: ",
                embeds=embeds[prev:ind],
            )
            prev = ind
            total = sum([len(str(field.value)) for field in embed.fields])
            has_sent = True
    if total != 0:
        await ctx.reply(
            content=f"{message}{' Continued' if has_sent else ''}: ",
            embeds=embeds[prev:],
        )
    price_usd = "{:.2f}".format(currency.convert_to(price_yen_total))
    await ctx.reply(content=f"Total cost: ¥{price_yen_total}, ${price_usd}")


async def export_doujin_data(
    ctx: Context, all_user_data: list[User], currency: Currency
):
    relevant_user_data = []
    for user_data in all_user_data:
        total_cost_in_yen = sum(
            [reservation.doujin.price_in_yen for reservation in user_data.reservations]
        )
        total_cost_in_usd = currency.convert_to(total_cost_in_yen)
        relevant_user_data.append(
            {
                "discord_id": user_data.discord_id,
                "num_items": len(user_data.reservations),
                "total_cost_in_yen": total_cost_in_yen,
                "total_cost_in_usd": total_cost_in_usd,
            }
        )
    relevant_user_data = sorted(
        relevant_user_data, key=lambda x: x["total_cost_in_yen"]
    )

    message = ""
    for user_data in relevant_user_data:
        print(user_data)
        message += f"<@{user_data['discord_id']}> purchased {user_data['num_items']} for a total of ¥{user_data['total_cost_in_yen']} (${user_data['total_cost_in_usd']})\n"

    csv_file_path = generate_csv(all_user_data, currency)
    await ctx.send(message, file=discord.File(csv_file_path))


def generate_csv(all_user_data: list[User], currency: Currency):
    # TODO: Create an array field for each doujin that contains the users that have reserved it.
    # To avoid recursion hell, the data classes for Doujin and User should be modified such that
    # the interior data classes don't contain references to the other.
    # For instance, the data class for Reservations within a User should remove the list_of_users field that would be present in the Doujin class
    # Here, this would save a large amount of complexity.

    all_usernames = [user.name for user in all_user_data]
    column_names = [
        "doujin_id",
        "title",
        "price_in_yen",
    ] + all_usernames

    # TODO: Add price_in_usd as a field as part of each doujin
    id_to_row = {}
    for user in all_user_data:
        username = user.name
        for reservation in user.reservations:
            (
                doujin_id,
                title,
                price_in_yen,
            ) = (
                reservation.doujin._id,
                reservation.doujin.title,
                reservation.doujin.price_in_yen,
            )

            if doujin_id not in id_to_row:
                id_to_row[doujin_id] = {
                    "doujin_id": doujin_id,
                    "title": title,
                    "price_in_yen": price_in_yen,
                    username: "X",
                }
            else:
                id_to_row[doujin_id][username] = "X"

    file_path = Path(f"doujin_export_{datetime.now(UTC)}.csv")
    with open(file_path, "w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=column_names)

        writer.writeheader()
        for row in id_to_row.values():
            writer.writerow(row)

    return file_path
