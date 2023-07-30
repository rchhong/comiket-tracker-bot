from datetime import date, datetime
import requests
import logging
from logging import FileHandler, Logger


class Currency:
    current_rate: float
    last_update: datetime
    api_key: str
    currency_from: str
    currency_to: str
    logger: Logger

    def __init__(
        self,
        api_key: str,
        currency_from: str = "JPY",
        currency_to: str = "USD",
        log_file="currency.log",
    ):
        self.current_rate = 0
        self.last_update = datetime.min
        self.api_key = api_key
        self.currency_from = currency_from
        self.currency_to = currency_to

        self.logger = logging.getLogger(__name__)

        lfHandler = logging.FileHandler(filename=log_file, encoding="utf-8", mode="w")
        lfHandler.setLevel(logging.ERROR)
        lfHandler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )

        self.logger.addHandler(lfHandler)

    def update_cache(self) -> None:
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
        if (
            force_update
            or self.last_update is None
            or (datetime.now() - self.last_update).seconds > 7200
        ):
            self.update_cache()

        return self.current_rate

    def convert_to(self, amount: float) -> float:
        return amount * self.get_rate()

    def convert_from(self, amount: float) -> float:
        return amount / self.get_rate()


if __name__ == "__main__":
    from dotenv import load_dotenv
    import os

    load_dotenv()
    key = os.getenv("CURRENCY_API_KEY")
    if key is not None:
        cur = Currency(key)
        print(cur.get_rate())
