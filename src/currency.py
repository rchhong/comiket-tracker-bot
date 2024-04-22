"""Wrapper for the currency exchange API."""

import logging
from datetime import datetime
from pathlib import Path

import requests


class Currency:
    """Wrapper to hold Currency API logic.

    Attributes
    ----------
    current_rate : Current exchange rate
    last_update : datetime of last update to exchange rate
    api_key : Currency Exchange API
    currency_from : Currency to exchange from
    currency_to : Currency to exchange to
    logger : Logger

    """

    def __init__(
        self,
        api_key: str,
        currency_from: str = "JPY",
        currency_to: str = "USD",
        log_file: str | Path = "currency.log",
    ):
        """Initialize the wrapper for the currency exchange API.

        Parameters
        ----------
        log_file : str | Path
            File to store output of currency conversion API.
        api_key : str
            Currency conversion API Key.
        currency_from : str
            Currency to convert from.
        currency_to : str
            Currency to convert to.

        """
        self.current_rate: float = 0
        self.last_update: datetime = datetime.min
        self.api_key: str = api_key
        self.currency_from: str = currency_from
        self.currency_to: str = currency_to

        self.logger = logging.getLogger(__name__)

        lfHandler = logging.FileHandler(filename=log_file, encoding="utf-8", mode="w")
        lfHandler.setLevel(logging.ERROR)
        lfHandler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )

        self.logger.addHandler(lfHandler)

    def update_cache(self) -> None:
        """Retrieve the live currency exchange rate from currency_from to currency_to."""
        parameters = {
            "api_key": self.api_key,
            "format": "json",
            "from": self.currency_from,
            "to": self.currency_to,
        }

        url = "https://api.getgeoapi.com/v2/currency/convert"

        response = requests.get(url, parameters)
        json = response.json()
        if json["status"] == "success":
            try:
                self.current_rate = float(json["rates"][self.currency_to]["rate"])
                self.last_update = datetime.now()
            except Exception:
                self.logger.error("API May have changed!")

                self.last_update = datetime.min
                self.current_rate = -1
        else:
            self.logger.error("API Key missing / invalid!")

    def get_rate(self, force_update: bool = False) -> float:
        """Get the exchange rate from currency_from to currency_to.

        The results from this operation will be cached for 2 hours, before being retrieved again.

        Parameters
        ----------
        force_update : bool
            Retrieve a live value instead of using the caches value.

        Returns
        -------
        float
            The currency exchange rate from currency_from to currency_to.

        """
        if (
            force_update
            or self.last_update is None
            or (datetime.now() - self.last_update).seconds > 7200
            or self.current_rate == 0
        ):
            self.update_cache()

        return self.current_rate

    def convert_to(self, amount: float) -> float:
        """Perform a conversion from currency_from to currency_to.

        Parameters
        ----------
        amount : float
            Amount in currency_from

        Returns
        -------
        float
            Amount in currency_to

        """
        return amount * self.get_rate()

    def convert_from(self, amount: float) -> float:
        """Perform a conversion from currency_to to currency_from.

        Parameters
        ----------
        amount : float
            Amount in currency_to

        Returns
        -------
        float
            Amount in currency_from

        """
        return amount / self.get_rate()


if __name__ == "__main__":
    import os

    from dotenv import load_dotenv

    load_dotenv()
    key = os.getenv("CURRENCY_API_KEY")
    if key is not None:
        cur = Currency(key)
        print(cur.get_rate())
