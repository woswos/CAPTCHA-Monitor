import logging
import os
from captchamonitor import fetchers
logger = logging.getLogger(__name__)


def fetch_via_method(data):
    tbb_path = os.environ['CM_TBB_PATH']
    tor_socks_host = os.environ['CM_TOR_HOST']
    tor_socks_port = os.environ['CM_TOR_SOCKS_PORT']
    tor_control_port = int(os.environ['CM_TOR_CONTROL_PORT'])

    method = data['method']
    url = data['url']
    captcha_sign = data['captcha_sign']
    additional_headers = data['additional_headers']
    exit_node = data['exit_node']
    tbb_security_level = data['tbb_security_level']

    results = {}
    logger.info('Fetching "%s" via "%s"', url, method)

    if(method == 'tor_browser'):
        results = fetchers.tor_browser(url=url,
                                       additional_headers=additional_headers,
                                       tbb_path=tbb_path,
                                       tor_socks_host=tor_socks_host,
                                       tor_socks_port=tor_socks_port,
                                       tor_control_port=tor_control_port,
                                       security_level=tbb_security_level,
                                       exit_node=exit_node)

    elif(method == 'firefox_over_tor'):
        results = fetchers.firefox_over_tor(url=url,
                                            additional_headers=additional_headers,
                                            tor_socks_host=tor_socks_host,
                                            tor_socks_port=tor_socks_port,
                                            tor_control_port=tor_control_port,
                                            exit_node=exit_node)

    elif(method == 'chromium_over_tor'):
        results = fetchers.chromium_over_tor(url=url,
                                             additional_headers=additional_headers,
                                             tor_socks_host=tor_socks_host,
                                             tor_socks_port=tor_socks_port,
                                             tor_control_port=tor_control_port,
                                             exit_node=exit_node)

    elif(method == 'requests_over_tor'):
        results = fetchers.requests_over_tor(url=url,
                                             additional_headers=additional_headers,
                                             tor_socks_host=tor_socks_host,
                                             tor_socks_port=tor_socks_port,
                                             tor_control_port=tor_control_port,
                                             exit_node=exit_node)

    elif(method == 'curl_over_tor'):
        results = fetchers.curl_over_tor(url=url,
                                         additional_headers=additional_headers,
                                         tor_socks_host=tor_socks_host,
                                         tor_socks_port=tor_socks_port,
                                         tor_control_port=tor_control_port,
                                         exit_node=exit_node)

    elif(method == 'requests'):
        results = fetchers.requests(url, additional_headers)

    elif(method == 'firefox'):
        results = fetchers.firefox(url, additional_headers)

    elif(method == 'chromium'):
        results = fetchers.chromium(url, additional_headers)

    elif(method == 'curl'):
        results = fetchers.curl(url, additional_headers)

    else:
        logger.info('"%s" is not available, please check the method name"', method)
        return None

    return results
