from src.doujin import Doujin
from pymongo import MongoClient
import os


class DoujinDAO:
    def __init__(self, connection_str: str) -> None:
        self.db = MongoClient(connection_str).get_database(os.getenv("MONGO_DB_NAME"))

    def add_doujin(self, doujin: Doujin):
        id = self.db.doujins.insert_one(vars(doujin)).inserted_id
        return id

    def get_doujin(self, url: str):
        parameters = {"url": url}
        result = self.db.doujins.find_one(parameters)

        return Doujin(**result) if result else None

    # TODO: Optimization - remove doujins that have 0 reservation
