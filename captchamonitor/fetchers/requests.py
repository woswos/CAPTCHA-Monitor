"""
Fetch a given URL using the requests library
"""

import logging
import requests
import json

logger = logging.getLogger(__name__)


def fetch_via_requests(url, additional_headers=None, **kwargs):

    if additional_headers:
        additional_headers = json.loads(additional_headers)
    results = {}

    # Try sending a request to the server and get server's response
    try:
        data = requests.get(url, headers=additional_headers)

    except Exception as err:
        logger.error('request.get() says: %s' % err)
        return None

    results['request_headers'] = json.dumps(dict(data.request.headers))
    results['html_data'] = str(data.text)
    results['all_headers'] = str(data.status_code)
    results['response_headers'] = json.dumps(dict(data.headers))

    logger.debug('I\'m done fetching %s', url)

    return results
