"""
Fetch a given URL using selenium and Tor Browser
"""

import os
import logging
import json
import time
import socket
import pathlib
import glob
from selenium import webdriver
from selenium.webdriver.firefox.firefox_profile import FirefoxProfile
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from selenium.webdriver.firefox.options import Options
import captchamonitor.utils.format_requests as format_requests


def fetch_via_tor_browser(url, additional_headers=None, security_level='medium', timeout=30, **kwargs):
    logger = logging.getLogger(__name__)

    try:
        tbb_path = os.environ['CM_BROWSER_PATH']
        tor_socks_host = os.environ['CM_TOR_HOST']
        tor_socks_port = os.environ['CM_TOR_SOCKS_PORT']
        download_folder = os.environ['CM_DOWNLOAD_FOLDER']
    except Exception as err:
        logger.error('Some of the environment variables are missing: %s', err)

    security_levels = {'high': 1, 'medium': 2, 'low': 4}

    results = {}
    http_header_live_export_file = os.path.join(download_folder, 'captcha_monitor_website_data.json')

    # Find the right extension
    http_header_live_folder = '../assests/http_header_live/'
    script_path = pathlib.Path(__file__).parent.absolute()
    search_string = os.path.abspath(os.path.join(script_path,
                                                 http_header_live_folder,
                                                 '*.xpi'))
    http_header_live_extension = glob.glob(search_string)[0]

    # Delete the previous HTTP-Header-Live export
    if os.path.exists(http_header_live_export_file):
        os.remove(http_header_live_export_file)

    # Set the Tor Browser binary and profile
    tb_binary = os.path.join(tbb_path, 'Browser/firefox')
    tb_profile = os.path.join(tbb_path, 'Browser/TorBrowser/Data/Browser/profile.default')
    binary = FirefoxBinary(os.path.join(tbb_path, 'Browser/firefox'))
    profile = FirefoxProfile(tb_profile)

    # Set the security level
    profile.set_preference("extensions.torbutton.security_slider", security_levels[security_level])

    # Stop Tor Browser's internal Tor
    profile.set_preference('extensions.torlauncher.start_tor', False)
    profile.set_preference('extensions.torlauncher.prompt_at_startup', False)
    profile.set_preference('extensions.torbutton.inserted_button', True)
    profile.set_preference('extensions.torbutton.launch_warning', False)

    # Set the details for the external Tor
    profile.set_preference('extensions.torbutton.settings_method', 'custom')
    profile.set_preference('extensions.torbutton.custom.socks_host', tor_socks_host)
    profile.set_preference('extensions.torbutton.custom.socks_port', int(tor_socks_port))
    profile.set_preference('extensions.torbutton.socks_port', int(tor_socks_port))
    profile.set_preference('network.proxy.socks_port', int(tor_socks_port))

    # Stop updates
    profile.set_preference('app.update.enabled', False)
    profile.set_preference('extensions.torbutton.versioncheck_enabled', False)

    # Set the download folder and disable pop up windows
    profile.set_preference("browser.download.folderList", 2)
    profile.set_preference("browser.download.useDownloadDir", True)
    profile.set_preference("browser.download.dir", download_folder)
    profile.set_preference("browser.download.defaultFolder", download_folder)

    # Required to run our custom HTTP-Header-Live extension
    profile.set_preference("xpinstall.signatures.required", False)
    profile.set_preference("xpinstall.whitelist.required", False)
    profile.set_preference("app.update.lastUpdateTime.xpi-signature-verification", 0)
    profile.set_preference("extensions.autoDisableScopes", 10)
    profile.set_preference("extensions.enabledScopes", 15)
    profile.set_preference("extensions.blocklist.enabled", False)
    profile.set_preference("extensions.blocklist.pingCountVersion", 0)

    # Choose the headless mode
    options = Options()
    options.headless = True

    # Set the timeout for webdriver initialization
    #socket.setdefaulttimeout(15)

    try:
        driver = webdriver.Firefox(firefox_profile=profile,
                                   firefox_binary=binary,
                                   options=options)
    except Exception as err:
        logger.error('Couldn\'t initialize the browser, check if there is enough memory available: %s'
                     % err)
        return None

    # Install the HTTP-Header-Live extension
    driver.install_addon(http_header_live_extension, temporary=True)

    # Set driver page load timeout
    driver.implicitly_wait(timeout)
    #socket.setdefaulttimeout(timeout)

    # Try sending a request to the server and get server's response
    try:
        driver.get(url)
    except Exception as err:
        driver.quit()
        logger.error('webdriver.Firefox.get() says: %s' % err)
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
            driver.quit()
            logger.error('Cannot parse the headers: %s' % err)
            return None

    if requests_data is None:
        driver.quit()
        # Don't return anything since we couldn't capture the headers
        logger.error('Couldn\'t capture the headers from %s' % http_header_live_export_file)
        return None

    # Record the results
    results['html_data'] = driver.page_source
    results['requests'] = format_requests.tb(requests_data, url)

    logger.debug('I\'m done fetching %s', url)

    driver.quit()

    return results
