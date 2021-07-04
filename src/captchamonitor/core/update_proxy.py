import logging
from typing import List
from datetime import datetime

import pytz
from sqlalchemy.orm import sessionmaker

from captchamonitor.utils.config import Config
from captchamonitor.utils.models import Proxy
from captchamonitor.utils.proxy_parser import ProxyParser


class UpdateProxy:
    """
    Fetches list of Proxy details like proxy host, proxy port, does it support ssl, passes google or not, etc.
    """

    def __init__(
        self,
        config: Config,
        db_session: sessionmaker,
        auto_update: bool = True,
    ) -> None:
        """
        Initializes UpdateProxy

        :param config: The config class instance that contains global configuration values
        :type config: Config
        :param db_session: Database session used to connect to the database
        :type db_session: sessionmaker
        :param auto_update: Should the proxy list update when __init__ is called, defaults to True
        :type auto_update: bool
        """
        # Private class attributes
        self.__db_session: sessionmaker = db_session
        self.__logger = logging.getLogger(__name__)
        self.__config: Config = config  # pylint: disable=W0238

        if auto_update:
            self.__logger.info(
                "Updating the proxy list using the latest version of the spys.me/proxy.txt"
            )
            self.update()

    # pylint: disable=R0914
    def __insert_proxy_into_db(
        self,
        host_list: List[str],
        port_list: List[int],
        ssl_list: List[bool],
        google_pass_list: List[bool],
        country_list: List[str],
        anonymity_list: List[str],
        incoming_ip_different_from_outgoing_ip_list: List[bool],
    ) -> None:
        """
        Inserts given list of proxies into the database

        :param host_list: List of strings containing proxy host
        :type host_list: List[str]
        :param port_list: List of integers containing proxy port
        :type port_list: List[str]
        :param ssl_list: List of Boolean values to check if proxies support ssl
        :type ssl_list: List[bool]
        :param google_pass_list: List of Boolean values to check if proxies are blocked or not by Google
        :type google_pass_list: List[bool]
        :param country_list: List of strings containing country code
        :type country_list: List[str]
        :param anonymity_list: List of strings describing the anonymity of the proxies
        :type anonymity_list: List[str]
        :param incoming_ip_different_from_outgoing_ip_list: List of Boolean values to check if proxies have incoming ip different from the outgoing ip
        :type incoming_ip_different_from_outgoing_ip_list: List[bool]
        """
        # Iterate over the proxies
        for (
            host,
            port,
            ssl,
            google_pass,
            country,
            anonymity,
            incoming_ip_different_from_outgoing_ip,
        ) in zip(
            host_list,
            port_list,
            ssl_list,
            google_pass_list,
            country_list,
            anonymity_list,
            incoming_ip_different_from_outgoing_ip_list,
        ):
            # Filters only when host and port of proxies match, else we don't filter proxies.
            # For example there can exist a proxy with same host but different port and we want to look at them as two individual proxies.
            query = self.__db_session.query(Proxy).filter(
                Proxy.host == host,
                Proxy.port == port,
            )
            # Insert results into the database
            if query.count() == 0:
                # Check if table is empty and add new proxy
                db_proxy = Proxy(
                    host=host,
                    port=port,
                    country=country,
                    google_pass=google_pass,
                    anonymity=anonymity,
                    incoming_ip_different_from_outgoing_ip=incoming_ip_different_from_outgoing_ip,
                    ssl=ssl,
                )
                self.__db_session.add(db_proxy)

            else:
                # Update the existing entry
                db_proxy = query.first()
                db_proxy.updated_at = datetime.now(pytz.utc)
                db_proxy.host = host
                db_proxy.port = port
                db_proxy.country = country
                db_proxy.google_pass = google_pass
                db_proxy.anonymity = anonymity
                db_proxy.incoming_ip_different_from_outgoing_ip = (
                    incoming_ip_different_from_outgoing_ip
                )
                db_proxy.ssl = ssl

            # Commit to the database
            self.__db_session.commit()

        self.__logger.debug("Inserted a new batch of proxy into the database")

    def update(self) -> None:
        """
        Fetches the proxies and parses the list of proxy.
        Later, adds the proxies to the database.
        """
        proxy = ProxyParser()
        proxy.get_proxy_details_spys()

        self.__insert_proxy_into_db(
            proxy.host,
            proxy.port,
            proxy.ssl,
            proxy.google_pass,
            proxy.country,
            proxy.anonymity,
            proxy.incoming_ip_different_from_outgoing_ip,
        )
        self.__logger.info("Done with updating the proxy list")
