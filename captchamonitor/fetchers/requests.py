#!/usr/bin/env python3

"""
Fetch a given URL using the requests library
"""

import logging
import requests

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Handles given the argument list and runs the test
def fetch(params):
    url = params.get('url')
    captcha_sign = params.get('captcha_sign')
    headers = params.get('headers')

    # Insert current UNIX time stamp
    params['time_stamp'] = int(time.time())
    params['method'] = 'requests'

    # Run the test and return the results with other parameters
    params['html_data'] = fetch_url(url, captcha_sign, headers)

    return params


# Check if site returns a CloudFlare CAPTCHA
def fetch_url(url, captcha_sign, headers):
    # Try sending a request to the server and get server's response
    try:
        data = requests.get(url, headers=headers)

    except Exception as err:
        logger.error('Double check the url you have entered because request.get() says: %s' % err)
        return -1

    return data.text
