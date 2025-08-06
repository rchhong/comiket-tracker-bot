"""Store a user's data."""

from datetime import UTC, datetime
import sqlite3
from src.db import with_cursor, GLOBAL_SQLITE_CONN

class User:
    """Store a user's data.

    Attributes
    ----------
    _id: MongoDB Id
    discord_id : Discord Id
    name : Global name of the discord user.
    If the global name is not available, the server name will be used instead.
    last_updated : last update to user

    """

    def __init__(
        self,
        discord_id: int,
        name: str,
        last_updated: datetime = datetime.now(UTC),
    ):
        """Initialize a user.

        Parameters
        ----------
        discord_id : int
            Discord Id
        name : str
            Global name of the discord user.
            If the global name is not available, the server name will be used instead.
        reservations : list[Reservation]
            list of doujin reservations
        last_updated : datetime
            last update to user

        """
        if not isinstance(discord_id, int):
            raise TypeError("discord_id must be an int")
        if not isinstance(name, str):
            raise TypeError("global_name must be an str")
        if not isinstance(last_updated, datetime):
            raise TypeError("last_updated must be a datetime")
        
        self.discord_id = discord_id
        self.name = name
        self.last_updated = last_updated

    @with_cursor
    def save(self, cursor: sqlite3.Cursor):
        """Save the user to the SQLite database."""
        cursor.execute('''
        INSERT OR REPLACE INTO user (
            discord_id, name, last_updated
        ) VALUES (?, ?, ?)
        ''', (
            self.discord_id, self.name, self.last_updated.isoformat()
        ))
        self.id = cursor.lastrowid

    @staticmethod
    @with_cursor
    def find_by_id(discord_id: int, cursor: sqlite3.Cursor):
        """Retrieve a User object from the SQLite database by Discord ID."""
        cursor.execute('SELECT * FROM user WHERE discord_id = ?', (discord_id,))
        row = cursor.fetchone()
        if row:
            return User(
                discord_id=row[0],
                name=row[1],
                last_updated=datetime.fromisoformat(row[2])
            )
        return None

    @staticmethod
    @with_cursor
    def all(cursor: sqlite3.Cursor) -> list["User"]:
        """Retrieve all users from the SQLite database."""
        cursor.execute('SELECT * FROM user')
        rows = cursor.fetchall()
        users = []
        for row in rows:
            users.append(User(
                discord_id=row[0],
                name=row[1],
                last_updated=datetime.fromisoformat(row[2])
            ))
        return users


