#!/usr/bin/env python3

"""
Fetch a given URL using selenium and Firefox
"""

import logging
import json
from seleniumwire import webdriver
from selenium.webdriver.firefox.options import Options

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def fetch(params):
    """
    Does the required conversions
    """
    url = params.get('url')
    captcha_sign = params.get('captcha_sign')
    request_headers = params.get('request_headers')
    if(request_headers != None):
        request_headers = json.loads(request_headers)

    # Run the test and return the results with other parameters
    driver = fetch_url(url, request_headers)

    for request in driver.requests:
        if((request.response) and (request.path == url)):
                params['request_headers'] = json.dumps(dict(request.headers))
                params['html_data'] = driver.page_source
                params['status_code'] = request.response.status_code
                params['response_headers'] = json.dumps(dict(request.response.headers))

    return params


def fetch_url(url, request_headers):
    """
    Fetch the website
    """

    # Create a new instance of the Firefox driver
    options = Options()
    options.headless = True
    driver = webdriver.Firefox(options=options)

    # Try sending a request to the server and get server's response
    try:
        # Go to the Google home page
        driver.get(url)

    except Exception as err:
        logger.error('webdriver.Firefox.get() says: %s' % err)
        return -1

    return driver
