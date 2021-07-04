import re
import logging
from typing import List

import requests


class ProxyParser:
    """
    Parses the list of proxies
    """

    def __init__(self) -> None:
        self.host: List[str] = []
        self.port: List[int] = []
        self.country: List[str] = []
        self.google_pass: List[bool] = []
        self.anonymity: List[str] = []
        self.incoming_ip_different_from_outgoing_ip: List[bool] = []
        self.ssl: List[bool] = []
        # Private class attribute
        self.__logger = logging.getLogger(__name__)

    def get_proxy_details_spys(self) -> None:
        """
        Get the informations regarding the proxies from http://spys.me/proxy.txt.
        """
        url = "https://spys.me/proxy.txt"
        try:
            page = requests.get(url)
            proxy_list = page.text.split("\n")
            self.__logger.info("Started parsing proxies...")

            # Remove first 9 lines and last 2 lines to get just the details of the proxies
            proxy_list = proxy_list[9:-2]

            # Format: IP address:Port CountryCode-Anonymity(Noa/Anm/Hia)-SSL_support(S)-Google_passed(+)
            for line in proxy_list:

                host = line[: line.index(":")]
                port = line[line.index(":") + 1 : line.index(" ")]
                country = line[line.index(" ") + 1 : line.index(" ") + 3]
                ssl = re.findall("[-][S]", line)
                google_pass = re.findall("[ ][+]", line)
                anonymity = line[line.index(country) + 3 : line.index(country) + 4]

                ssl_bool: bool = bool(len(ssl) == 0)
                google_pass_bool: bool = bool(len(google_pass) == 0)
                incoming_ip_different_from_outgoing_ip_bool: bool = bool("!" in line)

                self.host.append(host)
                self.port.append(int(port))
                self.country.append(country)
                self.google_pass.append(google_pass_bool)
                self.anonymity.append(anonymity)
                self.incoming_ip_different_from_outgoing_ip.append(
                    incoming_ip_different_from_outgoing_ip_bool
                )
                self.ssl.append(ssl_bool)

        except requests.exceptions.ConnectionError as exception:
            self.__logger.error(
                "Fetching of %s failed \nError :: %s",
                url,
                exception,
            )
