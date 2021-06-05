import logging
from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass

import stem.descriptor

from captchamonitor.utils.exceptions import (
    ConsensusParserInvalidDocument,
    ConsensusParserFileNotFoundError,
)


@dataclass
class ConsensusRelayEntry:
    """
    Stores a router/relay/node entry
    See https://gitweb.torproject.org/torspec.git/tree/dir-spec.txt#n2337 for
    exact details

    :param nickname: OR's nickname
    :type nickname: str
    :param identity: hash of relay's identity key, encoded in base64, with trailing equals sign(s) removed
    :type identity: str
    :param fingerprint: HEX version of the relay's identity key
    :type fingerprint: str
    :param digest:  hash of relay's most recent descriptor as signed (that is, not including the signature) by the RSA identity key, encoded in base64
    :type digest: str
    :param publication: publication time of relay's most recent descriptor, in the form YYYY-MM-DD HH:MM:SS, in UTC
    :type publication: datetime object
    :param IP: relay's current IPv4 address
    :type IP: str, optional
    :param IPv6: relay's current IPv6 address
    :type IPv6: str, optional
    :param IPv6ORPort: relay's current IPv6 OR port
    :type IPv6ORPort: str, optional
    :param is_exit: indicates whether this relay allows exitting
    :type is_exit: bool
    :param ORPort: relay's current OR port
    :type ORPort: int, optional
    :param DirPort: relay's current directory port
    :type DirPort: int, optional
    :param bandwidth: an estimate of the bandwidth of this relay
    :type bandwidth: float, optional
    :param flags: relay's flags
    :type flags: list, optional
    :param guard_probability: relay's guard probability
    :type guard_probability: float, optional
    :param middle_probability: relay's middle probability
    :type middle_probability: float, optional
    :param exit_probability: relay's exit probability
    :type exit_probability: float, optional
    :param consensus_weight_fraction: relay's consensus weight fraction
    :type consensus_weight_fraction: float, optional

    :returns: ConsensusRelayEntry object
    """

    nickname: str
    identity: str
    digest: str
    publication: datetime
    IP: str
    IPv6: Optional[str]
    IPv6ORPort: Optional[str]
    is_exit: bool
    ORPort: int
    DirPort: int
    bandwidth: float
    flags: List
    fingerprint: Optional[str] = None
    guard_probability: float = 0.0
    middle_probability: float = 0.0
    exit_probability: float = 0.0
    consensus_weight_fraction: float = 0.0
    captcha_percentage: float = 0.0

    def __post_init__(self) -> None:
        # pylint: disable=W0212
        self.fingerprint = stem.descriptor.router_status_entry._base64_to_hex(
            self.identity
        )


class ConsensusV3Parser:
    """
    Parses a given V3 consensus file
    """

    def __init__(self, consensus_file: str) -> None:
        """
        Initializes the parser

        :param consensus_file: The absolute path to the consensus file
        :type consensus_file: str
        :raises ConsensusParserFileNotFoundError: If given file does not exist
        """
        # Public class attributes
        self.valid_after: datetime
        self.fresh_until: datetime
        self.bandwidth_weights: Dict
        self.relay_entries: List[ConsensusRelayEntry]

        # Private class attributes
        self.__logger = logging.getLogger(__name__)
        self.__consensus_lines: List

        try:
            # Read the file
            with open(consensus_file, "r") as file:
                self.__consensus_lines = [line.strip() for line in file.readlines()]

        except FileNotFoundError as exception:
            self.__logger.warning("Given consensus file doesn't exist: %s", exception)
            raise ConsensusParserFileNotFoundError from exception

        # Parse the consensus
        self.valid_after = self.__parse_valid_after(self.__consensus_lines)
        self.fresh_until = self.__parse_fresh_until(self.__consensus_lines)
        self.bandwidth_weights = self.__parse_bandwidth_weights(self.__consensus_lines)
        self.relay_entries = self.__parse_relay_entries(self.__consensus_lines)
        self.relay_entries = self.__calculate_path_selection_probabilities(
            self.relay_entries, self.bandwidth_weights
        )

    @staticmethod
    def __parse_valid_after(consensus_lines: List) -> datetime:
        """
        Parses the valid after date from consensus

        :param consensus_lines: Rows of the consensus
        :type consensus_lines: List
        :raises ConsensusParserInvalidDocument: If given file is invalid
        :return: "valid-after" timestamp
        :rtype: datetime
        """
        for line in consensus_lines:
            if line.startswith("valid-after"):
                date = line.split(" ", 1)[1]
                return datetime.strptime(date, "%Y-%m-%d %H:%M:%S")

        raise ConsensusParserInvalidDocument

    @staticmethod
    def __parse_fresh_until(consensus_lines: List) -> datetime:
        """
        Parses the fresh until date from consensus

        :param consensus_lines: Rows of the consensus
        :type consensus_lines: List
        :raises ConsensusParserInvalidDocument: If given file is invalid
        :return: "fresh-until" timestamp
        :rtype: datetime
        """
        for line in consensus_lines:
            if line.startswith("fresh-until"):
                date = line.split(" ", 1)[1]
                return datetime.strptime(date, "%Y-%m-%d %H:%M:%S")

        raise ConsensusParserInvalidDocument

    @staticmethod
    def __parse_bandwidth_weights(consensus_lines: List) -> Dict:
        """
        Parses the fresh until date from consensus

        :param consensus_lines: Rows of the consensus
        :type consensus_lines: List
        :return: A dictionary of weight values
        :rtype: Dict
        """
        weights = []
        for line in consensus_lines[::-1]:
            if line.startswith("bandwidth-weights "):
                weights = line.split(" ")[1:]

        weights_dict = {}
        for weight in weights:
            values = weight.split("=")
            weights_dict.update({values[0]: float(values[1])})

        return weights_dict

    @staticmethod
    def __parse_relay_entries(
        consensus_lines: List,
    ) -> List[ConsensusRelayEntry]:
        """
        Parses relay entries in the consensus

        :param consensus_lines: Rows of the consensus
        :type consensus_lines: List
        :return: A list of ConsensusRelayEntry objects
        :rtype: List[ConsensusRelayEntry]
        """
        # TODO: Please refactor me into smaller functions
        # pylint: disable=R0914
        relays = []

        for idx, line in enumerate(consensus_lines):
            params = []
            # Find relay entries
            if line.startswith("r "):
                # Split the line into separate parameters
                params = line.split(" ")[1:]

                # See https://gitweb.torproject.org/torspec.git/tree/dir-spec.txt#n2337
                #   for the exact order of the params
                nickname = params[0]
                identity = params[1]
                digest = params[2]
                publication = datetime.strptime(
                    params[3] + " " + params[4], "%Y-%m-%d %H:%M:%S"
                )
                IP = params[5]
                ORPort = int(params[6])
                DirPort = int(params[7])

                # Parse the flags and bandwidth for this relay
                flags = []
                bandwidth = 0.0
                is_exit = False
                IPv6 = None
                IPv6ORPort = None
                for i in range(1, 10):

                    temp_line = consensus_lines[idx + i]

                    if temp_line.startswith("a "):
                        cur_line = temp_line.split(" ")[1:][0].rsplit(":", 1)
                        IPv6 = cur_line[0]
                        IPv6ORPort = cur_line[1]

                    elif temp_line.startswith("s "):
                        flags = temp_line.split(" ")[1:]
                        is_exit = "Exit" in flags and "BadExit" not in flags

                    elif temp_line.startswith("w "):
                        bandwidth = float(temp_line.split(" ")[1].split("=")[1])

                        # Stop searching since bandwidth comes the last
                        break

                # Add relay to the list
                relays.append(
                    ConsensusRelayEntry(
                        nickname=nickname,
                        identity=identity,
                        digest=digest,
                        publication=publication,
                        IP=IP,
                        is_exit=is_exit,
                        IPv6=IPv6,
                        IPv6ORPort=IPv6ORPort,
                        ORPort=ORPort,
                        DirPort=DirPort,
                        bandwidth=bandwidth,
                        flags=flags,
                    )
                )
        return relays

    @staticmethod
    def __calculate_path_selection_probabilities(
        relay_entries: List[ConsensusRelayEntry],
        bandwidth_weights: Dict,
    ) -> List[ConsensusRelayEntry]:
        """
        Calculates guard, middle, and exit probabilities for relays

        Adapted from the function called calculatePathSelectionProbabilities() in
        https://gitweb.torproject.org/onionoo.git/tree/src/main/java/org/torproject/metrics/onionoo/updater/NodeDetailsStatusUpdater.java#n597


        :param relay_entries: List of relay entries
        :type relay_entries: List[ConsensusRelayEntry]
        :param bandwidth_weights: A dictionary of bandwidth weights parsed from consensus
        :type bandwidth_weights: Dict
        :return: List of relay entry objects
        :rtype: List[ConsensusRelayEntry]
        """
        # TODO: Please refactor me into smaller functions
        # pylint: disable=R0914
        # pylint: disable=R0915
        wgg = bandwidth_weights["Wgg"] / 10000.0
        wgd = bandwidth_weights["Wgd"] / 10000.0
        wmg = bandwidth_weights["Wmg"] / 10000.0
        wmm = bandwidth_weights["Wmm"] / 10000.0
        wme = bandwidth_weights["Wme"] / 10000.0
        wmd = bandwidth_weights["Wmd"] / 10000.0
        wee = bandwidth_weights["Wee"] / 10000.0
        wed = bandwidth_weights["Wed"] / 10000.0

        consensusWeights = {}
        guardWeights = {}
        middleWeights = {}
        exitWeights = {}

        totalConsensusWeight = 0.0
        totalGuardWeight = 0.0
        totalMiddleWeight = 0.0
        totalExitWeight = 0.0

        running_relays = []
        for relay in relay_entries:
            if "Running" in relay.flags:
                running_relays.append(relay)

        for relay in running_relays:
            isExit = (
                relay.flags is not None
                and "Exit" in relay.flags
                and "BadExit" not in relay.flags
            )
            isGuard = relay.flags is not None and "Guard" in relay.flags
            consensusWeight = float(relay.bandwidth)
            consensusWeights.update({relay.fingerprint: consensusWeight})
            totalConsensusWeight += consensusWeight

            guardWeight = consensusWeight
            middleWeight = consensusWeight
            exitWeight = consensusWeight

            if isGuard and isExit:
                guardWeight *= wgd
                middleWeight *= wmd
                exitWeight *= wed
            elif isGuard:
                guardWeight *= wgg
                middleWeight *= wmg
                exitWeight = 0.0
            elif isExit:
                guardWeight = 0.0
                middleWeight *= wme
                exitWeight *= wee
            else:
                guardWeight = 0.0
                middleWeight *= wmm
                exitWeight = 0.0

            guardWeights.update({relay.fingerprint: guardWeight})
            middleWeights.update({relay.fingerprint: middleWeight})
            exitWeights.update({relay.fingerprint: exitWeight})

            totalGuardWeight += guardWeight
            totalMiddleWeight += middleWeight
            totalExitWeight += exitWeight

        for relay in relay_entries:
            fingerprint = relay.fingerprint

            if fingerprint in consensusWeights:
                fraction = float(consensusWeights[fingerprint] / totalConsensusWeight)
                relay.consensus_weight_fraction = fraction

            if fingerprint in guardWeights:
                probability = float(guardWeights[fingerprint] / totalGuardWeight)
                relay.guard_probability = probability

            if fingerprint in middleWeights:
                probability = float(middleWeights[fingerprint] / totalMiddleWeight)
                relay.middle_probability = probability

            if fingerprint in exitWeights:
                probability = float(exitWeights[fingerprint] / totalExitWeight)
                relay.exit_probability = probability

        return relay_entries
