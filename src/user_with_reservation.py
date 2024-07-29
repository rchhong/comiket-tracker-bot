from datetime import datetime
from src.reservation import DoujinReservation
from src.user import User
from bson.objectid import ObjectId


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
        return self.user._id

    @property
    def discord_id(self) -> int:
        return self.user.discord_id

    @property
    def name(self) -> str:
        return self.user.name

    @property
    def last_updated(self) -> datetime:
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
