from bs4 import BeautifulSoup
from urllib3.util import create_urllib3_context
from urllib3 import PoolManager
from requests.adapters import HTTPAdapter
from requests import Session


class AddedCipherAdapter(HTTPAdapter):
    def init_poolmanager(self, connections, maxsize, block=False):
        ctx = create_urllib3_context(ciphers=":HIGH:!DH:!aNULL")
        self.poolmanager = PoolManager(
            num_pools=connections,
            maxsize=maxsize,
            block=block,
            ssl_context=ctx
        )

s = Session()
s.mount('https://www.melonbooks.co.jp', AddedCipherAdapter())

def scrape_url(url):
    page = s.get(url)
    soup = BeautifulSoup(page.content, features="html.parser")

    title = soup.find("h1", {"class": "page-header"}).string.strip()
    price_in_yen = int(soup.find("span", {"class": "yen"}).string.strip()[
                    1:].replace(",", ""))

    # Table contains some key information
    info_table = soup.find("div", {"class", "table-wrapper"})
    relevant_table_children = info_table.findChildren(
        "a", {"class": ""}, recursive=True
    )

    circle_name = " ".join(
        relevant_table_children[0].string.strip().split("\xa0")[:-1])
    author_name = relevant_table_children[1].string.strip()
    genre = relevant_table_children[2].string.strip()
    event = relevant_table_children[3].string.strip()
    is_r18 = info_table.findChildren('td')[-1].string.strip() == "18禁"
    image_preview_url = f'https:{soup.find("div", {"class": "item-img"}).findChildren("img")[0].attrs["src"]}'

    return title, price_in_yen, circle_name, author_name, genre, event, is_r18, image_preview_url
