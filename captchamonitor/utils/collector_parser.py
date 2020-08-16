import datetime
import logging
import stem.descriptor


class ConsensusRouterEntry:
    """
    Stores a v3 type router/relay/node entry
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

    :returns: ConsensusRouterEntry object
    """

    def __init__(self, nickname, identity, digest, publication, IP, is_exit,
                 IPv6=None, IPv6ORPort=None,
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
        self.IPv6 = IPv6
        self.IPv6ORPort = IPv6ORPort
        self.is_exit = is_exit
        self.ORPort = ORPort
        self.DirPortP = DirPort
        self.bandwidth = bandwidth
        self.flags = flags
        self.guard_probability = guard_probability
        self.middle_probability = middle_probability
        self.exit_probability = exit_probability
        self.consensus_weight_fraction = consensus_weight_fraction
        self.captcha_percentage = 0


class ServerDescEntry:
    """
    Stores a server descriptor entry
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

    :returns: ServerDescEntry object
    """

    def __init__(self, nickname, address, fingerprint, bandwidth_avg=None, bandwidth_burst=None,
                 bandwidth_observed=None, platform=None, uptime=None, family=None,
                 accept=None, reject=None, IPv6_accept=None, IPv6_reject=None):
        self.nickname = nickname
        self.address = address
        self.bandwidth_avg = bandwidth_avg
        self.bandwidth_burst = bandwidth_burst
        self.bandwidth_observed = bandwidth_observed
        self.platform = platform
        self.fingerprint = fingerprint
        self.uptime = uptime
        self.accept = accept
        self.reject = reject
        self.IPv6_accept = IPv6_accept
        self.IPv6_reject = IPv6_reject
        self.family = family


class ParseConsensusV3:
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

        :returns: a list of ConsensusRouterEntry objects
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
                ORPort = int(params[6])
                DirPort = int(params[7])

                # Parse the flags and bandwidth for this relay
                flags = []
                bandwidth = None
                is_exit = False
                IPv6 = None
                IPv6ORPort = None
                for i in range(1, 10):

                    temp_line = consensus_lines[idx+i]

                    if temp_line.startswith('a '):
                        cur_line = temp_line.split(' ')[1:][0].rsplit(':', 1)
                        IPv6 = cur_line[0]
                        IPv6ORPort = cur_line[1]

                    elif temp_line.startswith('s '):
                        flags = temp_line.split(' ')[1:]
                        is_exit = 'Exit' in flags and 'BadExit' not in flags

                    elif temp_line.startswith('w '):
                        bandwidth = float(temp_line.split(' ')[1].split('=')[1])

                        # Stop searching since bandwidth comes the last
                        break

                # Add relay to the list
                relays.append(ConsensusRouterEntry(nickname=nickname, identity=identity, digest=digest,
                                                   publication=publication, IP=IP, is_exit=is_exit,
                                                   IPv6=IPv6, IPv6ORPort=IPv6ORPort,
                                                   ORPort=ORPort, DirPort=DirPort,
                                                   bandwidth=bandwidth, flags=flags))
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
            if line.startswith('bandwidth-weights '):
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


class ParseServerDesc:
    """
    Parses a given server descriptors file

    :param server_descriptors_file: the absolute path to the server descriptors file
    :type server_descriptors_file: str

    :returns: parsed ParseServerDesc object
    """

    def __init__(self, server_descriptors_file):
        """
        Constructor method
        """

        # Read the file
        file = open(server_descriptors_file, 'r')
        lines = file.readlines()
        lines = [x.strip() for x in lines]
        file.close()

        # Parse the server descriptors file
        self.relay_entries = self.parse_relay_entries(lines)

    def parse_relay_entries(self, server_desc_lines):
        """
        Parses relay entries in the server descriptors file

        :param server_desc_lines: rows of the server descriptors
        :type server_desc_lines: list

        :returns: a list of relay entries
        :rtype: list
        """

        relays = []

        for idx, line in enumerate(server_desc_lines):
            params = []
            # Find relay entries
            if line.startswith('router '):
                # Split the line into seperate parameters
                params = line.split(' ')[1:]

                nickname = params[0]
                address = params[1]

                bandwidth_avg = None
                bandwidth_burst = None
                bandwidth_observed = None
                platform = None
                fingerprint = ''
                uptime = None
                accept = []
                reject = []
                IPv6_accept = []
                IPv6_reject = []
                family = []

                i = 1
                # Keep parsing the lines until we hit the next router entry
                while ((idx+i) < len(server_desc_lines)) and (not server_desc_lines[idx+i].startswith('router ')):

                    temp_line = server_desc_lines[idx+i]

                    if temp_line.startswith('bandwidth '):
                        cur_line = temp_line.split(' ')[1:]
                        bandwidth_avg = int(cur_line[0])
                        bandwidth_burst = int(cur_line[1])
                        bandwidth_observed = int(cur_line[2])

                    elif temp_line.startswith('platform '):
                        platform = temp_line.split(' ', 1)[1:][0]

                    elif temp_line.startswith('fingerprint '):
                        fingerprint_parts = temp_line.split(' ')[1:]

                        # __A fingerprint (a HASH_LEN-byte of asn1 encoded public
                        # key, encoded in hex, with a single space after every 4
                        # characters)__
                        for part in fingerprint_parts:
                            fingerprint += str(part)

                    elif temp_line.startswith('uptime '):
                        uptime = int(temp_line.split(' ')[1:][0])

                    elif temp_line.startswith('accept '):
                        accept.append(temp_line.split(' ')[1:][0])

                    elif temp_line.startswith('reject '):
                        reject.append(temp_line.split(' ')[1:][0])

                    elif temp_line.startswith('ipv6-policy accept '):
                        IPv6_accept = IPv6_accept + (temp_line.split(' ')[2:][0]).split(',')

                    elif temp_line.startswith('ipv6-policy reject '):
                        IPv6_reject = IPv6_reject + (temp_line.split(' ')[2:][0]).split(',')

                    elif temp_line.startswith('family '):
                        family = family + (temp_line.split(' ', 1)[1:][0]).split(' ')

                    # Switch to the next line
                    i += 1

                # Add relay to the list
                relays.append(ServerDescEntry(nickname=nickname, address=address,
                                              bandwidth_avg=bandwidth_avg,
                                              bandwidth_burst=bandwidth_burst,
                                              bandwidth_observed=bandwidth_observed,
                                              platform=platform, fingerprint=fingerprint,
                                              uptime=uptime,
                                              accept=accept, reject=reject,
                                              IPv6_accept=IPv6_accept, IPv6_reject=IPv6_reject,
                                              family=family))

        return relays
