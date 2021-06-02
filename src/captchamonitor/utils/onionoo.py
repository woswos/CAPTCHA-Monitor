import json
import logging
from typing import Optional, Dict, List
from datetime import datetime, timezone
import requests
import country_converter as coco
from captchamonitor.utils.exceptions import (
    OnionooConnectionError,
    OnionooMissingRelayError,
)


class Onionoo:
    """
    Uses Onionoo to get the details of the given relay
    """

    def __init__(self, fingerprint: str) -> None:
        """
        Initialize, fetch, and parse the details

        :param fingerprint: BASE64 encoded SHA256 hash of the relay
        :type fingerprint: str
        """
        # Public class attributes
        self.fingerprint: str = fingerprint
        self.relay_data: Dict
        self.ipv4_exiting_allowed: bool
        self.ipv6_exiting_allowed: bool
        self.country: Optional[str]
        self.country_name: Optional[str]
        self.continent: Optional[str]
        self.nickname: Optional[str]
        self.first_seen: Optional[datetime]
        self.last_seen: Optional[datetime]
        self.version: Optional[str]
        self.asn: Optional[str]
        self.asn_name: Optional[str]
        self.platform: Optional[str]
        self.exit_policy_summary: Optional[dict]
        self.exit_policy_v6_summary: Optional[dict]

        # Private class attributes
        self.__logger = logging.getLogger(__name__)
        self.__lookup_fields: str = f"fingerprint,nickname,exit_policy_summary,exit_policy_v6_summary,first_seen,last_seen,country,country_name,as,as_name,version,platform&lookup={fingerprint}"
        self.__lookup_url: str = (
            f"https://onionoo.torproject.org/details?fields={self.__lookup_fields}"
        )
        self.__onionoo_datetime_format: str = "%Y-%m-%d %H:%M:%S"
        self.__exit_ports: List[int] = [80, 443]

        # Execute the private methods
        self.__get_details()
        self.__parse_details()

    def __get_details(self) -> None:
        """
        Performs a request to Onioon API

        :raises OnionooMissingRelay: Given relay is missing on Onionoo
        :raises OnionooConnectionError: Cannot connect to the API
        """
        try:
            response = json.loads(requests.get(self.__lookup_url).text)
            self.relay_data = response["relays"][0]

        except IndexError as exception:
            self.__logger.debug(
                "Upps, this relay does not exist on Onionoo yet: %s",
                self.fingerprint,
            )
            raise OnionooMissingRelayError from exception

        except Exception as exception:
            self.__logger.debug("Could not connect to Onionoo: %s", exception)
            raise OnionooConnectionError from exception

    def __parse_details(self) -> None:
        """
        Parses the JSON response
        """
        # Parse metadata
        self.country = self.relay_data.get("country", None)
        self.country_name = self.relay_data.get("country_name", None)
        self.continent = coco.convert(names=self.country, to="continent")
        self.nickname = self.relay_data.get("nickname", None)
        self.version = self.relay_data.get("version", None)
        self.asn = self.relay_data.get("as", None)
        self.asn_name = self.relay_data.get("as_name", None)
        self.platform = self.relay_data.get("platform", None)

        # Parse exit polices
        self.exit_policy_summary = self.relay_data.get("exit_policy_summary", None)
        self.exit_policy_v6_summary = self.relay_data.get(
            "exit_policy_v6_summary", None
        )

        self.ipv4_exiting_allowed = self.__is_exiting_allowed(
            self.exit_policy_summary, self.__exit_ports
        )
        self.ipv6_exiting_allowed = self.__is_exiting_allowed(
            self.exit_policy_v6_summary, self.__exit_ports
        )

        # Parse first and last seen fields
        first_seen = self.relay_data.get("first_seen", None)
        last_seen = self.relay_data.get("last_seen", None)
        if first_seen is not None:
            first_seen = datetime.strptime(
                first_seen, self.__onionoo_datetime_format
            ).replace(tzinfo=timezone.utc)
        if last_seen is not None:
            last_seen = datetime.strptime(
                last_seen, self.__onionoo_datetime_format
            ).replace(tzinfo=timezone.utc)
        self.first_seen = first_seen
        self.last_seen = last_seen

    def __is_exiting_allowed(
        self, exit_policy_summary: Optional[Dict], exit_ports: List[int]
    ) -> bool:
        """
        Checks whether given exit policy summary allows exits on ports 443 or 80

        :param exit_policy_summary: Exit policy summary obtained from Onionoo
        :type exit_policy_summary: Dict
        :param exit_ports: List of exit ports to check
        :type exit_ports: List[int]
        :return: Whether given exit policy summary allows exiting
        :rtype: bool
        """
        # Assume false by default
        is_exiting_allowed = False

        if exit_policy_summary is not None:
            accept_list = exit_policy_summary.get("accept", None)
            reject_list = exit_policy_summary.get("reject", None)

            # Check the accept list
            if accept_list is not None:
                for port in exit_ports:
                    is_exiting_allowed = (
                        self.__is_in_range(accept_list, port) or is_exiting_allowed
                    )

            # Check the reject list
            if reject_list is not None:
                for port in exit_ports:
                    is_exiting_allowed = (
                        not self.__is_in_range(reject_list, port)
                    ) or is_exiting_allowed

        return is_exiting_allowed

    @staticmethod
    def __is_in_range(port_list: List[str], given_port: int) -> bool:
        """
        Checks whether given port is in the port list range

        :param port_list: Port list to check, obtained from Onionoo API
        :type port_list: List[str]
        :param given_port: Port to check
        :type given_port: int
        :return: Whether given port is in the port list range
        :rtype: bool
        """
        # Assume false by default
        is_in_range = False

        for port in port_list:
            if ("-" not in str(port)) and (int(port) == given_port):
                is_in_range = True

            elif "-" in str(port):
                low = int(port.split("-")[0])
                high = int(port.split("-")[1])

                if low <= given_port <= high:
                    is_in_range = True

        return is_in_range
