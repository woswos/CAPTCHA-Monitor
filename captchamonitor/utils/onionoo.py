import json
import requests
import logging
from typing import List
from dataclasses import dataclass


@dataclass
class OnionooRelayDetails:
    """
    Stores details gathered from Onionoo details file

    :param fingerprint: Onionoo's fingerprint field
    :type fingerprint: str
    :param nickname: Onionoo's nickname field
    :type nickname: str
    :param exit_policy_summary: Onionoo's exit_policy_summary field
    :type exit_policy_summary: List
    :param exit_policy_v6_summary: Onionoo's exit_policy_v6_summary field
    :type exit_policy_v6_summary: List
    :param is_IPv4_exit: indicates whether relay allows IPv4 exitting
    :type is_IPv4_exit: bool
    :param is_IPv6_exit: indicates whether relay allows IPv6 exitting
    :type is_IPv6_exit: bool
    :param first_seen: Onionoo's first_seen field
    :type first_seen: str
    :param last_seen: Onionoo's last_seen field
    :type last_seen: str
    :param country: Onionoo's country field
    :type country: str
    :param country_name: Onionoo's country_name field
    :type country_name: str
    :param asn: Onionoo's as field
    :type asn: str
    :param asn_name: Onionoo's as_name field
    :type asn_name: str
    :param version: Onionoo's version field
    :type version: str
    :param platform: Onionoo's platform field
    :type platform: str

    :returns: OnionooRelayDetails object
    """

    fingerprint: str
    nickname: str
    exit_policy_summary_accept: List
    exit_policy_summary_reject: List
    exit_policy_v6_summary_accept: List
    exit_policy_v6_summary_reject: List
    is_IPv4_exit: bool
    is_IPv6_exit: bool
    first_seen: str
    last_seen: str
    country: str
    country_name: str
    asn: str
    as_name: str
    version: str
    platform: str


def get_onionoo_relay_details(fingerprint):
    """
    Get the details document from Onionoo for a given relay fingerprint
    See https://metrics.torproject.org/onionoo.html#details for more details

    :param fingerprint: relay fingerprint consisting of 40 upper-case hexadecimal characters
    :type fingerprint: str

    :returns: OnionooRelayDetails object
    """

    logger = logging.getLogger(__name__)
    logger.debug('Getting Onionoo details document for %s', fingerprint)

    url = 'https://onionoo.torproject.org/details?fields=fingerprint,nickname,exit_policy_summary,exit_policy_v6_summary,first_seen,last_seen,country,country_name,as,as_name,version,platform&lookup=' + fingerprint
    result = requests.get(url).text
    result_json = json.loads(result)

    try:
        relay_of_interest = result_json['relays'][0]

    except IndexError:
        logger.debug('Upps, this relay does not exist on Onionoo yet', fingerprint)
        return None

    except Exception as err:
        logger.debug('Could not connecto Onionoo: %s' % err)
        return None

    try:
        exit_policy_summary_accept = relay_of_interest.get('exit_policy_summary')['accept']
    except:
        exit_policy_summary_accept = []

    try:
        exit_policy_summary_reject = relay_of_interest.get('exit_policy_summary')['reject']
    except:
        exit_policy_summary_reject = []

    try:
        exit_policy_v6_summary_accept = relay_of_interest.get(
            'exit_policy_v6_summary')['accept']
    except:
        exit_policy_v6_summary_accept = []

    try:
        exit_policy_v6_summary_reject = relay_of_interest.get(
            'exit_policy_v6_summary')['reject']
    except:
        exit_policy_v6_summary_reject = []

    http_port = 80
    https_port = 443

    is_IPv4_http_exit = is_exitting_allowed(http_port,
                                            exit_policy_summary_accept,
                                            exit_policy_summary_reject)
    is_IPv4_https_exit = is_exitting_allowed(https_port,
                                             exit_policy_summary_accept,
                                             exit_policy_summary_reject)
    is_IPv6_http_exit = is_exitting_allowed(http_port,
                                            exit_policy_v6_summary_accept,
                                            exit_policy_v6_summary_reject)
    is_IPv6_https_exit = is_exitting_allowed(https_port,
                                             exit_policy_v6_summary_accept,
                                             exit_policy_v6_summary_reject)

    # See https://gitweb.torproject.org/torspec.git/tree/dir-spec.txt#n2632
    is_IPv4_exit = is_IPv4_https_exit and is_IPv4_http_exit
    is_IPv6_exit = is_IPv6_https_exit and is_IPv6_http_exit

    relay = OnionooRelayDetails(fingerprint=fingerprint,
                                exit_policy_summary_accept=exit_policy_summary_accept,
                                exit_policy_summary_reject=exit_policy_summary_reject,
                                exit_policy_v6_summary_accept=exit_policy_v6_summary_accept,
                                exit_policy_v6_summary_reject=exit_policy_v6_summary_reject,
                                is_IPv4_exit=is_IPv4_exit,
                                is_IPv6_exit=is_IPv6_exit,
                                nickname=relay_of_interest.get('nickname'),
                                first_seen=relay_of_interest.get('first_seen'),
                                last_seen=relay_of_interest.get('last_seen'),
                                country=relay_of_interest.get('country'),
                                country_name=relay_of_interest.get('country_name'),
                                asn=relay_of_interest.get('as'),
                                as_name=relay_of_interest.get('as_name'),
                                version=relay_of_interest.get('version'),
                                platform=relay_of_interest.get('platform'))

    return relay


def is_exitting_allowed(exit_port, accept_list, reject_list):
    """
    Determines if a relay allows exitting by using the accept&reject list summary from Onionoo
    Either accept_list or reject_list needs to be an empty list as specified by the Onionoo API

    :param exit_port: the exit port that will be used for determining the exitting capability
    :type exit_port: int
    :param accept_list: exit_policy_summary gathered from onionoo
    :type accept_list: list
    :param reject_list: exit_policy_summary gathered from onionoo
    :type reject_list: list

    :returns: if given exit_port is allowed based on accept&reject list
    :rtype: bool
    """

    exit_port = int(exit_port)

    if accept_list != []:
        for port in accept_list:
            if ('-' not in str(port)) and (int(port) == exit_port):
                return True

            elif ('-' in str(port)):
                low = int(port.split('-')[0])
                high = int(port.split('-')[1])

                if(low <= exit_port) and (high >= exit_port):
                    return True

        return False

    if reject_list != []:
        for port in reject_list:
            if ('-' not in str(port)) and (int(port) == exit_port):
                return False

            elif ('-' in str(port)):
                low = int(port.split('-')[0])
                high = int(port.split('-')[1])

                if(low <= exit_port) and (high >= exit_port):
                    return False

        return True

    return False
