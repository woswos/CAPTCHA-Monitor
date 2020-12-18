"""
Fetch a given URL using requests library and Tor
"""

import json
import logging
import os

import captchamonitor.utils.fetcher_utils as fetcher_utils
import captchamonitor.utils.tor_launcher as tor_launcher

import requests


def fetch_via_requests_over_tor(url, additional_headers=None, **kwargs):
    logger = logging.getLogger(__name__)

    try:
        tor_socks_host = os.environ["CM_TOR_HOST"]
        tor_socks_port = os.environ["CM_TOR_SOCKS_PORT"]

    except Exception as err:
        logger.error("Some of the environment variables are missing: %s", err)

    if additional_headers:
        additional_headers = json.loads(additional_headers)

    results = {}

    proxies = {
        "http": "socks5h://%s:%s" % (tor_socks_host, tor_socks_port),
        "https": "socks5h://%s:%s" % (tor_socks_host, tor_socks_port),
    }

    # Try sending a request to the server and get server's response
    try:
        data = requests.get(url, headers=additional_headers, proxies=proxies)

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
