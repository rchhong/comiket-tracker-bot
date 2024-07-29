from datetime import datetime
from bson.objectid import ObjectId
from src.reservation import UserReservation
from src.doujin import Doujin


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
        _id : ObjectId
            MongoDB Object Id
        title : str
            Title of doujin
        price_in_yen : float
            Price of doujin (in Japanese Yen)
        image_preview_url : str
            URL of image to use as preview
        url : str
            URL of Doujin
        is_r18 : bool
            Doujin R18?
        circle_name : Optional[str]
            Doujin circle name
        author_names : list[str]
            Doujin author names
        genres : list[str]
            Doujin genre names
        events : list[str]
            Doujin event names
        last_updated : datetime
            datetime of when Doujin data was added.

        """

        self.doujin = doujin

        if not isinstance(reservations, list) or not all(
            [isinstance(x, UserReservation) for x in reservations]
        ):
            raise TypeError("reservations must be a list[User]")

        self.reservations = reservations

    @property
    def _id(self) -> ObjectId:
        return self.doujin._id

    @property
    def title(self) -> str:
        return self.doujin.title

    @property
    def price_in_yen(self) -> int:
        return self.doujin.price_in_yen

    @property
    def image_preview_url(self) -> str:
        return self.doujin.image_preview_url

    @property
    def url(self) -> str:
        return self.doujin.url

    @property
    def is_r18(self) -> bool:
        return self.doujin.is_r18

    @property
    def circle_name(self) -> str | None:
        return self.doujin.circle_name

    @property
    def author_names(self) -> list[str]:
        return self.doujin.author_names

    @property
    def genres(self) -> list[str]:
        return self.doujin.genres

    @property
    def events(self) -> list[str]:
        return self.doujin.events

    @property
    def last_updated(self) -> datetime:
        return self.doujin.last_updated
