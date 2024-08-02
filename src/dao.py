"""Data Access Object (DAO)."""
# pyright: ignore[reportUnreachable]

import os
from datetime import UTC, datetime

from bson.objectid import ObjectId
from pymongo import MongoClient

from src.currency import Currency
from src.doujin import Doujin
from src.doujin_with_reservation import DoujinWithReservationData
from src.reservation import DoujinReservation, UserReservation
from src.user import User
from src.user_with_reservation import UserWithReservationData


class DAO:
    """Data Access Object (DAO).

    Use this class to interact with MongoDB

    Attributes
    ----------
    db : MongoDB Client
    currency : Currency API

    """

    def __init__(self, connection_str: str, currency: Currency) -> None:
        """Initialize the Doujin DAO.

        Parameters
        ----------
        connection_str : str
            A MongoDB connection string URL

        currency: Currency
            Currency API

        """
        if not isinstance(connection_str, str):
            raise TypeError("connection_str must be a str")

        if not isinstance(currency, Currency):
            raise TypeError("current must be a Currency")

        self.db = MongoClient(connection_str).get_database(os.getenv("MONGO_DB_NAME"))
        self.currency = currency

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
    ) -> DoujinWithReservationData:
        """Add a doujin to the database.

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
        if not (isinstance(circle_name, str) and circle_name is not None):
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
        price_in_usd = self.currency.convert_to(price_in_yen)

        parameters = {
            "title": title,
            "price_in_yen": price_in_yen,
            "price_in_usd": price_in_usd,
            "image_preview_url": image_preview_url,
            "url": url,
            "is_r18": is_r18,
            "circle_name": circle_name,
            "author_names": author_names,
            "genres": genres,
            "events": events,
            "last_updated": now,
            "reservations": [],
        }

        id = self.db.doujins.insert_one(parameters).inserted_id
        doujin = Doujin(
            _id=id,
            title=title,
            price_in_yen=price_in_yen,
            price_in_usd=price_in_usd,
            image_preview_url=image_preview_url,
            url=url,
            is_r18=is_r18,
            circle_name=circle_name,
            author_names=author_names,
            genres=genres,
            events=events,
            last_updated=now,
        )

        return DoujinWithReservationData(
            doujin=doujin,
            reservations=[],
        )

    def get_doujin_by_url(self, url: str) -> DoujinWithReservationData | None:
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

        if doujin_metadata is not None:
            doujin = Doujin(
                _id=doujin_metadata["_id"],
                title=doujin_metadata["title"],
                price_in_yen=doujin_metadata["price_in_yen"],
                price_in_usd=doujin_metadata["price_in_usd"],
                image_preview_url=doujin_metadata["image_preview_url"],
                url=doujin_metadata["url"],
                is_r18=doujin_metadata["is_r18"],
                circle_name=doujin_metadata["circle_name"],
                author_names=doujin_metadata["author_names"],
                genres=doujin_metadata["genres"],
                events=doujin_metadata["events"],
                last_updated=doujin_metadata["last_updated"],
            )

            reservations = []
            for reservation in doujin_metadata["reservations"]:
                user = self.get_user_by_id(reservation["user_id"])
                if user is None:
                    raise Exception(
                        "User reserved Doujin without corresponding data being inserted in doujin collection."
                    )

                else:
                    reservation = UserReservation(
                        user=user, datetime_added=reservation["datetime_added"]
                    )
                    reservations.append(reservation)

            return DoujinWithReservationData(
                doujin=doujin,
                reservations=reservations,
            )

        return None

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

        if doujin_metadata is not None:
            return Doujin(
                _id=doujin_metadata["_id"],
                title=doujin_metadata["title"],
                price_in_yen=doujin_metadata["price_in_yen"],
                price_in_usd=doujin_metadata["price_in_usd"],
                image_preview_url=doujin_metadata["image_preview_url"],
                url=doujin_metadata["url"],
                is_r18=doujin_metadata["is_r18"],
                circle_name=doujin_metadata["circle_name"],
                author_names=doujin_metadata["author_names"],
                genres=doujin_metadata["genres"],
                events=doujin_metadata["events"],
                last_updated=doujin_metadata["last_updated"],
            )

        return None

    def get_doujin_by_id_with_reservation_data(
        self, doujin_id: ObjectId
    ) -> DoujinWithReservationData | None:
        """Retrieve a doujin by id, but includes reservation data.

        This is separate method in order because the reservation data isn't always needed,
        and retrieving it is somewhat costly.


        Parameters
        ----------
        doujin_id : ObjectId
            Id of the doujin.

        Returns
        -------
        DoujinWithReservationData | None
            Doujin data class, with reservation data.
            Returns None if a doujin with the Id provided was not found in the database.

        """
        if not isinstance(doujin_id, ObjectId):
            raise TypeError(
                f"Expected 'doujin_id' to be of type 'ObjectId', but got '{type(doujin_id).__name__}'"
            )

        parameters = {"_id": doujin_id}
        doujin_metadata = self.db.doujins.find_one(parameters)

        if doujin_metadata is not None:
            doujin = Doujin(
                _id=doujin_metadata["_id"],
                title=doujin_metadata["title"],
                price_in_yen=doujin_metadata["price_in_yen"],
                price_in_usd=doujin_metadata["price_in_usd"],
                image_preview_url=doujin_metadata["image_preview_url"],
                url=doujin_metadata["url"],
                is_r18=doujin_metadata["is_r18"],
                circle_name=doujin_metadata["circle_name"],
                author_names=doujin_metadata["author_names"],
                genres=doujin_metadata["genres"],
                events=doujin_metadata["events"],
                last_updated=doujin_metadata["last_updated"],
            )

            reservations = []
            for reservation in doujin_metadata["reservations"]:
                user = self.get_user_by_id(reservation["user_id"])
                if user is None:
                    raise Exception(
                        "User reserved Doujin without corresponding data being inserted in doujin collection."
                    )

                else:
                    reservation = UserReservation(
                        user=user, datetime_added=reservation["datetime_added"]
                    )
                    reservations.append(reservation)

            return DoujinWithReservationData(
                doujin=doujin,
                reservations=reservations,
            )

        return None

    def add_user(self, discord_id: int, name: str) -> UserWithReservationData:
        """Add a user to the database.

        Parameters
        ----------
        discord_id : int
            Discord Id
        name : str
            Global name of the user.
            If the global name is not available, the server name will be used instead.

        Returns
        -------
        User
            User object representing the user just added to the database.

        """
        if not isinstance(discord_id, int):
            raise TypeError("discord_id must be an int")

        if not isinstance(name, str):
            raise TypeError("name must be an str")

        # In the database, only need to store doujin id as reservation
        now = datetime.now(UTC)
        parameters = {
            "discord_id": discord_id,
            "name": name,
            "reservations": [],
            "last_updated": now,
        }

        id = self.db.users.insert_one(parameters).inserted_id
        user = User(_id=id, discord_id=discord_id, name=name, last_updated=now)

        return UserWithReservationData(user=user, reservations=[])

    def get_user_by_discord_id(
        self,
        discord_id: int,
    ) -> UserWithReservationData | None:
        """Get a user from the database by Discord Id.

        Parameters
        ----------
        discord_id : int
            Discord Id

        Returns
        -------
        User | None
            The User with the Discord Id passed in.
            If there is no user found with the given Discord Id, None will be returned.

        """
        if not isinstance(discord_id, int):
            raise TypeError("discord_id must be an int")

        parameters = {"discord_id": discord_id}
        user_metadata = self.db.users.find_one(parameters)

        if user_metadata is not None:
            user = User(
                _id=user_metadata["_id"],
                discord_id=user_metadata["discord_id"],
                name=user_metadata["name"],
                last_updated=user_metadata["last_updated"],
            )

            reservations = []
            for reservation_metadata in user_metadata["reservations"]:
                doujin = self.get_doujin_by_id(reservation_metadata["doujin_id"])
                if doujin is None:
                    raise Exception(
                        "Doujin was reserved without corresponding data being inserted in doujin collection."
                    )
                else:
                    reservation = DoujinReservation(
                        doujin=doujin,
                        datetime_added=reservation_metadata["datetime_added"],
                    )

                    reservations.append(reservation)

            return UserWithReservationData(
                user=user,
                reservations=reservations,
            )

        return None

    def get_user_by_id(
        self,
        _id: ObjectId,
    ) -> User | None:
        """Get a user from the database by  Id.

        Parameters
        ----------
        _id : ObjectId
            Id

        Returns
        -------
        User | None
            The User with the Id passed in.
            If there is no user found with the given  Id, None will be returned.

        """
        if not isinstance(_id, ObjectId):
            raise TypeError("discord_id must be an ObjectId")

        parameters = {"_id": _id}
        user_metadata = self.db.users.find_one(parameters)

        if user_metadata is not None:
            return User(
                _id=user_metadata["_id"],
                discord_id=user_metadata["discord_id"],
                name=user_metadata["name"],
                last_updated=user_metadata["last_updated"],
            )

        return None

    def get_user_by_id_with_reservation_data(
        self,
        _id: ObjectId,
    ) -> UserWithReservationData | None:
        """Get a user from the database by  Id.

        Parameters
        ----------
        _id : ObjectId
            Id

        Returns
        -------
        User | None
            The User with the Id passed in.
            If there is no user found with the given  Id, None will be returned.

        """
        if not isinstance(_id, ObjectId):
            raise TypeError("discord_id must be an ObjectId")

        parameters = {"_id": _id}
        user_metadata = self.db.users.find_one(parameters)

        if user_metadata is not None:
            user = User(
                _id=user_metadata["_id"],
                discord_id=user_metadata["discord_id"],
                name=user_metadata["name"],
                last_updated=user_metadata["last_updated"],
            )

            reservations = []
            for reservation_metadata in user_metadata["reservations"]:
                doujin = self.get_doujin_by_id(reservation_metadata["doujin_id"])
                if doujin is None:
                    raise Exception(
                        "Doujin was reserved without corresponding data being inserted in doujin collection."
                    )
                else:
                    reservation = DoujinReservation(
                        doujin=doujin,
                        datetime_added=reservation_metadata["datetime_added"],
                    )

                    reservations.append(reservation)

            return UserWithReservationData(
                user=user,
                reservations=reservations,
            )

        return None

    def add_reservation(
        self,
        user_with_reservation_data: UserWithReservationData,
        doujin_with_reservation_data: DoujinWithReservationData,
    ) -> tuple[UserWithReservationData, DoujinWithReservationData]:
        """Add a reservation to a user.

        Parameters
        ----------
        user_with_reservation_data : UserWithReservationData
            User object, with user data
        doujin_with_reservation_data : DoujinWithReservationData
            Doujin object, with doujin data

        Returns
        -------
        tuple[UserWithReservationData, DoujinWithReservationData]
            Updated user object (with reservations) and doujin object (with reservations).

        """
        if not isinstance(user_with_reservation_data, UserWithReservationData):
            raise TypeError(
                "user_with_reservation_data must be a UserWithReservationData"
            )

        if not isinstance(doujin_with_reservation_data, DoujinWithReservationData):
            raise TypeError(
                "doujin_with_reservation_data must be a DoujinWithReservationData"
            )

        now = datetime.now(UTC)

        updated_doujin = self._add_user_reservation(
            user_with_reservation_data, doujin_with_reservation_data, now
        )
        updated_user = self._add_doujin_reservation(
            user_with_reservation_data, doujin_with_reservation_data, now
        )

        return updated_user, updated_doujin

    def _add_doujin_reservation(
        self,
        user_with_reservation_data: UserWithReservationData,
        doujin_with_reservation_data: DoujinWithReservationData,
        now: datetime,
    ) -> UserWithReservationData:
        if not isinstance(user_with_reservation_data, UserWithReservationData):
            raise TypeError(
                "user_with_reservation_data must be a UserWithReservationData"
            )

        if not isinstance(doujin_with_reservation_data, DoujinWithReservationData):
            raise TypeError(
                "doujin_with_reservation_data must be a DoujinWithReservationData"
            )

        if not isinstance(now, datetime):
            raise TypeError("now must be a datetime")

        parameters = {"_id": user_with_reservation_data._id}
        update = {
            "$push": {
                "reservations": {
                    "doujin_id": doujin_with_reservation_data._id,
                    "datetime_added": now,
                }
            },
            "$set": {"last_updated": now},
        }

        result = self.db.users.update_one(parameters, update)
        if result.modified_count == 1:
            user_with_reservation_data.user.last_updated = now
            user_with_reservation_data.reservations.append(
                DoujinReservation(
                    doujin=doujin_with_reservation_data.doujin, datetime_added=now
                )
            )
            return user_with_reservation_data
        else:
            raise Exception("Database failed to update user's reservations")

    def _add_user_reservation(
        self,
        user_with_reservation_data: UserWithReservationData,
        doujin_with_reservation_data: DoujinWithReservationData,
        now: datetime,
    ) -> DoujinWithReservationData:
        if not isinstance(user_with_reservation_data, UserWithReservationData):
            raise TypeError(
                "user_with_reservation_data must be a UserWithReservationData"
            )

        if not isinstance(doujin_with_reservation_data, DoujinWithReservationData):
            raise TypeError(
                "doujin_with_reservation_data must be a DoujinWithReservationData"
            )

        if not isinstance(now, datetime):
            raise TypeError("now must be a datetime")

        parameters = {"_id": doujin_with_reservation_data._id}
        update = {
            "$push": {
                "reservations": {
                    "user_id": user_with_reservation_data._id,
                    "datetime_added": now,
                }
            },
            "$set": {"last_updated": now},
        }

        result = self.db.doujins.update_one(parameters, update)
        if result.modified_count == 1:
            doujin_with_reservation_data.doujin.last_updated = now
            doujin_with_reservation_data.reservations.append(
                UserReservation(
                    user=user_with_reservation_data.user, datetime_added=now
                )
            )
            return doujin_with_reservation_data
        else:
            raise Exception("Database failed to update user's reservations")

    def remove_reservation(
        self,
        user_with_reservation_data: UserWithReservationData,
        doujin_with_reservation_data: DoujinWithReservationData,
    ) -> tuple[UserWithReservationData, DoujinWithReservationData]:
        """Remove a reservation to a user.

        Parameters
        ----------
        user_with_reservation_data : UserWithReservationData
            User object, with user data
        doujin_with_reservation_data : DoujinWithReservationData
            Doujin object, with doujin data

        Returns
        -------
        tuple[UserWithReservationData, DoujinWithReservationData]
            Updated user object (with reservations) and doujin object (with reservations).

        """
        if not isinstance(user_with_reservation_data, UserWithReservationData):
            raise TypeError(
                "user_with_reservation_data must be a UserWithReservationData"
            )

        if not isinstance(doujin_with_reservation_data, DoujinWithReservationData):
            raise TypeError(
                "doujin_with_reservation_data must be a DoujinWithReservationData"
            )

        now = datetime.now(UTC)

        updated_user = self._remove_doujin_reservation(
            user_with_reservation_data, doujin_with_reservation_data, now
        )
        updated_doujin = self._remove_user_reservation(
            user_with_reservation_data, doujin_with_reservation_data, now
        )

        return updated_user, updated_doujin

    def _remove_doujin_reservation(
        self,
        user_with_reservation_data: UserWithReservationData,
        doujin_with_reservation_data: DoujinWithReservationData,
        now: datetime,
    ) -> UserWithReservationData:
        if not isinstance(user_with_reservation_data, UserWithReservationData):
            raise TypeError(
                "user_with_reservation_data must be a UserWithReservationData"
            )

        if not isinstance(doujin_with_reservation_data, DoujinWithReservationData):
            raise TypeError(
                "doujin_with_reservation_data must be a DoujinWithReservationData"
            )

        if not isinstance(now, datetime):
            raise TypeError("now must be a datetime")

        parameters = {"_id": user_with_reservation_data._id}
        update = {
            "$pull": {
                "reservations": {
                    "doujin_id": doujin_with_reservation_data._id,
                }
            },
            "$set": {"last_updated": now},
        }

        result = self.db.users.update_one(parameters, update)
        if result.modified_count == 1:
            user_with_reservation_data.user.last_updated = now
            updated_reservations = []
            for reservation in user_with_reservation_data.reservations:
                if reservation.doujin._id != doujin_with_reservation_data._id:
                    updated_reservations.append(reservation)

            user_with_reservation_data.reservations = updated_reservations
            return user_with_reservation_data
        else:
            raise Exception("Database failed to update user's reservations")

    def _remove_user_reservation(
        self,
        user_with_reservation_data: UserWithReservationData,
        doujin_with_reservation_data: DoujinWithReservationData,
        now: datetime,
    ) -> DoujinWithReservationData:
        if not isinstance(user_with_reservation_data, UserWithReservationData):
            raise TypeError(
                "user_with_reservation_data must be a UserWithReservationData"
            )

        if not isinstance(doujin_with_reservation_data, DoujinWithReservationData):
            raise TypeError(
                "doujin_with_reservation_data must be a DoujinWithReservationData"
            )

        if not isinstance(now, datetime):
            raise TypeError("now must be a datetime")

        parameters = {"_id": doujin_with_reservation_data._id}
        update = {
            "$pull": {
                "reservations": {
                    "user_id": user_with_reservation_data._id,
                }
            },
            "$set": {"last_updated": now},
        }

        result = self.db.doujins.update_one(parameters, update)
        if result.modified_count == 1:
            doujin_with_reservation_data.doujin.last_updated = now
            updated_reservations = []
            for reservation in doujin_with_reservation_data.reservations:
                if reservation.user._id != user_with_reservation_data._id:
                    updated_reservations.append(reservation)

            doujin_with_reservation_data.reservations = updated_reservations
            return doujin_with_reservation_data
        else:
            raise Exception("Database failed to update user's reservations")

    def retrieve_all_users(self) -> list[UserWithReservationData]:
        """Retrieve all users present in the database.

        Returns
        -------
        list[Doujin]
            List of all users

        """
        ret = []
        for user_metadata in self.db.users.find(filter=None):
            user = User(
                _id=user_metadata["_id"],
                discord_id=user_metadata["discord_id"],
                name=user_metadata["name"],
                last_updated=user_metadata["last_updated"],
            )

            reservations = []
            for reservation_metadata in user_metadata["reservations"]:
                doujin = self.get_doujin_by_id(reservation_metadata["doujin_id"])
                if doujin is None:
                    raise Exception(
                        "Doujin was reserved without corresponding data being inserted in doujin collection."
                    )
                else:
                    reservation = DoujinReservation(
                        doujin=doujin,
                        datetime_added=reservation_metadata["datetime_added"],
                    )

                    reservations.append(reservation)

            ret.append(
                UserWithReservationData(
                    user=user,
                    reservations=reservations,
                )
            )

        return ret

    def retrieve_all_doujin(self) -> list[DoujinWithReservationData]:
        """Retrieve all doujin in the database.

        Returns
        -------
        list[DoujinWithReservationData]
            List of all doujin, with reservation data

        """
        ret = []
        for doujin_metadata in self.db.doujins.find(filter=None):
            doujin = Doujin(
                _id=doujin_metadata["_id"],
                title=doujin_metadata["title"],
                price_in_yen=doujin_metadata["price_in_yen"],
                price_in_usd=doujin_metadata["price_in_usd"],
                image_preview_url=doujin_metadata["image_preview_url"],
                url=doujin_metadata["url"],
                is_r18=doujin_metadata["is_r18"],
                circle_name=doujin_metadata["circle_name"],
                author_names=doujin_metadata["author_names"],
                genres=doujin_metadata["genres"],
                events=doujin_metadata["events"],
                last_updated=doujin_metadata["last_updated"],
            )

            reservations = []
            for reservation in doujin_metadata["reservations"]:
                user = self.get_user_by_id(reservation["user_id"])
                if user is None:
                    raise Exception(
                        "User reserved Doujin without corresponding data being inserted in doujin collection."
                    )

                else:
                    reservation = UserReservation(
                        user=user, datetime_added=reservation["datetime_added"]
                    )
                    reservations.append(reservation)

            ret.append(
                DoujinWithReservationData(
                    doujin=doujin,
                    reservations=reservations,
                )
            )
        return ret
