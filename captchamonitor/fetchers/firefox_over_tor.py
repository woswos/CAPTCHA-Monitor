"""
Fetch a given URL using seleniumwire, Firefox, and Tor
"""

import os
import logging
import json
from urltools import compare
from seleniumwire import webdriver
from selenium.webdriver.firefox.options import Options


def fetch_via_firefox_over_tor(url, additional_headers=None, **kwargs):
    logger = logging.getLogger(__name__)

    try:
        tor_socks_host = os.environ['CM_TOR_HOST']
        tor_socks_port = os.environ['CM_TOR_SOCKS_PORT']
    except Exception as err:
        logger.error('Some of the environment variables are missing: %s', err)

    results = {}

    # Configure seleniumwire to upstream traffic to Tor running on port 9050
    #   You might want to increase/decrease the timeout if you are trying
    #   to a load page that requires a lot of requests. It is in seconds.
    seleniumwire_options = {
        'proxy': {
            'http': 'socks5h://%s:%s' % (tor_socks_host, tor_socks_port),
            'https': 'socks5h://%s:%s' % (tor_socks_host, tor_socks_port),
            'connection_timeout': 30
        }
    }

    # Choose the headless mode
    options = Options()
    options.headless = True

    driver = webdriver.Firefox(options=options,
                               seleniumwire_options=seleniumwire_options)

    if additional_headers:
        driver.header_overrides = json.loads(additional_headers)

    # Try sending a request to the server and get server's response
    try:
        driver.get(url)

    except Exception as err:
        logger.error('webdriver.Firefox.get() says: %s' % err)
        return None

    # Record the results
    results['html_data'] = driver.page_source
    results['all_headers'] = str(driver.requests)

    for request in driver.requests:
        if(compare(request.path, url)):
            results['request_headers'] = json.dumps(dict(request.headers))
            if(request.response):
                results['response_headers'] = json.dumps(dict(request.response.headers))
            else:
                results['response_headers'] = " "

    logger.debug('I\'m done fetching %s', url)

    driver.quit()

    return results
