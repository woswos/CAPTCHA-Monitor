"""
Fetch a given URL using seleniumwire and Firefox
"""

import logging
import json
import sys
from urltools import compare
from seleniumwire import webdriver
from selenium.webdriver.firefox.options import Options

logger = logging.getLogger(__name__)


def fetch_via_firefox(url, additional_headers=None, **kwargs):
    results = {}

    # Choose the headless mode
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
