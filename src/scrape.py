"""Melonbooks scraper to get images and relevant information."""

from collections import namedtuple

from bs4 import BeautifulSoup
from bs4.element import Tag
from requests import Session
from requests.adapters import HTTPAdapter
from urllib3 import PoolManager
from urllib3.util import create_urllib3_context


class AddedCipherAdapter(HTTPAdapter):
    """Cipher manager needed to get BeautifulSoup to work with Melonbooks.

    Attributes
    ----------
    poolmanager : urllib3 pool manager.

    """

    def init_poolmanager(
        self, connections: int, maxsize: int, block: bool = False, **pool_kwargs
    ):
        """Initialize the pool manager needed to make BeautifulSoup work with Melonbooks.

        Parameters
        ----------
        connections : int
            Number of connection pools to cache before discarding the least recently used pool.
        maxsize : int
            Maximum number of connections to save in the pool.
            The behavior of any connections that exceed this limit depends on the block argument.
        block : bool
            If True, any connections above the maxsize will succeed, just not saved in the pool.
            If False, any connections above the maxsize will be blocked until one request completes.
        **pool_kwargs
            See https://urllib3.readthedocs.io/en/stable/reference/urllib3.connectionpool.html#urllib3.connectionpool.ConnectionPool

        """
        ctx = create_urllib3_context(ciphers=":HIGH:!DH:!annul")
        self.poolmanager = PoolManager(
            num_pools=connections,
            maxsize=maxsize,
            block=block,
            ssl_context=ctx,
            **pool_kwargs,
        )


DoujinMetadata = namedtuple(
    "DoujinMetadata",
    [
        "title",
        "price_in_yen",
        "circle_name",
        "author_names",
        "genres",
        "events",
        "is_r18",
        "image_preview_url",
    ],
)


class DoujinScraper:
    """Wrapper class that encapsulates the logic used to scrape Melonbooks.

    Attributes
    ----------
    CIRCLE_NAME_TAG_JAPANESE : Japanese characters indicating the circle name
    AUTHOR_NAME_TAG_JAPANESE : Japanese characters indicating the author name
    GENRE_TAG_JAPANESE : Japanese characters indicating the genre tag
    EVENT_TAG_JAPANESE : Japanese characters indicating the event tag
    session : Requests library session

    """

    CIRCLE_NAME_TAG_JAPANESE = "サークル名"
    AUTHOR_NAME_TAG_JAPANESE = "作家名"
    GENRE_TAG_JAPANESE = "ジャンル"
    EVENT_TAG_JAPANESE = "イベント"

    def __init__(self):
        """Initialize the Melonbooks scraper."""
        self.session = Session()
        self.session.mount("https://www.melonbooks.co.jp", AddedCipherAdapter())

    def scrape_url(self, url: str) -> DoujinMetadata:
        """Scrapes a given URL for relevant information regarding a doujin.

        Parameters
        ----------
        url : str
            Melonbooks URL to scrape

        Returns
        -------
        DoujinMetadata
            All relevant data about a Melonbooks Doujin

        """
        if not isinstance(url, str):
            raise TypeError("url must be a string")

        page = self.session.get(f"{url}&adult_view=1")
        soup = BeautifulSoup(page.content, features="html.parser")

        title = soup.find("h1", {"class": "page-header"})
        if title is not None:
            title = title.get_text().strip()
        else:
            raise ValueError("title cannot be None")

        price_in_yen = None
        price_in_yen_text = soup.find("span", {"class": "yen"})
        if price_in_yen_text is not None:
            price_in_yen = int(
                price_in_yen_text.get_text().strip()[1:].replace(",", "")
            )
        else:
            raise ValueError("price_in_yen cannot be None")

        image_preview_url = None
        image_element = soup.find("div", {"class": "item-img"})
        if image_element is not None and isinstance(image_element, Tag):
            image_preview_url = (
                f'https:{image_element.findChildren("img")[0].attrs["src"]}'
            )
        else:
            raise ValueError("image_preview_url cannot be None")

        # Table contains some key information
        circle_name, author_names, genres, events = None, [], [], []
        is_r18 = False
        info_table = soup.find("div", {"class": "table-wrapper"})
        if info_table is not None and isinstance(info_table, Tag):
            tag_elements = info_table.findChildren("th", recursive=True)
            raw_info = {}
            for tag_element in tag_elements:
                tag_name = tag_element.get_text().strip()

                tag_info_elements = tag_element.next_sibling.next_sibling.findAll(
                    text=True, recursive=True
                )
                tag_info = [
                    info.strip()
                    for info in tag_info_elements
                    if info.strip() and info.strip() != ","
                ]
                raw_info[tag_name] = tag_info

            if self.CIRCLE_NAME_TAG_JAPANESE in raw_info:
                raw_circle_name_string = raw_info[self.CIRCLE_NAME_TAG_JAPANESE][0]
                circle_name = " ".join(raw_circle_name_string.split("\xa0")[:-1])

            if self.AUTHOR_NAME_TAG_JAPANESE in raw_info:
                author_names = raw_info[self.AUTHOR_NAME_TAG_JAPANESE]

            if self.GENRE_TAG_JAPANESE in raw_info:
                genres = raw_info[self.GENRE_TAG_JAPANESE]

            if self.EVENT_TAG_JAPANESE in raw_info:
                events = raw_info[self.EVENT_TAG_JAPANESE]

            is_r18 = info_table.findChildren("td")[-1].get_text().strip() == "18禁"

        return DoujinMetadata(
            title,
            price_in_yen,
            circle_name,
            author_names,
            genres,
            events,
            is_r18,
            image_preview_url,
        )
