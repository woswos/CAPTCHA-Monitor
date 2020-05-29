#!/usr/bin/env python3

"""
Fetch a given URL using the requests library
"""

import logging
import requests
import json

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
    data = fetch_url(url, request_headers)

    params['request_headers'] = json.dumps(dict(data.request.headers))
    params['html_data'] = data.text
    params['status_code'] = data.status_code
    params['response_headers'] = json.dumps(dict(data.headers))

    logger.debug('I\'m done fetching %s', url)
    
    return params


def fetch_url(url, request_headers):
    """
    Fetch the website
    """
    # Try sending a request to the server and get server's response
    try:
        data = requests.get(url, headers=request_headers)

    except Exception as err:
        logger.error('request.get() says: %s' % err)
        return -1

    return data
