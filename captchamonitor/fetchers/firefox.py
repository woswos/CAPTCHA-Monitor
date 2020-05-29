#!/usr/bin/env python3

"""
Fetch a given URL using selenium and Firefox
"""

import logging
import json
import sys
from urltools import compare
from seleniumwire import webdriver
from selenium.webdriver.firefox.options import Options

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def run(url, additional_headers):
    results = {}

    # Create a new instance of the Firefox driver
    options = Options()
    options.headless = True
    driver = webdriver.Firefox(options=options)

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

    return results
