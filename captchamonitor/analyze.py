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
import operator
from pathlib import Path
from random import randint
from threading import Timer
from captchamonitor.utils.collector import get_consensus
from captchamonitor.utils.results import Results
from captchamonitor.utils.relays import Relays
from captchamonitor.utils.urls import Urls
from captchamonitor.utils.digests import Digests
from typing import List, Callable
from dataclasses import dataclass, field
from numpy import histogram, digitize, random, array, mean
from scipy.stats import sem, t
import json


def analyze(args):
    """

    """

    logger = logging.getLogger(__name__)

    if args.verbose:
        logging.getLogger('captchamonitor').setLevel(logging.DEBUG)
        global verbose
        verbose = True

    try:
        logger.info('Started running CAPTCHA Monitor Analyze')

        logger.info('Setting up the tasks...')

        tasks = []
        hour_multiplier = 60*24
        tasks.append(RepeatingTimer(args.process_captcha_rates * hour_multiplier,
                                    process_captcha_rates))

        for task in tasks:
            task.start()

        logger.debug('Done with the tasks, started looping...')

        while True:
            time.sleep(1)

    except Exception as err:
        logging.error(err, exc_info=True)

    except (KeyboardInterrupt, SystemExit):
        logger.info('Stopping CAPTCHA Monitor Analyze...')

    finally:
        logger.debug('Stopping the timed tasks...')
        # Stop the created tasks
        for task in tasks:
            task.cancel()

        logger.debug('Completely exitting...')
        sys.exit()


def process_captcha_rates():
    """

    """

    graphs = [Graph(bin_by_key='relay_exit_probability',
                    measurement_filter=filter_by_nothing,
                    measurement_filter_args=[],
                    create_unique_subbins=True,
                    weighted=False)]

    results = calculate_captcha_rates(graphs=graphs, depth=1)

    digests = Digests()

    for date_time in results:
        for graph in results[date_time]:
            for captcha_rate in results[date_time][graph]:
                data = {'timestamp': captcha_rate.timestamp,
                        'binned_by': captcha_rate.binned_by,
                        'bin_key': captcha_rate.bin_key,
                        'measurement_filter': captcha_rate.measurement_filter,
                        'measurement_filter_args': json.dumps(captcha_rate.measurement_filter_args),
                        'weighted': captcha_rate.weighted,
                        'sample_size': captcha_rate.sample_size,
                        'captcha_rate': captcha_rate.rate,
                        'confidence_interval': captcha_rate.conf_inter,
                        'confidence_interval_mean': captcha_rate.conf_inter_mean,
                        'confidence_interval_lower_bound': captcha_rate.conf_inter_lower_bound,
                        'confidence_interval_upper_bound': captcha_rate.conf_inter_upper_bound
                        }
                digests.insert_digest(data)


def calculate_captcha_rates(graphs, depth=1, timedelta_hours=24):
    """
    Calculates the CAPTCHA rates as described in
    https://gitlab.torproject.org/woswos/CAPTCHA-Monitor/-/wikis/Dashboard-Graphs

    :param length: the number of consensuses to process
    :type length: int
    """

    logger = logging.getLogger(__name__)

    if len(graphs) == 0:
        logger.debug('No graphs were provided')
        return None

    # Database originally returns a list of dictionaries where each dictionary
    #   is a row of data. However, we need to index the results based on the
    #   relay address. So, this little for loop makes that conversion
    db_relays_list = Relays().get_relays()
    db_relays_dict = {}
    for relay in db_relays_list:
        # TODO - replace "address" with fingerprint once measurements are indexed by fingerprint
        db_relays_dict.update({relay['address']: relay})

    # Get urls and index them by the "url" field
    db_urls_list = Urls().get_urls()
    db_urls_dict = {}
    for url in db_urls_list:
        db_urls_dict.update({url['url']: url})

    # Get current UTC time and round down to the nearest hour
    now = datetime.datetime.utcnow().replace(second=0, microsecond=0, minute=0)

    # Get this time yesterday
    yesterday = now - datetime.timedelta(hours=timedelta_hours)

    # Iterate over each consensus
    results = {}
    for i in range(depth):
        # Calculate "valid-after" datetime for consensus
        consensus_time = yesterday - datetime.timedelta(hours=i)

        # Get the consensus for the given "valid-after" datetime
        consensus = get_consensus(consensus_time)

        # Calculate the CAPTCHA rates
        captcha_rates = calculate_captcha_rates_per_consensus(graphs,
                                                              consensus,
                                                              db_relays_dict,
                                                              db_urls_dict)
        # Save the results
        results.update({consensus_time: captcha_rates})

    return results


def calculate_captcha_rates_per_consensus(graphs, consensus, db_relays_dict, db_urls_dict, bootstrap_sample_n=20000, confidence=0.95):
    """

    """

    logger = logging.getLogger(__name__)

    consensus_time = consensus.valid_after

    # Index consensus relays by IP and only add exit relays
    consensus_relays_dict = {}
    for relay in consensus.relay_entries:
        if relay.is_exit:
            # TODO - replace "IP" with fingerprint once measurements are indexed by fingerprint
            consensus_relays_dict.update({relay.IP: relay})

    ############################################################################

    # Get measurements that were completed during the given consensus's valid period
    db_measurements = Results().get_results(after=consensus_time,
                                            before=(consensus_time +
                                                    datetime.timedelta(hours=1)))

    if len(db_measurements) == 0:
        logger.debug('There are no measurements to analyze')
        return None

    ############################################################################

    # Create a new Measurement object for each measurement. It essentially
    #   INNER JOINs the "results" table and the "relays" table but I decided
    #   to do it here manually for performance reasons
    measurements = []
    for measurement in db_measurements:
        # TODO - replace "exit_node" with fingerprint once measurements are indexed by fingerprint
        try:
            # Get the details of the relay from consensus
            consensus_relay = consensus_relays_dict[measurement['exit_node']]

        except KeyError:
            # Skip measurements that were somehow completed with relay not found in consensus
            logger.debug('The requested exit relay isn\'t in consensus, skipping this measurement')
            continue

        try:
            # Get details of the url from database
            db_url = db_urls_dict[measurement['url']]

        except KeyError:
            # Skip measurements that were somehow completed with a url that is not in the database
            logger.debug('This URL isn\'t in the database, skipping this measurement')
            continue

        try:
            # Get the details of the relay from database
            # TODO - learn how to deal with measurement that do not have exit_node (aka non Tor experiments)
            db_relay = db_relays_dict[measurement['exit_node']]

        except KeyError:
            # This makes sure that the relays that are both on consensus and database
            #   are added
            logger.debug('This relay doesn\'t exist in the database yet, skipping this measurement')
            continue

        first_seen = datetime.datetime.strptime(db_relay['first_seen'], '%Y-%m-%d %H:%M:%S')

        # Now we have a measurement and everything related to it in a single object
        measurements.append(Measurement(method=measurement['method'],
                                        is_captcha_found=measurement['is_captcha_found'],
                                        is_data_modified=bool(measurement['is_data_modified']),
                                        exit_node=measurement['exit_node'],
                                        url=measurement['url'],
                                        browser_version=measurement['browser_version'],
                                        tbb_security_level=measurement['tbb_security_level'],
                                        url_is_https=bool(int(db_url['is_https'])),
                                        url_cdn_provider=db_url['cdn_provider'],
                                        url_requires_multiple_reqs=bool(
                                            int(db_url['requires_multiple_reqs'])),
                                        relay_first_seen=first_seen,
                                        relay_age=(consensus_time - first_seen).days,
                                        relay_is_ipv4_exiting_allowed=db_relay['is_ipv4_exiting_allowed'],
                                        relay_is_ipv6_exiting_allowed=db_relay['is_ipv6_exiting_allowed'],
                                        relay_country=db_relay['country'],
                                        relay_continent=db_relay['continent'],
                                        relay_version=db_relay['version'],
                                        relay_asn=db_relay['asn'],
                                        relay_platform=db_relay['platform'],
                                        relay_exit_probability=consensus_relay.exit_probability))

    ############################################################################

    # Calculate CAPTCHA rates per bin
    captcha_rates_dict = {}
    for graph in graphs:
        # Remove measurements that do not pass the measurement filter
        _measurements = measurements.copy()
        for measurement in measurements:
            if not graph.measurement_filter(measurement, graph.measurement_filter_args):
                _measurements.remove(measurement)

        # Calculate the CAPTCHA rates
        captcha_rates = calculate_captcha_rates_per_graph(consensus_relays_dict,
                                                          consensus_time,
                                                          _measurements,
                                                          graph)

        # Bootstrap the measurements
        bootstrapped_captcha_rates = {}
        sample_size = len(_measurements)
        for n in range(bootstrap_sample_n):
            sample_n = random.choice(_measurements, size=sample_size, replace=True)
            rates = calculate_captcha_rates_per_graph(consensus_relays_dict,
                                                      consensus_time,
                                                      sample_n,
                                                      graph)
            for rate in rates:
                try:
                    bootstrapped_captcha_rates[rate.bin_key].append(rate.rate)
                except KeyError:
                    bootstrapped_captcha_rates[rate.bin_key] = []
                    bootstrapped_captcha_rates[rate.bin_key].append(rate.rate)

        # Calculate the confidence intervals and mean
        for bin_key in bootstrapped_captcha_rates:

            # Place the confidence intervals into corresponding CAPTCHARate objects
            for rate in captcha_rates:
                if rate.bin_key == bin_key:
                    data = bootstrapped_captcha_rates[bin_key]
                    mean, lower_bound, upper_bound = mean_confidence_interval(data)

                    rate.conf_inter = confidence
                    rate.conf_inter_mean = round(mean, 4)
                    rate.conf_inter_lower_bound = round(lower_bound, 4)
                    rate.conf_inter_upper_bound = round(upper_bound, 4)

                    # Stop looping since we found what we need
                    break

        # Save the results
        captcha_rates_dict.update({graph.bin_by_key: captcha_rates})

    return captcha_rates_dict


def mean_confidence_interval(data, confidence=0.95):
    """
    Source: https://stackoverflow.com/a/15034143
    """

    a = 1.0 * array(data)
    n = len(a)
    m, se = mean(a), sem(a)
    h = se * t.ppf((1 + confidence) / 2., n-1)
    return m, m-h, m+h


def calculate_captcha_rates_per_graph(consensus_relays_dict, consensus_time, measurements, graph):
    """

    """

    logger = logging.getLogger(__name__)

    measurement_filter = graph.measurement_filter
    measurement_filter_args = graph.measurement_filter_args
    bin_by_key = graph.bin_by_key
    create_subbins_for_unique_bin_values = graph.create_unique_subbins
    weighted = graph.weighted

    # Bin the measurements
    if bin_by_key == 'relay_age':
        bin_boundaries = [0, 3, 8, 30, 68, 90, 120, 180, 365, 730]
        binned_measurements = bin_based_on_bin_boundaries(measurements, bin_by_key, bin_boundaries)
        del binned_measurements[0]

    elif bin_by_key == 'relay_exit_probability':
        bin_boundaries = [0.0, 0.0001, 0.0002, 0.0003,
                          0.0005, 0.0007, 0.0011, 0.0015, 0.0021, 0.0053]
        binned_measurements = bin_based_on_bin_boundaries(measurements, bin_by_key, bin_boundaries)
        del binned_measurements[0.0]

    else:
        binned_measurements = bin_based_on_key_values(measurements, bin_by_key)

    ############################################################################

    # Calculate weighted CAPTCHA percentages per bin
    # TODO - make this if else mess simpler and more intuitive
    captcha_rates = []
    if create_subbins_for_unique_bin_values:
        # Further bin the values into exit relay bins to calculate weighted CAPTCHA rates
        for bin_key in binned_measurements:
            # TODO - replace "exit_node" with fingerprint once measurements are indexed by fingerprint
            binned_by_exit = bin_based_on_key_values(binned_measurements[bin_key], 'exit_node')

            sub_bin_weighted_percentage, bin_sample_size = digest_captcha_rates(binned_by_exit,
                                                                                consensus_relays_dict,
                                                                                weighted=weighted)

            # Store calculated values
            captcha_rates.append(CAPTCHARate(timestamp=consensus_time,
                                             rate=sub_bin_weighted_percentage,
                                             sample_size=bin_sample_size,
                                             binned_by=bin_by_key,
                                             bin_key=bin_key,
                                             weighted=weighted,
                                             measurement_filter=measurement_filter.__name__,
                                             measurement_filter_args=measurement_filter_args))

    else:
        if weighted:
            # TODO - replace "exit_node" with fingerprint once measurements are indexed by fingerprint
            binned_measurements = bin_based_on_key_values(
                sum(binned_measurements.values(), []), 'exit_node')

        sub_bin_weighted_percentage, bin_sample_size = digest_captcha_rates(binned_measurements,
                                                                            consensus_relays_dict,
                                                                            weighted=weighted)

        # Store calculated values
        captcha_rates.append(CAPTCHARate(timestamp=consensus_time,
                                         rate=sub_bin_weighted_percentage,
                                         sample_size=bin_sample_size,
                                         binned_by=bin_by_key,
                                         weighted=weighted,
                                         measurement_filter=measurement_filter.__name__,
                                         measurement_filter_args=measurement_filter_args))

    return captcha_rates


def digest_captcha_rates(bins, consensus_relays_dict, weighted=False):
    """
    The bin keys need to be exit relay IPv4 address if weighted is set to True
    # TODO - replace "IPv4 address" ^^ with fingerprint once measurements are indexed by fingerprint
    """

    logger = logging.getLogger(__name__)

    bin_sample_size = 0
    bin_captcha_rates = {}

    # Calculate individual CAPTCHA percentages per each bin
    for _bin in bins:
        total_completed_measurements = len(bins[_bin])
        bin_sample_size += total_completed_measurements

        # Count the number of measurements received CAPTCHA
        captcha_found_count = 0
        for measurement in bins[_bin]:
            captcha_found_count += int(measurement.is_captcha_found)

        # Calculate this bin's CAPTCHA percentage
        captcha_percentage = (captcha_found_count / total_completed_measurements) * 100
        bin_captcha_rates.update({_bin: captcha_percentage})

    bin_digested_captcha_rate = 0

    ############################################################################

    # Calculate a single combined CAPTCHA rate
    if weighted:
        # Calculate the weighted percentage value
        for _bin in bin_captcha_rates:
            bin_digested_captcha_rate += bin_captcha_rates[_bin] * \
                consensus_relays_dict[_bin].exit_probability

    else:
        # Calculate the regular percentage value
        total_bin_count = len(bin_captcha_rates)
        for _bin in bin_captcha_rates:
            bin_digested_captcha_rate += (bin_captcha_rates[_bin] / total_bin_count)

    bin_digested_captcha_rate = round(bin_digested_captcha_rate, 4)

    return bin_digested_captcha_rate, bin_sample_size


def bin_based_on_bin_boundaries(measurements_list, bin_key, bin_boundaries):
    """

    """

    # Flatten the values into an array
    bin_values = []
    for measurement in measurements_list:
        bin_values.append(operator.attrgetter(bin_key)(measurement))

    # Create a histogram using numpy
    bin_boundaries.append(max(bin_values) + 1)
    hist, edges = histogram(bin_values, bins=bin_boundaries)

    # Check which bin a value belongs
    target_bins = digitize(bin_values, edges, right=False)

    # Create the bins
    binned = {}
    for bin in bin_boundaries:
        binned.update({bin: []})

    # Place measurements into correct bins
    for idx, target_bin in enumerate(target_bins):
        key = bin_boundaries[target_bin]
        binned[key].append(measurements_list[idx])

    return binned


def bin_based_on_key_values(list, bin_key):
    """
    Bins a list of objects based on the given object attribute's values

    :param list: list of objects
    :type list: list
    :param bin_key: the object attribute that will be used for binning
    :type bin_key: str

    :returns: binned result dictionary:
    :rtype: dict
    """

    binned = {}

    for measurement in list:
        try:
            binned[operator.attrgetter(bin_key)(measurement)].append(measurement)

        except KeyError:
            binned[operator.attrgetter(bin_key)(measurement)] = []
            binned[operator.attrgetter(bin_key)(measurement)].append(measurement)

    return binned


def filter_by_tor_browser_as_method(measurement, args):
    """

    """

    return 'tor_browser' == measurement.method


def filter_by_cloudflare_as_cdn(measurement, args):
    """

    """

    if measurement.url_cdn_provider is None:
        return False

    return 'cloudflare' in measurement.url_cdn_provider


def filter_by_tor_usage(measurement, args):
    """

    """

    return 'tor' in measurement.method


def filter_by_exit_relay(measurement, args):
    """

    """

    return args[0] == measurement.exit_node


def filter_by_nothing(measurement, args):
    """

    """

    return True


@dataclass
class Graph:
    """

    """

    bin_by_key: str
    measurement_filter: Callable
    create_unique_subbins: bool
    weighted: bool
    measurement_filter_args: list = None


@dataclass
class CAPTCHARate:
    """

    """

    timestamp: datetime
    rate: float
    sample_size: int
    binned_by: str
    weighted: bool
    bin_key: str = ''
    measurement_filter: str = ''
    measurement_filter_args: list = field(default_factory=list)
    conf_inter: float = None
    conf_inter_mean: float = None
    conf_inter_lower_bound: float = None
    conf_inter_upper_bound: float = None


@dataclass
class Measurement:
    """

    """

    method: str
    is_captcha_found: bool
    is_data_modified: bool
    exit_node: str
    browser_version: str
    tbb_security_level: str
    url: str
    url_cdn_provider: str
    url_requires_multiple_reqs: bool
    url_is_https: bool
    relay_first_seen: datetime = datetime.datetime.utcnow()
    relay_age: int = 0  # in days
    relay_is_ipv4_exiting_allowed: bool = False
    relay_is_ipv6_exiting_allowed: bool = False
    relay_country: str = 'ZZ'
    relay_continent: str = 'unknown'
    relay_version: str = ''
    relay_asn: str = ''
    relay_platform: str = ''
    relay_exit_probability: float = 0.0

    def __post_init__(self):
        self.is_tor_traffic = True if 'tor' in self.method else False


class RepeatingTimer(Timer):
    def run(self):
        while not self.finished.is_set():
            self.function(*self.args, **self.kwargs)
            self.finished.wait(self.interval)
