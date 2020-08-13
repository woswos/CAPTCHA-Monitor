import datetime
import logging
import stem.descriptor


class RelayEntry:
    """
    Stores a v3 type relay entry
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
    :type IP: str
    :param is_exit: indicates whether this relay allows exitting
    :type is_exit: bool
    :param ORPort: relay's current OR port
    :type ORPort: str, optional
    :param DirPort: relay's current directory port
    :type DirPort: str, optional
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

    :returns: RelayEntry object
    """

    def __init__(self, nickname, identity, digest, publication, IP, is_exit,
                 ORPort=None, DirPort=None, bandwidth=None, flags=None,
                 guard_probability=None, middle_probability=None, exit_probability=None,
                 consensus_weight_fraction=None):
        self.logger = logging.getLogger(__name__)
        self.nickname = nickname
        self.identity = identity
        self.fingerprint = stem.descriptor.router_status_entry._base64_to_hex(identity)
        self.digest = digest
        self.publication = publication
        self.IP = IP
        self.is_exit = is_exit
        self.ORPort = ORPort
        self.DirPortP = DirPort
        self.bandwidth = bandwidth
        self.flags = flags
        self.guard_probability = guard_probability
        self.middle_probability = middle_probability
        self.exit_probability = exit_probability
        self.consensus_weight_fraction = consensus_weight_fraction


class ParseConsensus:
    """
    Parses a given consensus file

    :param consensus_file: the absolute path to the consensus file
    :type consensus_file: str

    :returns: parsed consensus object
    """

    def __init__(self, consensus_file):
        """
        Constructor method
        """

        # Read the file
        file = open(consensus_file, 'r')
        lines = file.readlines()
        lines = [x.strip() for x in lines]
        file.close()

        # Parse the consensus
        self.valid_after = self.parse_valid_after(lines)
        self.fresh_until = self.parse_fresh_until(lines)
        self.bandwidth_weights = self.parse_bandwidth_weights(lines)
        self.relay_entries = self.parse_relay_entries(lines)
        self.relay_entries = self.calculate_path_selection_probabilities(self.relay_entries,
                                                                         self.bandwidth_weights)

    def calculate_path_selection_probabilities(self, relay_entries, bandwidth_weights):
        """
        Calculates guard, middle, and exit probabilities for relays

        Adapted from the function called calculatePathSelectionProbabilities() in
        https://gitweb.torproject.org/onionoo.git/tree/src/main/java/org/torproject/metrics/onionoo/updater/NodeDetailsStatusUpdater.java#n597

        :param relay_entries: list of relay entries
        :type relay_entries: list
        :param bandwidth_weights: a dictionary of bandwidth weights parsed from consensus
        :type bandwidth_weights: dict

        :returns: list of relay entry objects
        :rtype: list
        """

        wgg = bandwidth_weights['Wgg'] / 10000.0
        wgd = bandwidth_weights['Wgd'] / 10000.0
        wmg = bandwidth_weights['Wmg'] / 10000.0
        wmm = bandwidth_weights['Wmm'] / 10000.0
        wme = bandwidth_weights['Wme'] / 10000.0
        wmd = bandwidth_weights['Wmd'] / 10000.0
        wee = bandwidth_weights['Wee'] / 10000.0
        wed = bandwidth_weights['Wed'] / 10000.0

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
            if 'Running' in relay.flags:
                running_relays.append(relay)

        for relay in running_relays:
            isExit = relay.flags is not None and 'Exit' in relay.flags and 'BadExit' not in relay.flags
            isGuard = relay.flags is not None and 'Guard' in relay.flags
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

    def parse_relay_entries(self, consensus_lines):
        """
        Parses relay entries in the consensus

        :param consensus_lines: rows of the consensus
        :type consensus_lines: list

        :returns: a dictionary of weight values
        :rtype: list
        """

        relays = []

        for idx, line in enumerate(consensus_lines):
            params = []
            # Find relay entries
            if line.startswith('r '):
                # Split the line into seperate parameters
                params = line.split(' ')[1:]

                # See https://gitweb.torproject.org/torspec.git/tree/dir-spec.txt#n2337
                #   for the exact order of the params
                nickname = params[0]
                identity = params[1]
                digest = params[2]
                publication = datetime.datetime.strptime(params[3] + ' ' + params[4],
                                                         '%Y-%m-%d %H:%M:%S')
                IP = params[5]
                ORPort = params[6]
                DirPort = params[7]

                # Parse the flags and bandwidth for this relay
                flags = []
                bandwidth = None
                is_exit = False
                for i in range(1, 10):
                    # Find flags
                    temp_line = consensus_lines[idx+i]
                    if temp_line.startswith('s '):
                        flags = temp_line.split(' ')[1:]
                        is_exit = 'Exit' in flags and 'BadExit' not in flags

                    # Find bandwidth
                    elif temp_line.startswith('w '):
                        bandwidth = float(temp_line.split(' ')[1].split('=')[1])

                        # Stop searching since bandwidth comes the last
                        break

                # Add relay to the list
                relays.append(RelayEntry(nickname, identity, digest,
                                         publication, IP, is_exit,
                                         ORPort, DirPort,
                                         bandwidth, flags))
        return relays

    def parse_bandwidth_weights(self, consensus_lines):
        """
        Parses the fresh until date from consensus

        :param consensus_lines: rows of the consensus
        :type consensus_lines: list

        :returns: a dictionary of weight values
        :rtype: dict
        """

        weights = []
        for line in consensus_lines[::-1]:
            if line.startswith('bandwidth-weights'):
                weights = line.split(' ')[1:]

        weights_dict = {}
        for weight in weights:
            values = weight.split('=')
            weights_dict.update({values[0]: float(values[1])})

        return weights_dict

    def parse_valid_after(self, consensus_lines):
        """
        Parses the valid after date from consensus

        :param consensus_lines: rows of the consensus
        :type consensus_lines: list

        :returns: "valid-after" timestamp
        :rtype: datetime object
        """

        for line in consensus_lines:
            if line.startswith('valid-after'):
                date = line.split(' ', 1)[1]
                return datetime.datetime.strptime(date, '%Y-%m-%d %H:%M:%S')

    def parse_fresh_until(self, consensus_lines):
        """
        Parses the fresh until date from consensus

        :param consensus_lines: rows of the consensus
        :type consensus_lines: list

        :returns: "fresh-until" timestamp
        :rtype: datetime object
        """
        
        for line in consensus_lines:
            if line.startswith('fresh-until'):
                date = line.split(' ', 1)[1]
                return datetime.datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
