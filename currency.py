from datetime import date, datetime
import requests

class Currency:
    current_rate: float
    last_update: datetime
    api_key: str
    currency_from : str
    currency_to : str
    def __init__(self, api_key:str, currency_from:str="JPY", currency_to:str="USD"):
        self.current_rate = 0
        self.last_update = None
        self.api_key = api_key
        self.currency_from = currency_from
        self.currency_to = currency_to

    def update_cache (self):

        parameters = {"api_key": self.api_key, "format": "json", "from" : self.currency_from, "to" : self.currency_to}

        url = "https://api.getgeoapi.com/v2/currency/convert"

        response = requests.get(url, parameters)
        json = response.json()
        print(response.json())
        if json["status"] == "success":
            self.current_rate = json["rates"]["USD"]["rate"]
            self.last_update = datetime.now()

            
    def get_rate (self, force_update:bool = False):
        
        if force_update or self.last_update is None or (datetime.now() - self.last_update).seconds > 7200:
            self.update_cache()
        
        return self.current_rate

if __name__ == "__main__":
    from dotenv import load_dotenv
    import os
    load_dotenv()
    key = os.getenv("CURRENCY_API_KEY")

    cur = Currency(key)
    print (cur.get_rate())