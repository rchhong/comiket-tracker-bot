"""User Data Access Object (DAO)."""

from pymongo import MongoClient
from src.doujin import Doujin
from src.reservation import Reservation
from src.doujin_dao import DoujinDAO
from src.user import User
from datetime import datetime, UTC
import os


class UserDAO:
    """User Data Access Object (DAO).

    Attributes
    ----------
    db : MongoDB Client
    doujin_dao : DoujinDAO

    """

    def __init__(self, connection_str: str, doujin_dao: DoujinDAO) -> None:
        """Initialize the User DAO.

        Parameters
        ----------
        connection_str : str
            MongoDB Connection URL
        doujin_dao : DoujinDAO
            Doujin DAO

        """
        self.db = MongoClient(connection_str).get_database(os.getenv("MONGO_DB_NAME"))
        self.doujin_dao = doujin_dao

    def add_user(self, discord_id: int, name: str) -> User:
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
        # In the database, only need to store doujin id as reservation
        now = datetime.now(UTC)
        parameters = {
            "discord_id": discord_id,
            "name": name,
            "reservations": [],
            "last_updated": now,
        }

        id = self.db.users.insert_one(parameters).inserted_id

        return User(
            _id=id, discord_id=discord_id, name=name, reservations=[], last_updated=now
        )

    def get_user_by_discord_id(self, discord_id: int) -> User | None:
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
        parameters = {"discord_id": discord_id}
        user_metadata = self.db.users.find_one(parameters)

        if user_metadata is not None:
            reservations = []
            for reservation_metadata in user_metadata["reservations"]:
                doujin = self.doujin_dao.get_doujin_by_id(
                    reservation_metadata["doujin_id"]
                )
                if doujin is None:
                    raise Exception(
                        "Doujin was reserved without corresponding data being inserted in doujin collection."
                    )
                else:
                    reservation = Reservation(
                        doujin=doujin,
                        datetime_added=reservation_metadata["datetime_added"],
                    )

                    reservations.append(reservation)

            return User(
                _id=user_metadata["_id"],
                discord_id=user_metadata["discord_id"],
                name=user_metadata["name"],
                reservations=reservations,
                last_updated=user_metadata["last_updated"],
            )

        return None

    def add_reservation(self, user: User, doujin: Doujin) -> User:
        """Add a reservation to a user.

        Parameters
        ----------
        user : User
            User object
        doujin : Doujin
            Doujin object

        Returns
        -------
        User
            Updated user object

        """
        now = datetime.now(UTC)

        parameters = {"_id": user._id}
        update = {
            "$push": {
                "reservations": {
                    "doujin_id": doujin._id,
                    "datetime_added": now,
                }
            },
            "$set": {"last_updated": now},
        }

        result = self.db.users.update_one(parameters, update)
        if result.modified_count == 1:
            user.last_updated = now
            user.reservations.append(Reservation(doujin=doujin, datetime_added=now))
            return user
        else:
            raise Exception("Database failed to update user's reservations")

    def remove_reservation(self, user: User, doujin: Doujin) -> User:
        """Remove a reservation to a user.

        Parameters
        ----------
        user : User
            User object
        doujin : Doujin
            Doujin object

        Returns
        -------
        User
            Updated user object

        """
        now = datetime.now(UTC)

        parameters = {"_id": user._id}
        update = {
            "$pull": {
                "reservations": {
                    "doujin_id": doujin._id,
                }
            },
            "$set": {"last_updated": now},
        }

        result = self.db.users.update_one(parameters, update)
        if result.modified_count == 1:
            user.last_updated = now
            updated_reservations = []
            for reservation in user.reservations:
                if reservation.doujin._id != doujin._id:
                    updated_reservations.append(reservation)

            user.reservations = updated_reservations
            return user
        else:
            raise Exception("Database failed to update user's reservations")

    def retrieve_all_users(self) -> list[Doujin]:
        """Retrieve all users present in the database

        Returns
        -------
        list[Doujin]
            List of all users

        """
        ret = []
        for user_metadata in self.db.users.find(filter=None, projection=["discord_id"]):
            ret.append(self.get_user_by_discord_id(user_metadata["discord_id"]))

        return ret
