import logging
from typing import List
from datetime import datetime

import pytz
from sqlalchemy.orm import sessionmaker

from captchamonitor.utils.config import Config
from captchamonitor.utils.models import Domain
from captchamonitor.utils.small_scripts import get_traceback_information
from captchamonitor.utils.website_parser import WebsiteParser
from captchamonitor.utils.domain_attributes import DomainAttributes


class UpdateDomains:
    """
    Fetches Alexa topsites and Moz500 website and parses the list of urls in the website and inserts the urls listed there into the
    database
    """

    def __init__(
        self,
        config: Config,
        db_session: sessionmaker,
        auto_update: bool = True,
    ) -> None:
        """
        Initializes UpdateDomains

        :param config: The config class instance that contains global configuration values
        :type config: Config
        :param db_session: Database session used to connect to the database
        :type db_session: sessionmaker
        :param auto_update: Should I update the website list when __init__ is called, defaults to True
        :type auto_update: bool
        """
        # Private class attributes
        self.__db_session: sessionmaker = db_session
        self.__logger = logging.getLogger(__name__)
        self.__config: Config = config

        if auto_update:
            self.__logger.info(
                "Updating the website list using the latest version of the topsites"
            )
            self.update()

    def __insert_website_into_db(self, website_list: List[str]) -> None:
        """
        Inserts given list of websites into the database

        :param website_list: List of strings containing websites
        :type website_list: List[str]
        """
        # pylint: disable=W0703
        # Iterate over the websites in consensus file
        for website in website_list:
            query = self.__db_session.query(Domain).filter(Domain.domain == website)

            try:
                # Check the attributes
                attributes = DomainAttributes(website)

            except Exception:
                error = get_traceback_information()
                self.__logger.debug(
                    "Skipping %s since there was an error while getting its attributes:\n %s",
                    website,
                    error,
                )

            else:
                # Insert results into the database
                if query.count() == 0:
                    # Add new website
                    db_website = Domain(
                        domain=website,
                        supports_http=attributes.supports_http,
                        supports_https=attributes.supports_https,
                        supports_ftp=attributes.supports_ftp,
                        supports_ipv4=attributes.supports_ipv4,
                        supports_ipv6=attributes.supports_ipv6,
                        requires_multiple_requests=attributes.requires_multiple_requests,
                    )
                    self.__db_session.add(db_website)

                else:
                    # Or update the existing entry
                    db_website = query.first()
                    db_website.updated_at = datetime.now(pytz.utc)
                    db_website.domain = website
                    db_website.supports_http = attributes.supports_http
                    db_website.supports_https = attributes.supports_https
                    db_website.supports_ftp = attributes.supports_ftp
                    db_website.supports_ipv4 = attributes.supports_ipv4
                    db_website.supports_ipv6 = attributes.supports_ipv6
                    db_website.requires_multiple_requests = (
                        attributes.requires_multiple_requests
                    )

            finally:
                # Commit changes to the database frequently
                self.__db_session.commit()

        self.__logger.debug("Inserted a new batch of website into the database")

    def update(self) -> None:
        """
        Fetches Alexa topsites and Moz500 website and parses the list of urls in the website.
        Later, adds the websites to the database.
        """
        website = WebsiteParser()
        website.get_alexa_top_50()
        website.get_moz_top_500()
        website_list = list(website.unique_website_list)
        self.__insert_website_into_db(website_list)
        self.__logger.info(
            "Done with updating the unique website list of both Moz and Alexa sites"
        )
