import logging

import urllib3
import requests
import dns.resolver

from captchamonitor.utils.exceptions import NoSuchDomain


class DomainAttributes:
    """
    Checks if given domain supports certain protocols, IP versions, etc.
    """

    def __init__(self, domain: str) -> None:
        """
        Initializes DomainAttributes

        :param domain: Domain to check for details
        :type domain: str
        """
        # Private class attributes
        self.__logger = logging.getLogger(__name__)

        # Public class attributes
        self.domain: str = domain
        self.supports_ipv4: bool = self.__dns_resolver("A")
        self.supports_ipv6: bool = self.__dns_resolver("AAAA")
        self.supports_http: bool = self.__protocol_checker("http")
        self.supports_https: bool = self.__protocol_checker("https")
        self.supports_ftp: bool = self.__protocol_checker("ftp")
        self.requires_multiple_requests: bool = self.__multiple_requests_checker()

    def __dns_resolver(self, record_type: str) -> bool:
        """
        Returns True if the domain has given type of DNS entry

        :param record_type: The DNS record type
        :type record_type: str
        :raises NoSuchDomain: If there is no DNS record at all for the given domain
        :return: If the domain supports given record type
        :rtype: bool
        """
        try:
            dns.resolver.resolve(self.domain, record_type)  # type: ignore
            return True

        except dns.resolver.NoAnswer:
            return False

        except dns.resolver.NXDOMAIN as exception:
            self.__logger.debug("%s doesn't have any DNS records", self.domain)
            raise NoSuchDomain from exception

    def __protocol_checker(self, protocol: str) -> bool:
        """
        Returns True if the domain supports given protocol

        :param protocol: The protocol to test http, https, or ftp
        :type protocol: str
        :return: If the domain supports given protocol
        :rtype: bool
        """
        if protocol == "ftp":
            # TODO: Add a mechanism to check FTP support
            return False

        try:
            # Silence the warnings since we disable verification on purpose
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

            # Perform the request
            result = requests.get(
                f"{protocol}://{self.domain}", timeout=(3, 10), verify=False
            )
            return result.status_code in (200, 201, 202, 204, 205)

        except (
            requests.exceptions.ConnectionError,
            requests.exceptions.ReadTimeout,
        ):
            return False

    @staticmethod
    def __multiple_requests_checker() -> bool:
        """
        Returns True if multiple requests are required to fetch this domain

        Assuming True for now

        :return: Whether multiple requests are required to fetch this domain
        :rtype: bool
        """
        # TODO: Implement the actual functionality
        return True
