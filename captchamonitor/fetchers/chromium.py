"""
Fetch a given URL using selenium and Chromium
"""

import os
import pathlib
import glob
import logging
import json
import socket
import time
from pyvirtualdisplay import Display
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import captchamonitor.utils.format_requests as format_requests
import captchamonitor.utils.fetcher_utils as fetcher_utils


def fetch_via_chromium(url, additional_headers=None, timeout=30, **kwargs):
    logger = logging.getLogger(__name__)

    try:
        download_folder = os.environ['CM_DOWNLOAD_FOLDER']
    except Exception as err:
        logger.error('Some of the environment variables are missing: %s', err)

    results = {}

    http_header_live_extension_id = 'mhmbgecfengpllohfhnkpapmbgiphhff'

    # Find the right extension
    http_header_live_folder = '../assests/http_header_live/'
    script_path = pathlib.Path(__file__).parent.absolute()
    search_string = os.path.abspath(os.path.join(script_path,
                                                 http_header_live_folder,
                                                 '*.crx'))
    http_header_live_extension = glob.glob(search_string)[0]

    http_header_live_export_file = os.path.join(download_folder,
                                                'captcha_monitor_website_data.json')

    # Delete the previous HTTP-Header-Live export
    if os.path.exists(http_header_live_export_file):
        os.remove(http_header_live_export_file)

    # Start virtual display because Chromium doesn't support extensions in headless mode
    display = Display(visible=True, size=(1000, 900), backend='xvfb')
    display.start()

    options = Options()
    # options.headless = True
    # options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-dev-shm-usage')

    # Set the download folder and disable pop up windows
    prefs = {"profile.default_content_settings.popups": 0,
             "download.default_directory": download_folder,
             "directory_upgrade": True}
    options.add_experimental_option("prefs", prefs)

    # Required to enabled third party extensions
    options.add_argument('–-enable-easy-off-store-extension-install')
    options.add_extension(http_header_live_extension)

    # Set the timeout for webdriver initialization
    # socket.setdefaulttimeout(15)

    try:
        driver = webdriver.Chrome(options=options)
    except Exception as err:
        display.stop()
        logger.error('Couldn\'t initialize the browser, check if there is enough memory available: %s'
                     % err)
        return None

    # Start the HTTP-Header-Live extension and switch to a new tab for the actual URL fetch
    try:
        driver.get('chrome-extension://%s/HTTPHeaderMain.html' % http_header_live_extension_id)
        driver.execute_script("window.open('about:blank', 'tab2');")
        driver.switch_to.window("tab2")

    except Exception as err:
        force_quit(driver)
        display.stop()
        logger.error('Couldn\'t launch HTTP-Header-Live: %s' % err)
        return None

    # Set driver page load timeout
    driver.implicitly_wait(timeout)
    # socket.setdefaulttimeout(timeout)

    # Try sending a request to the server and get server's response
    try:
        driver.get(url)

        # Chromium returns a valid HTML page even if the page was not fetched.
        #   The returned page contains the license and 'The Chromium Authors'
        #   was choosen because of this reason.
        if 'The Chromium Authors' in driver.page_source:
            raise Exception('This site can’t be reached')

    except Exception as err:
        force_quit(driver)
        display.stop()
        logger.error('webdriver.Chrome.get() says: %s' % err)
        return None

    # Wait for HTTP-Header-Live extension to finish
    timeout = 20
    requests_data = None
    logger.debug('Waiting for HTTP-Header-Live extension')
    for counter in range(timeout):
        try:
            with open(http_header_live_export_file) as file:
                requests_data = json.load(file)
                break

        except OSError:
            time.sleep(1)

        except Exception as err:
            force_quit(driver)
            logger.error('Cannot parse the headers: %s' % err)
            return None

    if requests_data is None:
        force_quit(driver)
        # Don't return anything since we couldn't capture the headers
        logger.error('Couldn\'t capture the headers from %s' % http_header_live_export_file)
        return None

    # Record the results
    results['html_data'] = driver.page_source
    results['requests'] = format_requests.tb(requests_data, url)

    logger.debug('I\'m done fetching %s', url)

    fetcher_utils.force_quit_driver(driver)
    display.stop()

    return results
