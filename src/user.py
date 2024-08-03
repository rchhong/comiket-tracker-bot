"""Store a user's data."""

from datetime import UTC, datetime

from bson.objectid import ObjectId


class User:
    """Store a user's data.

    Attributes
    ----------
    _id: MongoDB Id
    discord_id : Discord Id
    name : Global name of the discord user.
    If the global name is not available, the server name will be used instead.
    last_updated : last update to user

    """

    def __init__(
        self,
        _id: ObjectId,
        discord_id: int,
        name: str,
        last_updated: datetime = datetime.now(UTC),
    ):
        """Initialize a user.

        Parameters
        ----------
        _id : ObjectId
            MongoDB Id
        discord_id : int
            Discord Id
        name : str
            Global name of the discord user.
            If the global name is not available, the server name will be used instead.
        reservations : list[Reservation]
            list of doujin reservations
        last_updated : datetime
            last update to user

        """
        if not isinstance(discord_id, int):
            raise TypeError("discord_id must be an int")
        if not isinstance(name, str):
            raise TypeError("global_name must be an str")
        if not isinstance(last_updated, datetime):
            raise TypeError("last_updated must be a datetime")

        self._id = _id
        self.discord_id = discord_id
        self.name = name
        self.last_updated = last_updated
