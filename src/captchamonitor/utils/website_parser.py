import re
import logging
from typing import List, Optional
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from captchamonitor.utils.exceptions import (
    WebsiteParserFetchError,
    WebsiteParserParseError,
)


class WebsiteParser:
    """
    This code scrapes and extracts top 500 websites from Moz Top 500 and also the top 50 websites from Alexa Topsites.
    Uses BeautifulSoup to scrape website and get a list of them
    """

    def __init__(self) -> None:
        """
        Initializes website parser
        """
        # Public class attributes
        self.website_list: List[str] = []

        # Private class attributes
        self.__logger = logging.getLogger(__name__)

    @property
    def number_of_websites(self) -> int:
        """
        Returns the total number of websites parsed

        :return: The total number of websites parsed
        :rtype: int
        """
        return len(self.website_list)

    @property
    def unique_website_list(self) -> List[str]:
        """
        Returns the list of unique websites

        :return: The list of unique websites
        :rtype: List[str]
        """
        return list(set(self.website_list))

    def __fetch_url(self, url: str) -> BeautifulSoup:
        """
        Fetches given URL and parses using BeautifulSoup

        :param url: The URL of the given website
        :type url: str
        :raises WebsiteParserFetchError: If it cannot fetch the given URL
        :return: The BeautifulSoup parsed HTML
        :rtype: BeautifulSoup
        """
        try:
            result = requests.get(url)

        except requests.ConnectionError as exception:
            self.__logger.debug(
                "Fetching of %s failed because of Connection Error: %s",
                url,
                exception,
            )
            raise WebsiteParserFetchError from exception

        except requests.Timeout as exception:
            self.__logger.debug(
                "Fetching of %s failed because of timeout: %s", url, exception
            )
            raise WebsiteParserFetchError from exception

        return BeautifulSoup(result.text, "html.parser")

    @staticmethod
    def __extract_hostname_from_url(url: str) -> Optional[str]:
        """
        Extracts the hostname from given URL, turns into lowercase, and removes
        any preceding www subdomains

        :param url: The URL of the given website
        :type url: str
        :return: Extracted hostname after processing
        :rtype: Optional[str]
        """
        # Add a protocol is there is none
        if not re.match("(?:http|ftp|https)://", url):
            url = f"http://{url}"

        # Extract the hostname
        hostname = urlparse(url).hostname

        if hostname is not None:
            # Convert to lowercase
            hostname = hostname.lower()

            # Get rid of wwww, if there is any
            hostname = hostname.replace("www.", "")

            return hostname

        return None

    def get_moz_top_500(self) -> List[str]:
        """
        Gets the Top 500 website list from moz.com/top500

        :raises WebsiteParserParseError: If the website layout is different than expected
        :return: List containing moz websites
        :rtype: List[str]
        """
        url = "https://moz.com/top500"

        page = self.__fetch_url(url)
        table_rows = page.find_all("td")

        if len(table_rows) == 0:
            raise WebsiteParserParseError

        for _ in range(1, len(table_rows), 4):
            raw_url = table_rows[_].a.get("href")
            hostname = self.__extract_hostname_from_url(raw_url)

            if hostname is not None:
                self.website_list.append(hostname)

        return self.website_list

    def get_alexa_top_50(self) -> List[str]:
        """
        Gets the Top 50 website lists from alexa.com/topsites

        :raises WebsiteParserParseError: If the website layout is different than expected
        :return: List containing Alexa topsites
        :rtype: List[str]
        """
        url = "https://alexa.com/topsites"

        page = self.__fetch_url(url)
        table_rows = page.find_all("div", class_="tr site-listing")

        if len(table_rows) == 0:
            raise WebsiteParserParseError

        for row in table_rows:
            raw_url = row.a.text
            hostname = self.__extract_hostname_from_url(raw_url)

            if hostname is not None:
                self.website_list.append(hostname)

        return self.website_list
