#!/usr/bin/env python3

"""
Fetch a given URL using the requests library
"""

import logging
import requests
import json

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def run(url, additional_headers):
    if additional_headers:
        additional_headers = json.loads(additional_headers)
    results = {}

    # Try sending a request to the server and get server's response
    try:
        data = requests.get(url, headers=additional_headers)

    except Exception as err:
        logger.error('request.get() says: %s' % err)
        return -1

    results['request_headers'] = json.dumps(dict(data.request.headers))
    results['html_data'] = data.text
    results['all_headers'] = data.status_code
    results['response_headers'] = json.dumps(dict(data.headers))

    logger.debug('I\'m done fetching %s', url)

    return results
