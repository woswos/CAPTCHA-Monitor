import json
import logging
from typing import Dict, List, Optional
from datetime import datetime, timezone
from dataclasses import dataclass

import requests
import country_converter as coco

from captchamonitor.utils.exceptions import OnionooConnectionError


@dataclass
class OnionooRelayEntry:
    """
    Stores a Onionoo relay entry
    """

    fingerprint: str
    ipv4_exiting_allowed: bool
    ipv6_exiting_allowed: bool
    country: Optional[str]
    country_name: Optional[str]
    continent: Optional[str]
    nickname: Optional[str]
    first_seen: Optional[datetime]
    last_seen: Optional[datetime]
    version: Optional[str]
    asn: Optional[str]
    asn_name: Optional[str]
    platform: Optional[str]
    exit_policy_summary: Optional[dict]
    exit_policy_v6_summary: Optional[dict]


class Onionoo:
    """
    Uses Onionoo to get the details of the given relay
    """

    def __init__(self, fingerprints: List[str]) -> None:
        """
        Initialize, fetch, and parse the details

        :param fingerprints: List of BASE64 encoded SHA256 hash of the relays
        :type fingerprints: List[str]
        """
        # Public class attributes
        self.fingerprint_list: List[str] = fingerprints
        self.relay_entries: List[OnionooRelayEntry] = []

        # Private class attributes
        self.__logger = logging.getLogger(__name__)
        self.__fingerprint_list_str: str = "".join(
            f"{str(fpr)}," for fpr in self.fingerprint_list
        )[:-1]
        self.__lookup_fields: str = f"fingerprint,nickname,exit_policy_summary,exit_policy_v6_summary,first_seen,last_seen,country,country_name,as,as_name,version,platform&lookup={self.__fingerprint_list_str}"
        self.__lookup_url: str = (
            f"https://onionoo.torproject.org/details?fields={self.__lookup_fields}"
        )
        self.__relay_data: Dict
        self.__onionoo_datetime_format: str = "%Y-%m-%d %H:%M:%S"
        self.__exit_ports: List[int] = [80, 443]

        # Execute the private methods
        self.__get_details()
        for relay in self.__relay_data:
            self.relay_entries.append(self.__parse_details_of_relay(relay))

    def __get_details(self) -> None:
        """
        Performs a request to Onioon API

        :raises OnionooConnectionError: If cannot connect to the API
        """
        try:
            response = json.loads(requests.get(self.__lookup_url).text)
            self.__relay_data = response["relays"]

        except Exception as exception:
            self.__logger.debug("Could not connect to Onionoo: %s", exception)
            raise OnionooConnectionError from exception

    def __parse_details_of_relay(self, relay_data: Dict) -> OnionooRelayEntry:
        """
        Parses given Onionoo JSON response

        :param relay_data: JSON data
        :type relay_data: Dict
        :return: OnionooRelayEntry object
        :rtype: OnionooRelayEntry
        """
        # TODO: Please refactor me into smaller functions
        # pylint: disable=R0914
        # Parse metadata
        fingerprint = relay_data.get("fingerprint", None)
        country = relay_data.get("country", None)
        country_name = relay_data.get("country_name", None)
        continent = coco.convert(names=country, to="continent")
        nickname = relay_data.get("nickname", None)
        version = relay_data.get("version", None)
        asn = relay_data.get("as", None)
        asn_name = relay_data.get("as_name", None)
        platform = relay_data.get("platform", None)

        # Parse exit polices
        exit_policy_summary = relay_data.get("exit_policy_summary", None)
        exit_policy_v6_summary = relay_data.get("exit_policy_v6_summary", None)

        ipv4_exiting_allowed = self.__is_exiting_allowed(
            exit_policy_summary, self.__exit_ports
        )
        ipv6_exiting_allowed = self.__is_exiting_allowed(
            exit_policy_v6_summary, self.__exit_ports
        )

        # Parse first and last seen fields
        first_seen = relay_data.get("first_seen", None)
        last_seen = relay_data.get("last_seen", None)
        if first_seen is not None:
            first_seen = datetime.strptime(
                first_seen, self.__onionoo_datetime_format
            ).replace(tzinfo=timezone.utc)
        if last_seen is not None:
            last_seen = datetime.strptime(
                last_seen, self.__onionoo_datetime_format
            ).replace(tzinfo=timezone.utc)

        return OnionooRelayEntry(
            fingerprint=fingerprint,
            ipv4_exiting_allowed=ipv4_exiting_allowed,
            ipv6_exiting_allowed=ipv6_exiting_allowed,
            country=country,
            country_name=country_name,
            continent=continent,
            nickname=nickname,
            first_seen=first_seen,
            last_seen=last_seen,
            version=version,
            asn=asn,
            asn_name=asn_name,
            platform=platform,
            exit_policy_summary=exit_policy_summary,
            exit_policy_v6_summary=exit_policy_v6_summary,
        )

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
