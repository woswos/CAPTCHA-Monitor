"""
Fetch a given URL using seleniumwire and Tor Browser
"""

import os
import logging
import json
from urltools import compare
from seleniumwire import webdriver
from selenium.webdriver.firefox.firefox_profile import FirefoxProfile
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from selenium.webdriver.firefox.options import Options

logger = logging.getLogger(__name__)


def fetch_via_tor_browser(url, additional_headers=None, security_level='medium', **kwargs):

    tbb_path = os.environ['CM_TBB_PATH']
    tor_socks_host = os.environ['CM_TOR_HOST']
    tor_socks_port = os.environ['CM_TOR_SOCKS_PORT']

    security_levels = {'high': 1, 'medium': 2, 'low': 4}

    results = {}

    # Disable Tor Launcher to prevent it connecting the Tor Browser to Tor directly
    os.environ['TOR_SKIP_LAUNCH'] = '1'
    os.environ['TOR_TRANSPROXY'] = '1'

    # Set the Tor Browser binary and profile
    tb_binary = os.path.join(tbb_path, 'Browser/firefox')
    tb_profile = os.path.join(tbb_path, 'Browser/TorBrowser/Data/Browser/profile.default')
    binary = FirefoxBinary(os.path.join(tbb_path, 'Browser/firefox'))
    profile = FirefoxProfile(tb_profile)

    # We need to disable HTTP Strict Transport Security (HSTS) in order to have
    #   seleniumwire between the browser and Tor. Otherwise, we will not be able
    #   to capture the requests and responses using seleniumwire.
    profile.set_preference("security.cert_pinning.enforcement_level", 0)
    profile.set_preference("network.stricttransportsecurity.preloadlist", False)
    profile.set_preference("extensions.torbutton.local_tor_check", False)
    profile.set_preference("extensions.torbutton.use_nontor_proxy", True)

    # Set the security level
    profile.set_preference("extensions.torbutton.security_slider", security_levels[security_level])

    # Configure seleniumwire to upstream traffic to Tor running on port 9050
    #   You might want to increase/decrease the timeout if you are trying
    #   to a load page that requires a lot of requests. It is in seconds.
    seleniumwire_options = {
        'proxy': {
            'http': 'socks5h://%s:%s' % (tor_socks_host, tor_socks_port),
            'https': 'socks5h://%s:%s' % (tor_socks_host, tor_socks_port),
            'connection_timeout': 30
        }
    }

    # Choose the headless mode
    options = Options()
    options.headless = True

    driver = webdriver.Firefox(firefox_profile=profile,
                               firefox_binary=binary,
                               options=options,
                               seleniumwire_options=seleniumwire_options)

    if additional_headers:
        driver.header_overrides = json.loads(additional_headers)

    # Try sending a request to the server and get server's response
    try:
        driver.get(url)

    except Exception as err:
        logger.error('webdriver.Firefox.get() says: %s' % err)
        return None

    # Record the results
    results['html_data'] = driver.page_source
    results['all_headers'] = str(driver.requests)

    for request in driver.requests:
        if(compare(request.path, url)):
            results['request_headers'] = json.dumps(dict(request.headers))
            if(request.response):
                results['response_headers'] = json.dumps(dict(request.response.headers))
            else:
                results['response_headers'] = " "

    logger.debug('I\'m done fetching %s', url)

    driver.quit()

    return results
