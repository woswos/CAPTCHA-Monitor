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
        :param auto_update: Should I update the proxy list when __init__ is called, defaults to True
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
        proxy_host_list: List[str],
        proxy_port_list: List[int],
        proxy_ssl_list: List[bool],
        proxy_google_pass_list: List[bool],
        proxy_country_list: List[str],
        proxy_anon_list: List[str],
        proxy_incoming_ip_different_from_outgoing_ip_list: List[bool],
    ) -> None:
        """
        Inserts given list of proxys into the database

        :param proxy_host_list: List of strings containing proxy host
        :type proxy_host_list: List[str]
        :param proxy_port_list: List of integers containing proxy port
        :type proxy_port_list: List[str]
        :param proxy_ssl_list: List of Boolean values to check if proxies support ssl
        :type proxy_ssl_list: List[bool]
        :param proxy_google_pass_list: List of Boolean values to check if proxies are blocked or not by Google
        :type proxy_google_pass_list: List[bool]
        :param proxy_country_list: List of strings containing country code
        :type proxy_country_list: List[str]
        :param proxy_anon_list: List of strings describing the anonymity of the proxies
        :type proxy_anon_list: List[str]
        :param proxy_incoming_ip_different_from_outgoing_ip_list: List of Boolean values to check if proxies have incoming ip different from the outgoing ip
        :type proxy_incoming_ip_different_from_outgoing_ip_list: List[bool]
        """
        # pylint: disable=W0703
        # Iterate over the proxys
        for (
            proxy_host,
            proxy_port,
            proxy_ssl,
            proxy_google_pass,
            proxy_country,
            proxy_anon,
            proxy_incoming_ip_different_from_outgoing_ip,
        ) in zip(
            proxy_host_list,
            proxy_port_list,
            proxy_ssl_list,
            proxy_google_pass_list,
            proxy_country_list,
            proxy_anon_list,
            proxy_incoming_ip_different_from_outgoing_ip_list,
        ):
            query = self.__db_session.query(Proxy).filter(
                Proxy.proxy_host == proxy_host
            )
            # Insert results into the database
            if query.count() == 0:
                # Add new proxy
                db_proxy = Proxy(
                    proxy_host=proxy_host,
                    proxy_port=proxy_port,
                    proxy_country=proxy_country,
                    proxy_google_pass=proxy_google_pass,
                    proxy_anon=proxy_anon,
                    proxy_incoming_ip_different_from_outgoing_ip=proxy_incoming_ip_different_from_outgoing_ip,
                    proxy_ssl=proxy_ssl,
                )
                self.__db_session.add(db_proxy)

            else:
                # Or update the existing entry
                db_proxy = query.first()
                db_proxy.updated_at = datetime.now(pytz.utc)
                db_proxy.proxy_host = proxy_host
                db_proxy.proxy_port = proxy_port
                db_proxy.proxy_country = proxy_country
                db_proxy.proxy_google_pass = proxy_google_pass
                db_proxy.proxy_anon = proxy_anon
                db_proxy.proxy_incoming_ip_different_from_outgoing_ip = (
                    proxy_incoming_ip_different_from_outgoing_ip
                )
                db_proxy.proxy_ssl = proxy_ssl
                # Commit changes to the database frequently

            self.__db_session.commit()

        self.__logger.debug("Inserted a new batch of proxy into the database")

    def update(self) -> None:
        """
        Fetches the proxies and parses the list of proxy.
        Later, adds the proxys to the database.
        """
        proxy = ProxyParser()
        proxy.get_proxy_details()

        proxy_host_list = proxy.proxy_host
        proxy_port_list = proxy.proxy_port
        proxy_ssl_list = proxy.proxy_ssl
        proxy_google_pass_list = proxy.proxy_google_pass
        proxy_country_list = proxy.proxy_country
        proxy_anon_list = proxy.proxy_anon
        proxy_incoming_ip_different_from_outgoing_ip_list = (
            proxy.incoming_ip_different_from_outgoing_ip
        )

        self.__insert_proxy_into_db(
            proxy_host_list,
            proxy_port_list,
            proxy_ssl_list,
            proxy_google_pass_list,
            proxy_country_list,
            proxy_anon_list,
            proxy_incoming_ip_different_from_outgoing_ip_list,
        )
        self.__logger.info("Done with updating the proxy list")
