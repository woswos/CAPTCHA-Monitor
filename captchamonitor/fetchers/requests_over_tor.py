"""
Fetch a given URL using requests library and Tor
"""

import logging
import requests
import json
import captchamonitor.utils.tor_launcher as tor_launcher

logger = logging.getLogger(__name__)


def requests_over_tor(url, tor_socks_host, tor_socks_port, additional_headers=None, exit_node=None, **kwargs):

    tor_process = tor_launcher.launch_tor_with_config(tor_socks_port, exit_node)

    # Wait until Tor starts
    while(not tor_launcher.is_tor_running(tor_socks_port)):
        pass

    if additional_headers:
        additional_headers = json.loads(additional_headers)
    results = {}

    proxies = {
        'http': 'socks5h://' + tor_socks_host + ':' + tor_socks_port,
        'https': 'socks5h://' + tor_socks_host + ':' + tor_socks_port,
    }

    # Try sending a request to the server and get server's response
    try:
        data = requests.get(url, headers=additional_headers, proxies=proxies)

    except Exception as err:
        logger.error('request.get() says: %s' % err)
        return -1

    results['request_headers'] = json.dumps(dict(data.request.headers))
    results['html_data'] = str(data.text)
    results['all_headers'] = str(data.status_code)
    results['response_headers'] = json.dumps(dict(data.headers))

    logger.debug('I\'m done fetching %s', url)

    tor_launcher.kill(tor_process)

    return results
