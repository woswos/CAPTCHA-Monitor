#!/usr/bin/env python3

"""
Fetch a given URL using selenium and Tor browser
"""

import logging
from seleniumwire import webdriver
from selenium.webdriver.firefox.firefox_profile import FirefoxProfile
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from selenium.webdriver.firefox.options import Options
from pyvirtualdisplay import Display
import os
from time import sleep

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Only needed if running in headless mode
try:
    from pyvirtualdisplay import Display
except ImportError:
    logger.debug('PyVirtualDisplay is not installed')
    pass


def fetch(params):
    """
    Does the required conversions
    """
    url = params.get('url')
    tbb_path = params.get('tbb_path')
    request_headers = params.get('request_headers')

    # Run the test and return the results with other parameters
    params['html_data'] = fetch_url(tbb_path, url)

    params['request_headers'] = "N/A"
    params['status_code'] = "N/A"
    params['response_headers'] = "N/A"

    logger.debug('I\'m done fetching %s', url)

    return params


def fetch_url(tbb_dir, url):
    """
    Launch the given url in the browser and get the result
    """

    #path to TOR binary
    os.popen(tbb_dir + 'Browser/firefox')

    #path to TOR profile
    profile = FirefoxProfile(tbb_dir + 'Browser/TorBrowser/Data/Browser/profile.default')

    #profile.set_preference( "network.proxy.type", 1 )
    #profile.set_preference( "network.proxy.socks", '127.0.0.1' )
    #profile.set_preference( "network.proxy.socks_port", 9050 )
    #profile.set_preference( "network.proxy.socks_remote_dns", False )
    #profile.update_preferences()

    xvfb_display = Display(visible=0, size=(800, 600))
    xvfb_display.start()

    options = {
        'proxy': {
            'http': 'socks5://127.0.0.1:9050',
            'https': 'socks5://127.0.0.1:9050'
        }
    }

    driver = webdriver.Firefox(firefox_profile=profile, seleniumwire_options=options)


    driver.get(url)

    data = driver.page_source

    driver.quit()

    xvfb_display.stop()

    return data
