import datetime
import logging
import sys
import os
import time
import tarfile
import requests
import shutil
import datetime
import fnmatch
import tempfile
from pathlib import Path
import stem.descriptor
from typing import List
from dataclasses import dataclass


@dataclass
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

    nickname: str
    identity: str
    digest: str
    publication: datetime
    IP: str
    IPv6: str
    IPv6ORPort: str
    is_exit: bool
    ORPort: int
    DirPort: int
    bandwidth: int
    flags: List
    guard_probability: float = 0.0
    middle_probability: float = 0.0
    exit_probability: float = 0.0
    consensus_weight_fraction: float = 0.0
    captcha_percentage: float = 0.0

    def __post_init__(self):
        self.fingerprint = stem.descriptor.router_status_entry._base64_to_hex(self.identity)


@dataclass
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

    nickname: str
    address: str
    bandwidth_avg: int
    bandwidth_burst: int
    bandwidth_observed: int
    platform: str
    fingerprint: str
    uptime: int
    accept: List
    reject: List
    IPv6_accept: List
    IPv6_reject: List
    family: List


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

        logger = logging.getLogger(__name__)
        logger.debug('Parsing %s', consensus_file)

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

        logger = logging.getLogger(__name__)
        logger.debug('Parsing %s', server_descriptors_file)

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


def get_consensus(consensus_time):
    """
    Finds the consensus document that was published at given date and deletes it

    :param date: the date for valid-after timestamp of the consensus document
    :type date: datetime object

    :returns: parsed consensus
    :rtype: ParseConsensusV3 object
    """

    logger = logging.getLogger(__name__)

    # Try at most 3 times
    for i in range(3):
        try:
            # Get the corresponding consensus
            consensus_file = consensus_date_to_local_file(consensus_time)

            # Parse the consensus file
            consensus = ParseConsensusV3(consensus_file)

            return consensus

        except Exception as err:
            # Remove the file from computer
            remove_consensus_file(consensus_time)

            logger.debug('Couldn\'t parse the consensus for %s: %s' % (consensus_time, err))
            logger.debug('Possibly the file is corrupted, and downloading again')

    # If we are here, it means that we failed
    logger.debug('Cannot access requested consensus, please try again later')

    return None


def consensus_date_to_local_file(date):
    """
    Finds the consensus document that was published at given date

    :param date: the date for valid-after timestamp of the consensus document
    :type date: datetime object

    :returns: absolute path to the consensus document
    :rtype: str
    """

    logger = logging.getLogger(__name__)

    # Create the base path for consensus cache
    consensus_dir = os.path.join(str(Path.home()), 'captchamonitor', 'consensuses')
    if not os.path.exists(consensus_dir):
        os.makedirs(consensus_dir)

    date_str = date.strftime('%Y-%m-%d-%H-%M-%S')

    # Try 3 times maximum
    for i in range(3):
        # Find the requested consensus from the cache
        for file in os.listdir(consensus_dir):
            if fnmatch.fnmatch(file, '*' + date_str + '*'):
                return os.path.join(consensus_dir, file)

        # If we are here, it means that the requested consensus is not cached yet
        logger.debug('Requested consensus is not cached yet, downloading...')
        download_consensus(date, consensus_dir)

    logger.debug('Cannot source the requested consensus, try again')


def download_consensus(date, consensus_dir):
    """
    Downloads the consensus document for the specified date from CollecTor

    :param date: the date for valid-after timestamp of the consensus document
    :type date: datetime object
    :param consensus_dir: the absolute path to the directory where cached consensus files are stored
    :type consensus_dir: str
    """

    logger = logging.getLogger(__name__)

    url_consensuses_recent = 'https://collector.torproject.org/recent/relay-descriptors/consensuses/'
    url_consensuses_archive = 'https://collector.torproject.org/archive/relay-descriptors/consensuses/'

    date_str = date.strftime('%Y-%m-%d-%H-%M-%S')

    # Check for recent consensuses first
    recent_consensuses = requests.get(url_consensuses_recent).text

    if date_str in recent_consensuses:
        base_url = url_consensuses_recent
        file_name = date_str + '-consensus'
        url = base_url + file_name
        file_path = os.path.join(consensus_dir, file_name)

        # Download the consensus file directly to consensus_dir
        open(file_path, 'wb').write(requests.get(url).content)

    else:
        # Create a temporary directory and download the consensus archive
        with tempfile.TemporaryDirectory() as download_dir:
            base_url = url_consensuses_archive
            folder_name = 'consensuses-%s-%s' % (date.strftime('%Y'), date.strftime('%m'))
            archive_name = folder_name + '.tar.xz'
            archive_path = os.path.join(download_dir, archive_name)
            extracted_path = os.path.join(download_dir, folder_name)
            url = base_url + archive_name

            # Download the consensus archive to a temp location
            open(archive_path, 'wb').write(requests.get(url).content)

            # Extract the archive
            with tarfile.open(archive_path) as f:
                f.extractall(download_dir)

            # Recursively move files
            for day_folder in os.listdir(extracted_path):
                for con_file in os.listdir(os.path.join(extracted_path, day_folder)):
                    try:
                        shutil.move(os.path.join(extracted_path,
                                                 day_folder, con_file), consensus_dir)

                    except Exception as err:
                        # We can simply skip already existing files
                        logger.debug(err)


def remove_consensus_file(date):
    """
    Finds the consensus document that was published at given date and deletes it

    :param date: the date for valid-after timestamp of the consensus document
    :type date: datetime object
    """

    logger = logging.getLogger(__name__)

    date_str = date.strftime('%Y-%m-%d-%H-%M-%S')

    # Create the base path for consensus cache
    consensus_dir = os.path.join(str(Path.home()), 'captchamonitor', 'consensuses')
    if os.path.exists(consensus_dir):
        file = os.path.join(consensus_dir, date_str + '-consensus')
        try:
            os.remove(file)
        except FileNotFoundError:
            pass
        logger.debug('Removed the consensus file %s', file)
