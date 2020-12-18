"""
Fetch a given URL using the requests library
"""

import json
import logging

import captchamonitor.utils.fetcher_utils as fetcher_utils

import requests


def fetch_via_requests(url, additional_headers=None, **kwargs):
    logger = logging.getLogger(__name__)

    if additional_headers:
        additional_headers = json.loads(additional_headers)
    results = {}

    # Try sending a request to the server and get server's response
    try:
        data = requests.get(url, headers=additional_headers)

    except Exception as err:
        logger.error("request.get() says: %s" % err)
        return None

    results["html_data"] = str(data.text)
    results["requests"] = fetcher_utils.format_requests_requests(
        dict(data.request.headers),
        dict(data.headers),
        str(data.status_code),
        url,
    )

    logger.debug("I'm done fetching %s", url)

    return results
