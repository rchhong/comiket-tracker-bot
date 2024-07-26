"""Store metadata about a doujin reservation."""

from datetime import datetime
from src.doujin import Doujin


class Reservation:
    """Reservation Data Class.

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
