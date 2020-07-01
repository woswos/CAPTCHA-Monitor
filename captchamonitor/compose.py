from pathlib import Path
import os
import logging
import sys
import time
import json
from random import randint
from threading import Timer
import captchamonitor.utils.tor_launcher as tor_launcher
from captchamonitor.utils.relays import Relays
from captchamonitor.utils.queue import Queue
from captchamonitor import add
from datetime import datetime
import random
import itertools
import copy

verbose = False
batch_size = 100
use_local_tor = False


def compose(args):
    """
    Automatically add new jobs based on the job history
    """
    logger = logging.getLogger(__name__)

    os.environ['CM_TOR_DIR_PATH'] = str(os.path.join(str(Path.home()), '.cm_tor', '0'))

    global batch_size
    batch_size = args.batch_size

    if args.verbose:
        logging.getLogger('captchamonitor').setLevel(logging.DEBUG)
        global verbose
        verbose = True

    if args.local_tor:
        global use_local_tor
        use_local_tor = True
        logger.info('Using the local Tor for getting the consensus')

    try:
        logger.info('Started running CAPTCHA Monitor Compose')

        logger.info('Setting up the tasks...')

        tasks = []
        minute_multiplier = 60
        tasks.append(RepeatingTimer(args.new_relays * minute_multiplier,
                                    get_new_relays))
        tasks.append(RepeatingTimer(args.match_relays_and_jobs * minute_multiplier,
                                    match_relays_and_jobs))
        tasks.append(RepeatingTimer(args.dispatch_jobs * minute_multiplier,
                                    dispatch_jobs))

        for task in tasks:
            task.start()
            # To reduce the chance of simultaneus database access
            time.sleep(randint(10, 30))

        logger.debug('Done with the tasks, started looping...')

        while True:
            time.sleep(1)

    except Exception as err:
        logging.error(err, exc_info=True)

    except (KeyboardInterrupt, SystemExit):
        logger.info('Stopping CAPTCHA Monitor Compose...')

    finally:
        logger.debug('Stopping the timed tasks...')
        # Stop the created tasks
        for task in tasks:
            task.cancel()

        logger.debug('Completely exitting...')
        sys.exit()


def match_relays_and_jobs():
    logger = logging.getLogger(__name__)

    logger.debug('Started matching job and relay information')

    relays = Relays()
    relays_list = relays.get_relays()

    for relay in relays_list:
        completed_jobs = relays.get_completed_jobs_for_given_relay(relay['address'])

        # If this relay has completed jobs
        if len(completed_jobs) != 0:

            # Create a list of completed jobs in the format we need
            data_list = []
            data_list.append(json.loads(relay['performed_tests']))
            for job in completed_jobs:
                data_list.append({'data': [{'timestamp': job['timestamp'],
                                            'url': job['url'],
                                            'method':  job['method'],
                                            'browser_version': job['browser_version'],
                                            'tbb_security_level':job['tbb_security_level']}]})

            data_list_dict = dict_clean_merge(data_list)

            data = {'performed_tests': json.dumps(data_list_dict)}
            # Now update the database
            relays.update_relay(relay['fingerprint'], data)

    logger.info('Matched job and relay information')


def dispatch_jobs():
    logger = logging.getLogger(__name__)

    logger.debug('Started dispatching a new batch of jobs')

    relays = Relays()

    relays_list = relays.get_relays()

    for counter in range(batch_size):

        # For now choose randomly
        relay = random.choice(relays_list)

        # Only process ones that allow exiting
        if relay['is_ipv6_exiting_allowed'] or relay['is_ipv4_exiting_allowed']:
            performed_tests = json.loads(relay['performed_tests'])

            next_test_values = {}

            # Choose a random random parameters for the next test
            # These parameters will be used for adding the test if the exit
            #   relay doesn't have an history of measurements
            tests = {}
            if relay['is_ipv6_exiting_allowed'] == 1:
                tests = get_tests(ipv6_only=True)
                test_url = list(tests['data']['url'].keys())[0]
                next_test_values['url'] = test_url
                next_test_values['data_hash'] = tests['data']['url'][test_url]
            else:
                tests = get_tests(ipv4_only=True)
                test_url = list(tests['data']['url'].keys())[0]
                next_test_values['url'] = test_url
                next_test_values['data_hash'] = tests['data']['url'][test_url]

            next_test_values['method'] = tests['data']['method'][0]
            next_test_values['tbb_security_level'] = tests['data']['tbb_security_level'][0]
            next_test_values['browser_version'] = ''
            next_test_values['exit_node'] = relay['address']

            # Now consider the history of the relay's measurements and change some
            #   of the parameters
            if performed_tests['data']:
                # Get list of the tests
                tests = get_tests()

                # Creata a cartesian product of the tests to get all combinations
                test_combinations = create_combinations(tests)

                # Get a full list of untested values
                # Simply remove the tested combinations from the full combinations list
                untested = find_untested(performed_tests, test_combinations)

                # I know returning the data under 'data' label instead of directly
                #   returning is dumb but I wanted to be consistent across the
                #   codebase. One day I might get rid of all of these 'data' labels
                untested = untested['data']

                # If there is something untested, overwrite the previously
                #   chosen values
                # The priority is given to the the untested tests
                if untested:
                    # Iterate over the untested measurements until we find
                    #   a suitable one.
                    for test in untested:
                        test_url = test['url']
                        is_ipv6_test = is_ipv6(test_url)
                        is_relay_ipv6 = (relay['is_ipv6_exiting_allowed'] == '1')

                        # Assign an IPv6 url to an exit relay that supports IPv6
                        if(is_ipv6_test and is_relay_ipv6):
                            next_test_values['data_hash'] = tests['data']['url'][test_url]
                            for key in test:
                                next_test_values[key] = test[key]
                            break
                        elif (not is_ipv6_test and not is_relay_ipv6):
                            next_test_values['data_hash'] = tests['data']['url'][test_url]
                            for key in test:
                                next_test_values[key] = test[key]
                            break

                else:
                    # If we are here, it means that this exit relay had completed
                    #   ths combinations of all tests already. Now, we need to refresh
                    #   the oldest test.
                    oldest_test = find_oldest(performed_tests)
                    oldest_test = oldest_test['data']
                    test_url = oldest_test['url']
                    next_test_values['data_hash'] = tests['data']['url'][test_url]
                    del oldest_test['timestamp']

                    for key in oldest_test:
                        next_test_values[key] = oldest_test[key]

            # Construct the arguments for the job adder
            args = Args()
            args.verbose = verbose
            args.all_exit_nodes = False
            args.method = next_test_values['method']
            args.url = next_test_values['url']
            args.captcha_sign = '| Cloudflare'
            args.additional_headers = ''
            args.exit_node = next_test_values['exit_node']
            args.tbb_security_level = next_test_values['tbb_security_level']
            args.browser_version = next_test_values['browser_version']
            args.data_hash = next_test_values['data_hash']

            # Add a new job to the queue with given args
            add.add(args=args, exit_on_finish=False, print_done_message=False)

    logger.info('Dispatched a new batch of jobs')


def get_new_relays():
    logger = logging.getLogger(__name__)

    logger.debug('Started getting the list of new relays')

    relays = Relays()

    # Get latest consensus
    tor = tor_launcher.TorLauncher()
    for relay in tor.get_consensus(use_local_dir=use_local_tor):
        # For now, add only exit relays
        if relay['is_ipv4_exiting_allowed'] == '1':
            # Add the new relay if doesn't exits
            data = {'fingerprint': relay['fingerprint'],
                    'address': relay['address'],
                    'is_ipv4_exiting_allowed': relay['is_ipv4_exiting_allowed'],
                    'is_ipv6_exiting_allowed': relay['is_ipv6_exiting_allowed'],
                    'last_updated': relay['published'],
                    'status': 'online',
                    'performed_tests': '{ "data": [] }'}
            relays.add_relay_if_not_exists(data)

    logger.info('Got the list of new relays')


class Args(object):
    pass


class RepeatingTimer(Timer):
    def run(self):
        while not self.finished.is_set():
            self.function(*self.args, **self.kwargs)
            self.finished.wait(self.interval)


def is_ipv6(url):
    tests = get_tests(ipv6_only=True)
    return url in str(tests)


def get_tests(ipv4_only=False, ipv6_only=False):
    ipv4_urls = {'http://captcha.wtf': '503189ba9e8413d22c1a31f664820894',
                 'https://captcha.wtf': '503189ba9e8413d22c1a31f664820894',
                 'http://captcha.wtf/complex.html': 'b5b69aae854493ae196ce3936644e0ee',
                 'https://captcha.wtf/complex.html': 'b5b69aae854493ae196ce3936644e0ee'}

    ipv6_urls = {'http://exit11.online': '503189ba9e8413d22c1a31f664820894',
                 'https://exit11.online': '503189ba9e8413d22c1a31f664820894',
                 'http://exit11.online/complex.html': 'b5b69aae854493ae196ce3936644e0ee',
                 'https://exit11.online/complex.html': 'b5b69aae854493ae196ce3936644e0ee'}

    methods = ['tor_browser']

    browser_versions = ['9.5']

    tbb_security_levels = ['low', 'medium', 'high']

    if ipv6_only:
        urls = ipv6_urls
    elif ipv4_only:
        urls = ipv4_urls
    else:
        urls = {**ipv4_urls, **ipv6_urls}

    tests_dict = {'url': urls,
                  'method': methods,
                  'tbb_security_level': tbb_security_levels,
                  'browser_version': browser_versions}

    return {'data': tests_dict}


def find_oldest(performed_tests):
    performed_tests = performed_tests['data']

    oldest_time = datetime.now()
    oldest_test = {}
    for test in performed_tests:
        test_time = datetime.strptime(test['timestamp'], '%Y-%m-%d %H:%M:%S')
        if oldest_time > test_time:
            oldest_test = test
            oldest_time = test_time

    return {'data': oldest_test}


def find_untested(performed_tests, tests_list):
    performed_tests_copy = copy.deepcopy(performed_tests['data'])
    for test in performed_tests_copy:
        del test['timestamp']
    tests_list = tests_list['data']

    performed_tests_hashes = []
    for test in performed_tests_copy:
        performed_tests_hashes.append(hash(frozenset(test.items())))

    not_seen = []
    for test in tests_list:
        if hash(frozenset(test.items())) not in performed_tests_hashes:
            not_seen.append(test)

    return {'data': not_seen}


def create_combinations(tests):
    dicts = tests['data']
    return {'data': list(dict(zip(dicts.keys(), x)) for x in itertools.product(*dicts.values()))}


def dict_clean_merge(dicts):
    # Merge
    master_list = []
    for data in dicts:
        for d in data['data']:
            master_list.append(d)

    # Remove duplicate values
    seen = set()
    new_list = []
    for d in master_list:
        t = tuple(d.items())
        if t not in seen:
            seen.add(t)
            new_list.append(d)

    # Get hashes of the measurements without the timestamp
    hashes = {}
    hash_to_data = {}
    for value in new_list:
        new_timestamp = datetime.strptime(value['timestamp'], '%Y-%m-%d %H:%M:%S')
        del value['timestamp']
        hash_val = hash(frozenset(value.items()))
        hash_to_data[hash_val] = value

        # Add the hash if it doesn't exist yet
        if hash_val not in hashes:
            hashes[hash_val] = new_timestamp
        else:
            old_timestamp = hashes[hash_val]
            # If the hash exists, check if the timestamp is newer.
            # Put the newest timestamp
            if new_timestamp > old_timestamp:
                hashes[hash_val] = new_timestamp

    # Now match the hashes and their values
    result = []
    for hash_val in hashes:
        timestamp = {'timestamp': hashes[hash_val].strftime('%Y-%m-%d %H:%M:%S')}
        result.append({**timestamp, **hash_to_data[hash_val]})

    return {'data': result}
