"""Store metadata about a doujin reservation."""

from datetime import datetime
from src.doujin import Doujin
from src.user import User


class DoujinReservation:
    """Doujin Reservation Data Class.
    Only users will use this.

    Attributes
    ----------
    doujin : A doujin object
    datetime_added : When the reservation for the doujin was placed

    """

    def __init__(self, doujin: Doujin, datetime_added: datetime):
        """Reservation Data Class.

        Parameters
        ----------
        doujin : Doujin
            A doujin object
        datetime_added : datetime
            When the reservation for the doujin was placed

        """

        if not isinstance(doujin, Doujin):
            raise TypeError("doujin must be a Doujin")

        if not isinstance(datetime_added, datetime):
            raise TypeError("datetime_added must be a datetime")

        self.doujin = doujin
        self.datetime_added = datetime_added


class UserReservation:
    """User Reservation Data Class.
    Only Doujins will use this.

    Attributes
    ----------
    doujin : A doujin object
    datetime_added : When the reservation for the doujin was placed

    """

    def __init__(self, user: User, datetime_added: datetime):
        """Reservation Data Class.

        Parameters
        ----------
        doujin : Doujin
            A doujin object
        datetime_added : datetime
            When the reservation for the doujin was placed

        """

        if not isinstance(user, User):
            raise TypeError(f"user must be a User, but user is {type(user)}")

        if not isinstance(datetime_added, datetime):
            raise TypeError(
                f"datetime_added must be a datetime, but datetime_added is {type(datetime_added)}"
            )

        self.user = user
        self.datetime_added = datetime_added
