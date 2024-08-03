"""Wrapper class for User and their reservation data."""

from datetime import datetime

from bson.objectid import ObjectId

from src.reservation import DoujinReservation
from src.user import User


class UserWithReservationData:
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

    def __init__(self, user: User, reservations: list[DoujinReservation] = []):
        """Initialize a user.

        Parameters
        ----------
        user : User
            User class containing all other user information
        reservations : list[Reservation]
            list of doujin reservations

        """
        self.user = user
        if not isinstance(reservations, list) or not all(
            [isinstance(x, DoujinReservation) for x in reservations]
        ):
            raise TypeError("reservations must be a list of reservation")

        self.reservations = reservations

    @property
    def _id(self) -> ObjectId:
        """Retrieve Id of the user.

        Returns
        -------
        ObjectId
            Id of the user

        """
        return self.user._id

    @property
    def discord_id(self) -> int:
        """Retrieve Discord Id of the user.

        Returns
        -------
        int
            Discord Id of user.

        """
        return self.user.discord_id

    @property
    def name(self) -> str:
        """Retrieve display name of the user.

        Returns
        -------
        str
            Display name of user.

        """
        return self.user.name

    @property
    def last_updated(self) -> datetime:
        """Retrieve the last updated timestamp of the user.

        Returns
        -------
        datetime
            Last updated timestamp of the user.

        """
        return self.user.last_updated

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
