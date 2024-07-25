"""Contain a wrapper class for doujin information."""

from datetime import UTC, datetime
from bson.objectid import ObjectId


class Doujin:
    """Wrapper class for attributes of a doujin.

    Attributes
    ----------
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
        title: str,
        price_in_yen: int,
        image_preview_url: str,
        url: str,
        _id: ObjectId | None = None,
        is_r18: bool = False,
        circle_name: str | None = None,
        author_names: list[str] = [],
        genres: list[str] = [],
        events: list[str] = [],
        datetime_added: datetime = datetime.now(UTC),
    ):
        """Construct a doujin class.

        Parameters
        ----------
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
        datetime_added : datetime
            datetime of when Doujin data was added.

        """
        if not isinstance(title, str):
            raise TypeError("title must be a string")

        if not isinstance(price_in_yen, int):
            raise TypeError("price_in_yen must be an integer")

        if not isinstance(image_preview_url, str):
            raise TypeError("image_preview_url must be a string")

        if not isinstance(url, str):
            raise TypeError("url must be a string")

        if not isinstance(is_r18, bool):
            raise TypeError("is_r18 must be a boolean")

        if _id is not None and not isinstance(_id, ObjectId):
            raise TypeError("_id must be an ObjectId or None")

        if circle_name is not None and not isinstance(circle_name, str):
            raise TypeError("circle_name must be a string or None")

        if not isinstance(author_names, list) or not all(
            [isinstance(author_name, str) for author_name in author_names]
        ):
            raise TypeError("author_name must be a list of strings")

        if not isinstance(genres, list) or not all(
            [isinstance(genre, str) for genre in genres]
        ):
            raise TypeError("genre must be a list of strings")

        if not isinstance(events, list) or not all(
            isinstance(event, str) for event in events
        ):
            raise TypeError("event must be a list of strings")

        if not isinstance(datetime_added, datetime):
            raise TypeError("datetime_added must be a string")

        self.title = title
        self.price_in_yen = price_in_yen
        self.is_r18 = is_r18
        self.image_preview_url = image_preview_url
        self.url = url
        self.datetime_added = datetime_added
        self.circle_name = circle_name
        self.author_names = author_names
        self.genres = genres
        self.events = events
