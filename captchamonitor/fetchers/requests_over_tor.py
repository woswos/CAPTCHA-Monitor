"""
Fetch a given URL using requests library and Tor
"""

import logging
import requests
import json
import captchamonitor.utils.tor_launcher as tor_launcher
import os


def fetch_via_requests_over_tor(url, additional_headers=None, **kwargs):
    logger = logging.getLogger(__name__)

    try:
        tor_socks_host = os.environ['CM_TOR_HOST']
        tor_socks_port = os.environ['CM_TOR_SOCKS_PORT']
    except Exception as err:
        logger.error('Some of the environment variables are missing: %s', err)

    if additional_headers:
        additional_headers = json.loads(additional_headers)
    results = {}

    proxies = {
        'http': 'socks5h://%s:%s' % (tor_socks_host, tor_socks_port),
        'https': 'socks5h://%s:%s' % (tor_socks_host, tor_socks_port)
    }

    # Try sending a request to the server and get server's response
    try:
        data = requests.get(url, headers=additional_headers, proxies=proxies)

    except Exception as err:
        logger.error('request.get() says: %s' % err)
        return None

    results['request_headers'] = json.dumps(dict(data.request.headers))
    results['html_data'] = str(data.text)
    results['all_headers'] = str(data.status_code)
    results['response_headers'] = json.dumps(dict(data.headers))

    logger.debug('I\'m done fetching %s', url)

    return results
