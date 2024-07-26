"""Doujin Data Access Object (DAO)."""

from datetime import datetime, UTC

from bson.objectid import ObjectId
from src.doujin import Doujin
from pymongo import MongoClient
import os


class DoujinDAO:
    """Doujin Data Access Object (DAO).

    Use this class to interact with MongoDB

    Attributes
    ----------
    db : MongoDB Client

    """

    def __init__(self, connection_str: str) -> None:
        """Initialize the Doujin DAO.

        Parameters
        ----------
        connection_str : str
            A MongoDB connection string URL

        """
        self.db = MongoClient(connection_str).get_database(os.getenv("MONGO_DB_NAME"))

    def add_doujin(
        self,
        url: str,
        title: str,
        price_in_yen: int,
        circle_name: str | None,
        author_names: list[str],
        genres: list[str],
        events: list[str],
        is_r18: bool,
        image_preview_url: str,
    ) -> Doujin:
        """Adds a doujin to the database

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

        Returns
        -------
        Doujin
            Doujin data class

        """
        if not isinstance(url, str):
            raise TypeError(
                f"Expected 'url' to be of type 'str', but got '{type(url).__name__}'"
            )
        if not isinstance(title, str):
            raise TypeError(
                f"Expected 'title' to be of type 'str', but got '{type(title).__name__}'"
            )
        if not isinstance(price_in_yen, int):
            raise TypeError(
                f"Expected 'price_in_yen' to be of type 'int', but got '{type(price_in_yen).__name__}'"
            )
        if not (isinstance(circle_name, str) or circle_name is None):
            raise TypeError(
                f"Expected 'circle_name' to be of type 'str' or 'None', but got '{type(circle_name).__name__}'"
            )
        if not isinstance(author_names, list) or not all(
            isinstance(name, str) for name in author_names
        ):
            raise TypeError("Expected 'author_names' to be a list of 'str'")
        if not isinstance(genres, list) or not all(
            isinstance(genre, str) for genre in genres
        ):
            raise TypeError("Expected 'genres' to be a list of 'str'")
        if not isinstance(events, list) or not all(
            isinstance(event, str) for event in events
        ):
            raise TypeError("Expected 'events' to be a list of 'str'")
        if not isinstance(is_r18, bool):
            raise TypeError(
                f"Expected 'is_r18' to be of type 'bool', but got '{type(is_r18).__name__}'"
            )
        if not isinstance(image_preview_url, str):
            raise TypeError(
                f"Expected 'image_preview_url' to be of type 'str', but got '{type(image_preview_url).__name__}'"
            )
        now = datetime.now(UTC)
        parameters = {
            "title": title,
            "price_in_yen": price_in_yen,
            "image_preview_url": image_preview_url,
            "url": url,
            "is_r18": is_r18,
            "circle_name": circle_name,
            "author_names": author_names,
            "genres": genres,
            "events": events,
            "last_updated": now,
        }

        id = self.db.doujins.insert_one(parameters).inserted_id
        return Doujin(
            _id=id,
            title=title,
            price_in_yen=price_in_yen,
            image_preview_url=image_preview_url,
            url=url,
            is_r18=is_r18,
            circle_name=circle_name,
            author_names=author_names,
            genres=genres,
            events=events,
            last_updated=now,
        )

    def get_doujin_by_url(self, url: str) -> Doujin | None:
        """Retrieve a doujin by URL.

        Parameters
        ----------
        url : str
            URL of the doujin.

        Returns
        -------
        Doujin | None
            Doujin data class.
            Returns None if a doujin with the URL provided was not found in the database.

        """
        if not isinstance(url, str):
            raise TypeError(
                f"Expected 'url' to be of type 'str', but got '{type(url).__name__}'"
            )
        parameters = {"url": url}
        doujin_metadata = self.db.doujins.find_one(parameters)

        return Doujin(**doujin_metadata) if doujin_metadata else None

    def get_doujin_by_id(self, doujin_id: ObjectId) -> Doujin | None:
        """Retrieve a doujin by id.

        Parameters
        ----------
        doujin_id : ObjectId
            Id of the doujin.

        Returns
        -------
        Doujin | None
            Doujin data class.
            Returns None if a doujin with the Id provided was not found in the database.

        """
        if not isinstance(doujin_id, ObjectId):
            raise TypeError(
                f"Expected 'doujin_id' to be of type 'ObjectId', but got '{type(doujin_id).__name__}'"
            )
        parameters = {"_id": doujin_id}

        doujin_metadata = self.db.doujins.find_one(parameters)
        return Doujin(**doujin_metadata) if doujin_metadata else None
