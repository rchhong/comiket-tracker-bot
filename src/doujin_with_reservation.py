"""Wrapper class for Doujin with Reservations."""

from datetime import datetime

from bson.objectid import ObjectId

from src.doujin import Doujin
from src.reservation import UserReservation


class DoujinWithReservationData:
    """Wrapper class for attributes of a doujin.

    Attributes
    ----------
    _id : MongoDB Object ID
    title : Title of doujin
    price_in_yen : Price of doujin (in Japanese Yen)
    is_r18 : Doujin R18?
    image_preview_url : URL of image to use as preview
    circle_name : Doujin circle name
    author_name : Doujin author name
    genre : Doujin genre name
    event : Doujin event name
    url : URL of Doujin
    datetime_added : datetime of when Doujin data was added.

    """

    def __init__(
        self,
        doujin: Doujin,
        reservations: list[UserReservation] = [],
    ):
        """Construct a doujin class.

        Parameters
        ----------
        doujin : Doujin
            Contains all doujin information besides reservation data
        reservations : list[UserReservation]
            List of user reservations.

        """
        self.doujin = doujin

        if not isinstance(reservations, list) or not all(
            [isinstance(x, UserReservation) for x in reservations]
        ):
            raise TypeError("reservations must be a list[User]")

        self.reservations = reservations

    @property
    def _id(self) -> ObjectId:
        """Retrieve Id of the doujin.

        Returns
        -------
        ObjectId
            Id of object

        """
        return self.doujin._id

    @property
    def title(self) -> str:
        """Retrieve doujin title of the doujin.

        Returns
        -------
        str
            Title of the doujin

        """
        return self.doujin.title

    @property
    def price_in_yen(self) -> int:
        """Retrieve price in Japanese Yen of the doujin.

        Returns
        -------
        int
            Price in Japanese Yen of the doujin

        """
        return self.doujin.price_in_yen

    @property
    def price_in_usd(self) -> float:
        """Retrieve price in USD of the doujin.

        Returns
        -------
        float
            Price in USD of the doujin

        """
        return self.doujin.price_in_usd

    @property
    def image_preview_url(self) -> str:
        """Retrieve image preview URL of the doujin.

        Returns
        -------
        str
            Image preview URL of the doujin

        """
        return self.doujin.image_preview_url

    @property
    def url(self) -> str:
        """Retrieve Melonbooks URL of the doujin.

        Returns
        -------
        str
            Melonbooks URL of the doujin

        """
        return self.doujin.url

    @property
    def is_r18(self) -> bool:
        """Return whether or not the doujin is R18+ or not.

        Returns
        -------
        bool
            Is the doujin R18+?

        """
        return self.doujin.is_r18

    @property
    def circle_name(self) -> str | None:
        """Retrieve the circle name of the doujin.

        Returns
        -------
        str | None
            Circle name of doujin.

        """
        return self.doujin.circle_name

    @property
    def author_names(self) -> list[str]:
        """Retrieve the list of authors of the doujin.

        Returns
        -------
        list[str]
            List of authors of the doujin.

        """
        return self.doujin.author_names

    @property
    def genres(self) -> list[str]:
        """Retrieve the list of genres of the doujin.

        Returns
        -------
        list[str]
            List of genres of the doujin.

        """
        return self.doujin.genres

    @property
    def events(self) -> list[str]:
        """Retrieve the list of events associated with the doujin.

        Returns
        -------
        list[str]
            List of events associated with the doujin.

        """
        return self.doujin.events

    @property
    def last_updated(self) -> datetime:
        """Retrieve the last updated timestamp of the doujin object.

        Returns
        -------
        datetime
            Last updated timestamp of the doujin object.

        """
        return self.doujin.last_updated
