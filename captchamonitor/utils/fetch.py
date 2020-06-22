import logging
import os
import pwd
from captchamonitor import fetchers
import captchamonitor.utils.tor_launcher as tor_launcher


def fetch_via_method(data):
    logger = logging.getLogger(__name__)

    method = data['method']
    url = data['url']
    captcha_sign = data['captcha_sign']
    additional_headers = data['additional_headers']
    exit_node = data['exit_node']
    tbb_security_level = data['tbb_security_level']

    results = {}
    logger.debug('Fetching "%s" via "%s"', url, method)

    if(method == 'tor_browser'):
        results = fetchers.tor_browser(url,
                                       additional_headers,
                                       tbb_security_level)

    elif(method == 'firefox_over_tor'):
        results = fetchers.firefox_over_tor(url, additional_headers)

    elif(method == 'chromium_over_tor'):
        results = fetchers.chromium_over_tor(url, additional_headers)

    elif(method == 'requests_over_tor'):
        results = fetchers.requests_over_tor(url, additional_headers)

    elif(method == 'curl_over_tor'):
        results = fetchers.curl_over_tor(url, additional_headers)

    elif(method == 'requests'):
        results = fetchers.requests(url, additional_headers)

    elif(method == 'firefox'):
        results = fetchers.firefox(url, additional_headers)

    elif(method == 'chromium'):
        results = fetchers.chromium(url, additional_headers)

    elif(method == 'curl'):
        results = fetchers.curl(url, additional_headers)

    else:
        logger.warning('"%s" is not available, please check the method name"', method)
        return None

    return results
