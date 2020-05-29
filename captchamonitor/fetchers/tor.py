#!/usr/bin/env python3

"""
Fetch a given URL using selenium and Tor browser
"""

import logging
from tbselenium.tbdriver import TorBrowserDriver
from tbselenium.utils import start_xvfb, stop_xvfb
from selenium.webdriver.support.ui import Select

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

    return params


def fetch_url(tbb_dir, url):
    """
    Launch the given url in the browser and get the result
    """
    try:

        # Try starting a virtual display
        try:
            # start a virtual display
            xvfb_display = start_xvfb()

        except Exception as err:
            logger.debug(err)
            logger.error('Check if you installed Xvfb and PyVirtualDisplay')
            return -1

        # Open Tor Browser
        with TorBrowserDriver(tbb_dir) as driver:
            driver.load_url(url)

            # Check if the captcha sign exists within the page
            # I could have returned the function here but we need to close the
            #       virtual display if run in headless mode. Otherwise, the
            #       virtul displays let open fills the memory very quickly
            result = driver.page_source

        stop_xvfb(xvfb_display)

    except Exception as err:
        logger.error('Cannot fetch %s: %s' % (url, err))
        message = ('Sometimes running in headless mode on desktop OS '
                   'causes issues. Please check that.')
        logger.warning(message)
        result = -1

    return result
