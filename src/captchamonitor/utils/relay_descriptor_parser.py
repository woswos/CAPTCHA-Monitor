import logging
from typing import List, Optional
from dataclasses import dataclass
from captchamonitor.utils.exceptions import (
    RelayDescriptorParserFileNotFoundError,
)


@dataclass
class RelayDescriptorEntry:
    """
    Stores a relay descriptor entry
    See https://gitweb.torproject.org/torspec.git/tree/dir-spec.txt#n409 for
    exact details

    :param nickname: router nickname
    :type nickname: str
    :param address: relay's current IPv4 address
    :type address: str
    :param bandwidth_avg: the "average" bandwidth is the volume per second that the OR is willing to sustain over long periods
    :type bandwidth_avg: int
    :param bandwidth_burst: the "burst" bandwidth is the volume that the OR is willing to sustain in very short intervals
    :type bandwidth_burst: int
    :param bandwidth_observed: the "observed" value is an estimate of the capacity this relay can handle
    :type bandwidth_observed: int
    :param platform: a human-readable string describing the system on which this OR is running
    :type platform: str
    :param fingerprint: a HASH_LEN-byte of asn1 encoded public key, encoded in hex
    :type fingerprint: str
    :param uptime: the number of seconds that this OR process has been running.
    :type uptime: int
    :param accept: the rules that an OR follows when deciding whether to allow a new stream to a given IPv4 address
    :type accept: list
    :param reject: the rules that an OR follows when deciding whether to allow a new stream to a given IPv4 address
    :type reject: list
    :param IPv6_accept: the rules that an OR follows when deciding whether to allow a new stream to a given IPv6 address
    :type IPv6_accept: list
    :param IPv6_reject: the rules that an OR follows when deciding whether to allow a new stream to a given IPv6 address
    :type IPv6_reject: list
    :param family: If two ORs list one another in their "family" entries, then OPs should treat them as a single OR for the purpose of path selection
    :type family: list

    :returns: RelayDescriptorEntry object
    """

    nickname: str
    address: str
    bandwidth_avg: Optional[int]
    bandwidth_burst: Optional[int]
    bandwidth_observed: Optional[int]
    platform: Optional[str]
    fingerprint: str
    uptime: Optional[int]
    accept: List[str]
    reject: List[str]
    IPv6_accept: List[str]
    IPv6_reject: List[str]
    family: List[str]


class RelayDescriptorParser:
    """
    Parses a given relay descriptor file
    """

    def __init__(self, descriptor_file: str) -> None:
        """
        Initializes the parser

        :param descriptor_file: The absolute path to the descriptor file
        :type descriptor_file: str
        """
        # Public class attributes
        self.relay_entries: List

        # Private class attributes
        self.__logger = logging.getLogger(__name__)
        self.__descriptor_lines: List

        try:
            # Read the file
            with open(descriptor_file, "r") as file:
                self.__descriptor_lines = [line.strip() for line in file.readlines()]

        except FileNotFoundError as exception:
            self.__logger.warning("Given descriptor file doesn't exist: %s", exception)
            raise RelayDescriptorParserFileNotFoundError from exception

        # Parse the descriptor
        self.relay_entries = self.__parse_relay_entries(self.__descriptor_lines)

    @staticmethod
    def __parse_relay_entries(
        descriptor_lines: List,
    ) -> List[RelayDescriptorEntry]:
        """
        Parses relay entries in the server descriptors file

        :param descriptor_lines: Rows of the server descriptors
        :type descriptor_lines: List
        :return: A list of relay entries
        :rtype: List[RelayDescriptorEntry]
        """
        # TODO: Please refactor me into multiple functions
        # pylint: disable=R0912
        # pylint: disable=R0914
        relays = []

        for idx, line in enumerate(descriptor_lines):
            params = []
            # Find relay entries
            if line.startswith("router "):
                # Split the line into separate parameters
                params = line.split(" ")[1:]

                nickname = params[0]
                address = params[1]

                bandwidth_avg = None
                bandwidth_burst = None
                bandwidth_observed = None
                platform = None
                fingerprint = ""
                uptime = None
                accept = []
                reject = []
                IPv6_accept: List[str] = []
                IPv6_reject: List[str] = []
                family: List[str] = []

                i = 1
                # Keep parsing the lines until we hit the next router entry
                while ((idx + i) < len(descriptor_lines)) and (
                    not descriptor_lines[idx + i].startswith("router ")
                ):

                    temp_line = descriptor_lines[idx + i]

                    if temp_line.startswith("bandwidth "):
                        cur_line = temp_line.split(" ")[1:]
                        bandwidth_avg = int(cur_line[0])
                        bandwidth_burst = int(cur_line[1])
                        bandwidth_observed = int(cur_line[2])

                    elif temp_line.startswith("platform "):
                        platform = temp_line.split(" ", 1)[1:][0]

                    elif temp_line.startswith("fingerprint "):
                        fingerprint_parts = temp_line.split(" ")[1:]

                        # __A fingerprint (a HASH_LEN-byte of asn1 encoded public
                        # key, encoded in hex, with a single space after every 4
                        # characters)__
                        for part in fingerprint_parts:
                            fingerprint += str(part)

                    elif temp_line.startswith("uptime "):
                        uptime = int(temp_line.split(" ")[1:][0])

                    elif temp_line.startswith("accept "):
                        accept.append(temp_line.split(" ")[1:][0])

                    elif temp_line.startswith("reject "):
                        reject.append(temp_line.split(" ")[1:][0])

                    elif temp_line.startswith("ipv6-policy accept "):
                        IPv6_accept = IPv6_accept + (temp_line.split(" ")[2:][0]).split(
                            ","
                        )

                    elif temp_line.startswith("ipv6-policy reject "):
                        IPv6_reject = IPv6_reject + (temp_line.split(" ")[2:][0]).split(
                            ","
                        )

                    elif temp_line.startswith("family "):
                        family = family + (temp_line.split(" ", 1)[1:][0]).split(" ")

                    # Switch to the next line
                    i += 1

                # Add relay to the list
                relays.append(
                    RelayDescriptorEntry(
                        nickname=nickname,
                        address=address,
                        bandwidth_avg=bandwidth_avg,
                        bandwidth_burst=bandwidth_burst,
                        bandwidth_observed=bandwidth_observed,
                        platform=platform,
                        fingerprint=fingerprint,
                        uptime=uptime,
                        accept=accept,
                        reject=reject,
                        IPv6_accept=IPv6_accept,
                        IPv6_reject=IPv6_reject,
                        family=family,
                    )
                )

        return relays
