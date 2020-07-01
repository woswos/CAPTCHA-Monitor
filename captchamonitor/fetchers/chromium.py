"""
Fetch a given URL using seleniumwire and Chromium
"""

import logging
import json
import sys
import socket
from urltools import compare
from seleniumwire import webdriver
from selenium.webdriver.chrome.options import Options
import captchamonitor.utils.format_requests as format_requests


def fetch_via_chromium(url, additional_headers=None, timeout=30, **kwargs):
    logger = logging.getLogger(__name__)

    results = {}

    # Choose the headless mode
    options = Options()
    options.headless = True
    options.add_argument("--no-sandbox")
    options.add_argument("--headless")

    # Set the timeout for webdriver initialization
    #socket.setdefaulttimeout(15)

    try:
        driver = webdriver.Chrome(options=options)
    except Exception as err:
        logger.error('Couldn\'t initialize the browser, check if there is enough memory available: %s'
                     % err)
        return None

    if additional_headers:
        driver.header_overrides = json.loads(additional_headers)

    # Set driver page load timeout
    driver.implicitly_wait(timeout)
    #socket.setdefaulttimeout(timeout)

    # Try sending a request to the server and get server's response
    try:
        driver.get(url)

    except Exception as err:
        driver.quit()
        logger.error('webdriver.Chrome.get() says: %s' % err)
        return None

    # Record the results
    results['html_data'] = driver.page_source
    results['requests'] = format_requests.seleniumwire(driver.requests)

    logger.debug('I\'m done fetching %s', url)

    driver.quit()

    return results
