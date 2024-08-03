"""Contains various utility functions, mostly dealing with the generation of discord messages."""

import csv
from datetime import UTC, datetime
from pathlib import Path

import discord
from discord import Embed
from discord.ext.commands import Context

from src.doujin_with_reservation import DoujinWithReservationData
from src.reservation import DoujinReservation
from src.user_with_reservation import UserWithReservationData


async def generate_doujin_embed(
    ctx: Context, message: str, doujin: DoujinWithReservationData
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

    Returns
    -------
    Embed
        Discord Embed

    """
    # Add embed
    embed = Embed(
        url=doujin.url,
        title=f"{doujin.title} - {doujin.circle_name} ({','.join(doujin.author_names)})",
    )
    embed.set_thumbnail(url=doujin.image_preview_url)
    embed.add_field(name="Price (¥)", value=doujin.price_in_yen, inline=True)
    embed.add_field(
        name="Price ($)", value="{:.2f}".format(doujin.price_in_usd), inline=True
    )

    embed.add_field(name="R18?", value="Yes" if doujin.is_r18 else "No", inline=True)
    embed.add_field(name="Genre", value=",".join(doujin.genres), inline=False)
    embed.add_field(name="Id", value=doujin._id, inline=False)

    await ctx.reply(message, embed=embed)


async def list_doujins(
    message: str,
    ctx: Context,
    reservations: list[DoujinReservation],
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

    """
    embeds = []
    list_string = ""
    page = 0
    cur_embed = Embed()

    price_yen_total = 0
    price_usd_total = 0
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
        line = f'{index + 1}. ¥{doujin.price_in_yen} (${'{:.2f}'.format(doujin.price_in_usd)}) - [{title[:10] + "..." if len(title) > 12 else title}]({url}) ({doujin._id})\n'

        price_yen_total += doujin.price_in_yen
        price_usd_total += doujin.price_in_usd
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

    await ctx.reply(
        content=f"Total cost: ¥{price_yen_total}, ${'{:.2f}'.format(price_usd_total)}"
    )


async def export_doujin_data(
    ctx: Context,
    all_user_data: list[UserWithReservationData],
    all_doujin_data: list[DoujinWithReservationData],
):
    """Export Comiket Bot's data.

    This will generate a message that contains the total amount spent by all users and the number of items reserved.
    A CSV that contains more detailed data will also be included.

    Parameters
    ----------
    ctx : Context
        Discord Context
    all_user_data : list[UserWithReservationData]
        The data of all users, including reservation data.
    all_doujin_data : list[DoujinWithReservationData]
        The data of all doujin, including reservation data.

    """
    # TODO: This should be it's own database query instead of fetching everything (but this might be a bit hard with MongoDB)
    relevant_user_data = []
    for user_data in all_user_data:
        total_cost_in_yen = sum(
            [reservation.doujin.price_in_yen for reservation in user_data.reservations]
        )
        total_cost_in_usd = sum(
            [reservation.doujin.price_in_usd for reservation in user_data.reservations]
        )
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
        message += f"<@{user_data['discord_id']}> purchased {user_data['num_items']} for a total of ¥{user_data['total_cost_in_yen']} (${'{:.2f}'.format(user_data['total_cost_in_usd'])})\n"

    csv_file_path = generate_csv(all_doujin_data)
    await ctx.send(message, file=discord.File(csv_file_path))


def generate_csv(all_doujin_data: list[DoujinWithReservationData]) -> Path:
    """Generate a CSV containing reservation data.

    Parameters
    ----------
    all_doujin_data : list[DoujinWithReservationData]
        All doujin data, with reservation data included.

    Returns
    -------
    Path
        Path to output file.

    """
    all_usernames = set()

    rows = []
    for doujin in all_doujin_data:
        row = {
            "doujin_id": doujin._id,
            "url": doujin.url,
            "title": doujin.title,
            "price_in_yen": doujin.price_in_yen,
            "price_in_usd": "{:.2f}".format(doujin.price_in_usd),
        }

        for reservation in doujin.reservations:
            username = reservation.user.name
            row[username] = "X"
            all_usernames.add(username)

        rows.append(row.copy())

    file_path = Path(f"doujin_export_{datetime.now(UTC)}.csv")
    column_names = [
        "doujin_id",
        "url",
        "title",
        "price_in_yen",
        "price_in_usd",
    ] + sorted(list(all_usernames))

    with open(file_path, "w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=column_names)

        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    return file_path
