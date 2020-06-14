"""
Fetch a given URL using seleniumwire, Chromium, and Tor
"""

import os
import logging
import json
from urltools import compare
from seleniumwire import webdriver
from selenium.webdriver.chrome.options import Options

logger = logging.getLogger(__name__)


def fetch_via_chromium_over_tor(url, additional_headers=None, **kwargs):

    tor_socks_host = os.environ['CM_TOR_HOST']
    tor_socks_port = os.environ['CM_TOR_SOCKS_PORT']

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
    options.add_argument("--no-sandbox")
    options.add_argument("--headless")

    driver = webdriver.Chrome(options=options,
                              seleniumwire_options=seleniumwire_options)

    if additional_headers:
        driver.header_overrides = json.loads(additional_headers)

    # Try sending a request to the server and get server's response
    try:
        driver.get(url)

    except Exception as err:
        logger.error('webdriver.Chrome.get() says: %s' % err)
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
