import re
from typing import List

import requests


class ProxyParser:
    """
    Parses the list of proxies
    """

    def __init__(self) -> None:
        self.proxy_url = "http://spys.me/proxy.txt"
        self.proxy_host: List[str] = []
        self.proxy_port: List[int] = []
        self.proxy_country: List[str] = []
        self.proxy_google_pass: List[bool] = []
        self.proxy_anon: List[str] = []
        self.incoming_ip_different_from_outgoing_ip: List[bool] = []
        self.proxy_ssl: List[bool] = []

    def get_proxy_details(self) -> None:
        """
        Get the informations regarding the proxies from http://spys.me/proxy.txt.
        """

        page = requests.get(self.proxy_url)

        proxy_list = page.text.split("\n")

        # Remove first 9 lines and last 2 lines to get just the details of the proxies
        proxy_list = proxy_list[9:-2]

        # Format: IP address:Port CountryCode-Anonymity(Noa/Anm/Hia)-SSL_support(S)-Google_passed(+)
        for line in proxy_list:

            proxy_host = line[: line.index(":")]
            proxy_port = line[line.index(":") + 1 : line.index(" ")]
            proxy_country = line[line.index(" ") + 1 : line.index(" ") + 3]
            proxy_ssl = re.findall("[-][S]", line)
            proxy_google_pass = re.findall("[ ][+]", line)

            proxy_anon = line[
                line.index(proxy_country) + 3 : line.index(proxy_country) + 4
            ]
            proxy_ssl_b: bool
            incoming_ip_different_from_outgoing_ip_b: bool
            proxy_google_pass_b: bool

            if len(proxy_ssl) == 0:
                proxy_ssl_b = False
            else:
                proxy_ssl_b = True

            if len(proxy_google_pass) == 0:
                proxy_google_pass_b = False
            else:
                proxy_google_pass_b = True

            # if "!" in line:
            incoming_ip_different_from_outgoing_ip_b = bool("!" in line)
            # else:
            #     incoming_ip_different_from_outgoing_ip_b = False

            self.proxy_host.append(proxy_host)
            self.proxy_port.append(int(proxy_port))
            self.proxy_country.append(proxy_country)
            self.proxy_google_pass.append(proxy_google_pass_b)
            self.proxy_anon.append(proxy_anon)
            self.incoming_ip_different_from_outgoing_ip.append(
                incoming_ip_different_from_outgoing_ip_b
            )
            self.proxy_ssl.append(proxy_ssl_b)
