"""Data Access Object (DAO)."""
# pyright: ignore[reportUnreachable]

import os
from datetime import UTC, datetime

from src.currency import Currency
from src.doujin import Doujin
from src.doujin_with_reservation import DoujinWithReservationData
from src.reservation import DoujinReservation, UserReservation, Reservation
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

        doujin = Doujin(

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
        
        doujin.save() # type: ignore

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
        doujin = Doujin.find_by_url(url) # type: ignore

        if doujin is not None:
            return DoujinWithReservationData(
                doujin=doujin,
                reservations=UserReservation.find_by_doujin(doujin),
            )

        return None

    def get_doujin_by_id(self, doujin_id: int) -> Doujin | None:
        """Retrieve a doujin by id.

        Parameters
        ----------
        doujin_id : int
            Id of the doujin.

        Returns
        -------
        Doujin | None
            Doujin data class.
            Returns None if a doujin with the Id provided was not found in the database.

        """
        if not isinstance(doujin_id, int):
            raise TypeError(
                f"Expected 'doujin_id' to be of type 'int', but got '{type(doujin_id).__name__}'"
            )
       
        return Doujin.find_by_id(doujin_id) # type: ignore
        

    def get_doujin_by_id_with_reservation_data(
        self, doujin_id: int
    ) -> DoujinWithReservationData | None:
        """Retrieve a doujin by id, but includes reservation data.

        This is separate method in order because the reservation data isn't always needed,
        and retrieving it is somewhat costly.


        Parameters
        ----------
        doujin_id : int
            Id of the doujin.

        Returns
        -------
        DoujinWithReservationData | None
            Doujin data class, with reservation data.
            Returns None if a doujin with the Id provided was not found in the database.

        """
        if not isinstance(doujin_id, int):
            raise TypeError(
                f"Expected 'doujin_id' to be of type 'ObjectId', but got '{type(doujin_id).__name__}'"
            )

        doujin = self.get_doujin_by_id(doujin_id)
        if doujin is not None:
            return DoujinWithReservationData(
                doujin=doujin,
                reservations=UserReservation.find_by_doujin(doujin),
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

        
        user = User(discord_id=discord_id, name=name, last_updated=now)
        
        user.save() # type: ignore

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

        user = User.find_by_id(discord_id) # type: ignore
        
        if user is not None:
            return UserWithReservationData(
                user=user,
                reservations= DoujinReservation.find_by_user(user),
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

        reservation = Reservation(
            user_discord_id=user_with_reservation_data.user.discord_id,
            doujin_id=doujin_with_reservation_data.doujin.id,
            datetime_added=now,)

        reservation.save() # type: ignore
       
        doujin_with_reservation_data.reservations.append(
            UserReservation(
                user=user_with_reservation_data.user, datetime_added=now
            )
        )
        
        user_with_reservation_data.reservations.append(
            DoujinReservation(
                doujin=doujin_with_reservation_data.doujin, datetime_added=now
            )
        )

        return user_with_reservation_data, doujin_with_reservation_data

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

        # Retrieve the reservation by intersecting user and doujin
        reservations = Reservation.find_by_user_id(user_with_reservation_data.user.discord_id) # type: ignore
        reservation_to_remove = next(
            (r for r in reservations if r.doujin_id == doujin_with_reservation_data.doujin.id), 
            None
        )

        if reservation_to_remove is None:
            raise ValueError("No reservation found for the specified user and doujin.")

        reservation_to_remove.delete()

        # Update user_with_reservation_data
        user_with_reservation_data.reservations = [
            r for r in user_with_reservation_data.reservations
            if r.doujin.id != doujin_with_reservation_data.doujin.id
        ]

        # Update doujin_with_reservation_data
        doujin_with_reservation_data.reservations = [
            r for r in doujin_with_reservation_data.reservations
            if r.user.discord_id != user_with_reservation_data.user.discord_id
        ]

        return user_with_reservation_data, doujin_with_reservation_data
    