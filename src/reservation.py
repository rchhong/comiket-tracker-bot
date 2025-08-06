"""Store metadata about a doujin reservation."""

from datetime import UTC, datetime
import sqlite3
from src.doujin import Doujin
from src.user import User
from src.db import with_cursor, GLOBAL_SQLITE_CONN


class Reservation:
    """Reservation class to handle database interactions.

    Attributes
    ----------
    id : int
        Reservation ID
    user_discord_id : int
        Discord ID of the user
    doujin_id : int
        ID of the doujin
    datetime_added : datetime
        Timestamp when the reservation was added
    """

    id = -1

    def __init__(self, user_discord_id: int, doujin_id: int, datetime_added: datetime = datetime.now(UTC)):
        """Initialize a Reservation object.

        Parameters
        ----------
        user_discord_id : int
            Discord ID of the user
        doujin_id : int
            ID of the doujin
        datetime_added : datetime
            Timestamp when the reservation was added
        """
        if not isinstance(user_discord_id, int):
            raise TypeError("user_discord_id must be an int")
        if not isinstance(doujin_id, int):
            raise TypeError("doujin_id must be an int")
        if not isinstance(datetime_added, datetime):
            raise TypeError("datetime_added must be a datetime")

        self.user_discord_id = user_discord_id
        self.doujin_id = doujin_id
        self.datetime_added = datetime_added

    @with_cursor
    def save(self, cursor: sqlite3.Cursor):
        """Save the reservation to the SQLite database."""
        cursor.execute('''
        INSERT OR REPLACE INTO reservation (
            user_discord_id, doujin_id, datetime_added
        ) VALUES (?, ?, ?)
        ''', (
            self.user_discord_id, self.doujin_id, self.datetime_added.isoformat()
        ))
        self.id = cursor.lastrowid

    @with_cursor
    def delete(self, cursor: sqlite3.Cursor):
        """Delete the reservation from the SQLite database."""
        if self.id == -1:
            raise ValueError("Reservation ID is not set. Cannot delete.")
        cursor.execute('DELETE FROM reservation WHERE _id = ?', (self.id,))

    @staticmethod
    @with_cursor
    def find_by_user_id(user_discord_id: int, cursor: sqlite3.Cursor) -> list["Reservation"]:
        """Retrieve reservations by user Discord ID."""
        cursor.execute('SELECT * FROM reservation WHERE user_discord_id = ?', (user_discord_id,))
        rows = cursor.fetchall()
        reservations = []
        for row in rows:
            reservations.append(Reservation(
                user_discord_id=row[1],
                doujin_id=row[2],
                datetime_added=datetime.fromisoformat(row[3])
            ))
            reservations[-1].id = row[0]  # Set the ID from the database
        return reservations

    @staticmethod
    @with_cursor
    def find_by_doujin_id(doujin_id: int, cursor: sqlite3.Cursor) -> list["Reservation"]:
        """Retrieve reservations by doujin ID."""
        cursor.execute('SELECT * FROM reservation WHERE doujin_id = ?', (doujin_id,))
        rows = cursor.fetchall()
        reservations = []
        for row in rows:
            reservations.append(Reservation(
                user_discord_id=row[1],
                doujin_id=row[2],
                datetime_added=datetime.fromisoformat(row[3])
            ))
        return reservations


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

    @staticmethod
    def find_by_user(user: User) -> list["DoujinReservation"]:
        """Retrieve reservations by user Discord ID."""
        reservations = Reservation.find_by_user_id(user.discord_id) # type: ignore
        result = []
        for reservation in reservations:
            doujin = Doujin.find_by_id(reservation.doujin_id) # type: ignore
            if doujin is None:
                raise ValueError(f"Doujin with ID {reservation.doujin_id} not found. Database corrupted?")
            result.append(DoujinReservation(doujin, reservation.datetime_added))
        return result


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
        user : User
            A user object
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

    @staticmethod
    def find_by_doujin(doujin: Doujin) -> list["UserReservation"]:
        """Retrieve reservations by doujin ID."""
        reservations = Reservation.find_by_doujin_id(doujin.id) # type: ignore
        result = []
        for reservation in reservations:
            user = User.find_by_id(reservation.user_discord_id) # type: ignore
            if user is None:
                raise ValueError(f"User with ID {reservation.user_discord_id} not found. Database corrupted?")
            result.append(UserReservation(user, reservation.datetime_added))
        return result

