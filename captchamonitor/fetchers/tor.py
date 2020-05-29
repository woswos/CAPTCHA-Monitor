#!/usr/bin/env python3

"""
Fetch a given URL using selenium and Tor browser
"""

import os
import logging
import json
from urltools import compare
from seleniumwire import webdriver
from selenium.webdriver.firefox.firefox_profile import FirefoxProfile
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from pyvirtualdisplay import Display

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def run(url, additional_headers, tbb_path, tor_socks_address, tor_socks_port):
    results = {}

    os.popen(os.path.join(tbb_path, 'Browser/firefox'))
    profile = FirefoxProfile(os.path.join(tbb_path, 'Browser/TorBrowser/Data/Browser/profile.default'))

    options = {
        'proxy': {
            'http': 'socks5h://127.0.0.1:9050',
            'https': 'socks5h://127.0.0.1:9050'
        }
    }

    xvfb_display = Display(visible=0, size=(1600, 900))
    xvfb_display.start()

    driver = webdriver.Firefox(seleniumwire_options=options)

    if additional_headers:
        driver.header_overrides = json.loads(additional_headers)

    # Try sending a request to the server and get server's response
    try:
        driver.get(url)

    except Exception as err:
        logger.error('webdriver.Firefox.get() says: %s' % err)
        return -1

    # Record the results
    results['html_data'] = driver.page_source
    results['all_headers'] = str(driver.requests)

    for request in driver.requests:
        if(compare(request.path, url)):
                results['request_headers'] = json.dumps(dict(request.headers))
                results['response_headers'] = json.dumps(dict(request.response.headers))

    logger.debug('I\'m done fetching %s', url)

    driver.quit()

    xvfb_display.stop()

    return results
