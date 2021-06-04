import logging
from typing import Set, List

import requests
from bs4 import BeautifulSoup


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
        self.number_of_websites: int = 0
        self.uniq_website_list: Set[str] = set()

        # Private class attributes
        self.__logger = logging.getLogger(__name__)

    def __fetch_and_parse_url(self, url: str) -> BeautifulSoup:
        """
        Fetches given url and parses using BeautifulSoup

        :param url: The url of the given website
        :type url: str
        :return: The BeautifulSoup parsed HTML
        :rtype: BeautifulSoup
        """
        try:
            result = requests.get(url)
            return BeautifulSoup(result.text, "html.parser")
        except requests.ConnectionError as exception:
            self.__logger.debug(
                "Fetching of %s failed becasue of (Connection Error): [%s]",
                url,
                exception,
            )
            return BeautifulSoup("", "html.parser")
        except requests.Timeout as exception:
            self.__logger.debug(
                "Fetching of %s failed becasue of (Time out): [%s]", url, exception
            )
            return BeautifulSoup("", "html.parser")

    def __cleaning_website(self, url: str) -> str:
        """
        Cleans the urls, removing `www., http://, https://` from anywhere in the url to unify all the websites and return in lowercase

        :param url: The url of the given website
        :type url: str
        :return: The clean url after processing
        :rtype: str
        """
        try:
            url = url.replace("www.", "").replace("http://", "").replace("https://", "")
            return "http://" + url.lower()
        except AttributeError as exception:
            self.__logger.debug("Website can't be unified because: [%s]", exception)
            return ""

    def get_moz_top_500(self) -> List[str]:
        """
        Gets the Top 500 website list from moz.com/top500

        :return: List containing moz websites
        :rtype: List[str]
        """
        # Take the website as url and parse it
        url = "https://moz.com/top500"
        result = self.__fetch_and_parse_url(url)
        try:
            info = result.find_all("td")
            length = len(info)
            for _ in range(1, length, 4):
                site = info[_].a.get("href")
                self.website_list.append(self.__cleaning_website(site))
                self.uniq_website_list.add(self.__cleaning_website(site))

        except AttributeError as exception:
            self.__logger.debug(
                "Moz 500 website returns None in website url. More details are: [%s]",
                exception,
            )
        except TypeError as exception:
            self.__logger.debug(
                "Moz 500 website returns None in the information. More details are: [%s]",
                exception,
            )

        self.number_of_websites = +len(self.website_list)
        return self.website_list

    def get_alexa_top_50(self) -> List[str]:
        """Gets the Top 50 website lists from alexa.com/topsites

        :return: List containing alexa topsites
        :rtype: List[str]
        """
        url = "https://alexa.com/topsites"
        result = self.__fetch_and_parse_url(url)
        try:
            # Parses according to div and class "tr site-listing"
            info = result.find_all("div", class_="tr site-listing")
            length = len(info)
            self.number_of_websites = +length
            for _ in range(0, length):
                site = info[_].a.text
                self.website_list.append(self.__cleaning_website(site))
                self.uniq_website_list.add(self.__cleaning_website(site))

        except AttributeError as exception:
            self.__logger.debug(
                "Alexa Topsite returns None in website url. More details are: [%s]",
                exception,
            )
        except TypeError as exception:
            self.number_of_websites = 0
            self.__logger.debug(
                "Alexa Topsite returns None in the information. More details are: [%s]",
                exception,
            )
        return self.website_list
