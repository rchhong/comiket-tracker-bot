"""Store a user's data."""

from datetime import datetime, UTC
from src.reservation import Reservation
from bson.objectid import ObjectId


class User:
    """Store a user's data.

    Attributes
    ----------
    _id: MongoDB Id
    discord_id : Discord Id
    name : Global name of the discord user.
    If the global name is not available, the server name will be used instead.
    reservations : list of doujin reservations
    last_updated : last update to user

    """

    def __init__(
        self,
        _id: ObjectId,
        discord_id: int,
        name: str,
        reservations: list[Reservation],
        last_updated: datetime = datetime.now(UTC),
    ):
        """Initialize a user.

        Parameters
        ----------
        _id : ObjectId
            MongoDB Id
        discord_id : int
            [TODO:description]
        name : str
            [TODO:description]
        reservations : list[Reservation]
            [TODO:description]
        last_updated : datetime
            [TODO:description]

        """
        if not isinstance(discord_id, int):
            raise TypeError("discord_id must be an int")
        if not isinstance(name, str):
            raise TypeError("global_name must be an str")
        if not isinstance(reservations, list) or not all(
            [isinstance(x, Reservation) for x in reservations]
        ):
            raise TypeError("reservations must be a list of reservation")
        if not isinstance(last_updated, datetime):
            raise TypeError("last_updated must be a datetime")

        self._id = _id
        self.discord_id = discord_id
        self.name = name
        self.reservations = reservations
        self.last_updated = last_updated

    def has_reserved(self, doujin_id: ObjectId) -> bool:
        """Check whether or not a doujin has already been reserved by the user.

        Parameters
        ----------
        doujin_id : ObjectId
            MongoDB Id of Doujin

        Returns
        -------
        bool
            Whether or not the doujin has already been reserved by the user.

        """
        doujin_ids = [x.doujin._id for x in self.reservations]

        return doujin_id in doujin_ids
