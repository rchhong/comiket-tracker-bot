from bs4 import BeautifulSoup
from urllib3.util import create_urllib3_context
from urllib3 import PoolManager
from requests.adapters import HTTPAdapter
from requests import Session
from collections import namedtuple
import re

CIRCLE_NAME_TAG_JAPANESE = 'サークル名'
ARTIST_NAME_TAG_JAPANESE = '作家名'
GENRE_TAG_JAPANESE = 'ジャンル'
EVENT_TAG_JAPANESE = 'イベント'


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

Doujin = namedtuple('Doujin', ["title", "price_in_yen", "circle_name", "author_name", "genre", "event", "is_r18", "image_preview_url"])

def scrape_url(url: str):
    page = s.get(f"{url}&adult_view=1")
    soup = BeautifulSoup(page.content, features="html.parser")

    title = soup.find("h1", {"class": "page-header"}).string.strip()
    price_in_yen = int(soup.find("span", {"class": "yen"}).string.strip()[
                    1:].replace(",", ""))

    # Table contains some key information
    info_table = soup.find("div", {"class": "table-wrapper"})
    raw_tags = info_table.findChildren(
        "th", recursive=True
    )

    available_tags = [tag.string for tag in raw_tags]
    raw_tag_info = [raw_tag.next_sibling.next_sibling.findAll(text=True, recursive=True) for raw_tag in raw_tags]
    raw_tag_info = [[x.strip() for x in raw_tag if x.strip() and x.strip() != ","] for raw_tag in raw_tag_info]

    raw_info = dict(zip(available_tags, raw_tag_info))

    circle_name, author_name, genre, event = None, None, None, None

    if CIRCLE_NAME_TAG_JAPANESE in raw_info:
        raw_circle_name_string = raw_info[CIRCLE_NAME_TAG_JAPANESE][0]
        circle_name = " ".join(
            raw_circle_name_string.split("\xa0")[:-1])

    if ARTIST_NAME_TAG_JAPANESE in raw_info:
        author_name = ", ".join(raw_info[ARTIST_NAME_TAG_JAPANESE])

    if GENRE_TAG_JAPANESE in raw_info:
        genre = ", ".join(raw_info[GENRE_TAG_JAPANESE])

    if EVENT_TAG_JAPANESE in raw_info:
        event = ", ".join(raw_info[EVENT_TAG_JAPANESE])

    is_r18 = info_table.findChildren('td')[-1].string.strip() == "18禁"
    image_preview_url = f'https:{soup.find("div", {"class": "item-img"}).findChildren("img")[0].attrs["src"]}'

    return Doujin(title, price_in_yen, circle_name, author_name, genre, event, is_r18, image_preview_url)