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


# Handles the given argument list and runs the test
def fetch(params):
    url = params.get('url')
    tbb_path = params.get('tbb_path')
    headless_mode = params.get('headless_mode')

    # Run the test and return the results with other parameters
    return fetch_url(tbb_path, url, headless_mode)


# Launch the given url in the browser and get the result
def fetch_url(tbb_dir, url, headless_mode):
    try:

        if headless_mode:
            logger.debug('Running in headless mode')

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

        if headless_mode:
            stop_xvfb(xvfb_display)

    except Exception as err:
        logger.error('Cannot fetch %s: %s' % (url, err))
        message = ('Sometimes running in headless mode on desktop OS '
                   'causes issues. Please check that.')
        logger.warning(message)
        result = -1

    return result
