"""Contain a wrapper class for doujin information."""

from typing import Optional


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

    """

    def __init__(
        self,
        title: str,
        price_in_yen: int,
        image_preview_url: str,
        is_r18: bool = False,
        circle_name: Optional[str] = None,
        author_names: list[str] = [],
        genres: list[str] = [],
        events: list[str] = [],
    ):
        """Construct a doujin class.

        Parameters
        ----------
        title : str
            Title of doujin
        price_in_yen : float
            Price of doujin (in Japanese Yen)
        is_r18 : bool
            Doujin R18?
        image_preview_url : str
            URL of image to use as preview
        circle_name : Optional[str]
            Doujin circle name
        author_names : list[str]
            Doujin author names
        genres : list[str]
            Doujin genre names
        events : list[str]
            Doujin event names

        """
        if not isinstance(title, str):
            raise TypeError("title must be a string")

        if not isinstance(price_in_yen, int):
            raise TypeError("price_in_yen must be an integer")

        if not isinstance(is_r18, bool):
            raise TypeError("is_r18 must be a boolean")

        if not isinstance(image_preview_url, str):
            raise TypeError("image_preview_url must be a string")

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

        self.title: str = title
        self.price_in_yen: int = price_in_yen
        self.is_r18: bool = is_r18
        self.image_preview_url: str = image_preview_url
        self.circle_name: str | None = circle_name
        self.author_names: list[str] = author_names
        self.genres: list[str] = genres
        self.events: list[str] = events
