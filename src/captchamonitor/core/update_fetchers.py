import logging
from typing import Set

from sqlalchemy.orm import sessionmaker

from captchamonitor.utils.config import Config
from captchamonitor.utils.models import Fetcher


class UpdateFetchers:
    """
    Discovers the list of Docker containers dedicated to web browsers and adds
    them to the database
    """

    def __init__(
        self,
        config: Config,
        db_session: sessionmaker,  # pylint: disable=R0801
    ) -> None:
        """
        Initializes UpdateFetchers

        :param config: The config class instance that contains global configuration values
        :type config: Config
        :param db_session: Database session used to connect to the database
        :type db_session: sessionmaker
        """
        # Private class attributes
        self.__logger = logging.getLogger(__name__)
        self.__config: Config = config
        self.__db_session: sessionmaker = db_session

        # Calls to the class methods
        self.update()

    def __discover_browser_containers(self) -> Set:
        """
        Parses the config file to see which web browsers are available

        :return: List of web browsers
        :rtype: Set
        """
        keywords = ["docker", "browser"]
        browsers = set()
        for config in self.__config.keys():
            if all(x in config for x in keywords):
                name = config.split("_")
                browsers.add(f"{name[1]}_{name[2]}")
        return browsers

    def update(self) -> None:
        """
        Automatically discovers the new fetchers that are using Docker containers
        and adds them to the database
        """
        self.__logger.info(
            "Updating the fetchers list by discovering the available Docker containers"
        )
        browsers = self.__discover_browser_containers()

        for browser in browsers:
            for uses_proxy_type in [None, "tor", "http"]:
                # Check if there is a matching fetcher in the database
                query = (
                    self.__db_session.query(Fetcher)
                    .filter(Fetcher.method == browser)
                    .filter(
                        Fetcher.uses_proxy_type == uses_proxy_type,
                    )
                )

                # Insert the fetcher if it doesn't already exist'
                if query.count() == 0:
                    fetcher = Fetcher(
                        method=browser,
                        uses_proxy_type=uses_proxy_type,
                        version="0",
                    )
                    self.__db_session.add(fetcher)

        # Save changes to the database
        self.__db_session.commit()
