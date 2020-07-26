import logging
import os
import pwd
from captchamonitor import fetchers


def fetch_via_method(data, timeout=30):
    logger = logging.getLogger(__name__)

    method = data['method']
    url = data['url']
    captcha_sign = data['captcha_sign']
    additional_headers = data['additional_headers']
    exit_node = data['exit_node']
    tbb_security_level = data['tbb_security_level']
    browser_version = data['browser_version']

    method_to_folder = {'tor_browser': 'tor_browser',
                        'firefox': 'firefox',
                        'firefox_over_tor': 'firefox',
                        'chromium': 'chromium',
                        'chromium_over_tor': 'chromium',
                        'brave': 'brave',
                        'brave_over_tor': 'brave'}

    method_path = os.path.join(os.environ['CM_BROWSER_VERSIONS_PATH'], method_to_folder[method])

    if ('tor_browser' in method) or ('firefox' in method) or ('chromium' in method) or ('brave' in method):
        # Find the latest version available if not specified
        if (browser_version == ''):
            browser_version = get_latest_version(method_path)
            logger.debug('The latest version available for "%s" is "%s"' %
                         (method, browser_version))

        browser_path = os.path.join(method_path, browser_version)

        if not os.path.exists(browser_path):
            logger.warning('The specified browser version %s for %s does not exist' %
                           (browser_version, method))
            return None

        os.environ['CM_BROWSER_PATH'] = browser_path

        logger.debug('Fetching "%s" via "%s" - "v%s"' % (url, method, browser_version))

    else:
        logger.debug('Fetching "%s" via "%s"' % (url, method))

    results = {}
    if(method == 'tor_browser'):
        results = fetchers.tor_browser(url,
                                       additional_headers=additional_headers,
                                       security_level=tbb_security_level,
                                       timeout=timeout)

    elif(method == 'firefox_over_tor'):
        results = fetchers.firefox_over_tor(url,
                                            additional_headers=additional_headers,
                                            timeout=timeout)

    elif(method == 'chromium_over_tor'):
        results = fetchers.chromium_over_tor(url,
                                             additional_headers=additional_headers,
                                             timeout=timeout)
    elif(method == 'brave_over_tor'):
        results = fetchers.brave_over_tor(url,
                                          exit_node,
                                          additional_headers=additional_headers,
                                          timeout=timeout)

    elif(method == 'requests_over_tor'):
        results = fetchers.requests_over_tor(url,
                                             additional_headers=additional_headers,
                                             timeout=timeout)

    elif(method == 'curl_over_tor'):
        results = fetchers.curl_over_tor(url, additional_headers)

    elif(method == 'requests'):
        results = fetchers.requests(url, additional_headers)

    elif(method == 'firefox'):
        results = fetchers.firefox(url,
                                   additional_headers=additional_headers,
                                   timeout=timeout)

    elif(method == 'chromium'):
        results = fetchers.chromium(url,
                                    additional_headers=additional_headers,
                                    timeout=timeout)
    elif(method == 'brave'):
        results = fetchers.brave(url,
                                 additional_headers=additional_headers,
                                 timeout=timeout)
    elif(method == 'curl'):
        results = fetchers.curl(url, additional_headers)

    else:
        logger.warning('"%s" is not available, please check the method name"', method)
        return None

    if results is not None:
        # Add the browser version if it wasn't specified
        results['browser_version'] = browser_version

    return results


def get_latest_version(path):
    import os
    import re

    def atoi(text):
        return int(text) if text.isdigit() else text

    def natural_keys(text):
        return [atoi(c) for c in re.split(r'(\d+)', text)]

    versions = next(os.walk(path))[1]
    versions.sort(key=natural_keys)
    return versions[-1]
