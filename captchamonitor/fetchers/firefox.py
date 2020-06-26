"""
Fetch a given URL using seleniumwire and Firefox
"""

import logging
import json
import sys
from urltools import compare
from seleniumwire import webdriver
from selenium.webdriver.firefox.options import Options
import captchamonitor.utils.format_requests as format_requests


def fetch_via_firefox(url, additional_headers=None, **kwargs):
    logger = logging.getLogger(__name__)

    results = {}

    # Choose the headless mode
    options = Options()
    options.headless = True

    try:
        driver = webdriver.Firefox(options=options)
    except Exception as err:
        logger.error('Couldn\'t initialize the browser, check if there is enough memory available: %s'
                     % err)
        return None

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
    results['requests'] = format_requests.seleniumwire(driver.requests)

    logger.debug('I\'m done fetching %s', url)

    driver.quit()

    return results
