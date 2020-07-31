"""
Fetch a given URL using selenium, Brave Browser, and Tor
"""

import os
import pathlib
import glob
import logging
import json
import socket
import time
import subprocess
from pathlib import Path
from stem.control import Controller
from pyvirtualdisplay import Display
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import captchamonitor.utils.tor_launcher as tor_launcher
import captchamonitor.utils.fetcher_utils as fetcher_utils


def fetch_via_brave_over_tor(url, exit_node, additional_headers=None, timeout=30, **kwargs):
    logger = logging.getLogger(__name__)

    results = {}

    brave_browser_location = '/usr/bin/brave-browser'

    # Start virtual display because Chromium doesn't support extensions in headless mode
    display = Display(visible=True, size=(1000, 900), backend='xvfb')
    display.start()

    options = Options()
    # options.headless = True
    # options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-dev-shm-usage')

    # Set Brave binary
    options.binary_location = brave_browser_location

    # Set the timeout for webdriver initialization
    # socket.setdefaulttimeout(15)

    try:
        driver = webdriver.Chrome(options=options)

    except Exception as err:
        display.stop()
        logger.error('Couldn\'t initialize the browser, check if there is enough memory available: %s'
                     % err)
        return None

    # Get the handle for the regular window
    initial_window_handle = driver.window_handles[0]

    tor_window_handle = ''
    for i in range(10):
        try:
            # Send Alt+Shift+N to the browser to open a "Private Window with Tor"
            subprocess.run(['xdotool', 'key', 'alt+shift+n'])

            # Try to get the window handle of the new window
            tor_window_handle = driver.window_handles[1]
            break

        except IndexError:
            time.sleep(3)

    if tor_window_handle != '':
        # Attach to the new Tor window
        driver.switch_to.window(tor_window_handle)

    else:
        fetcher_utils.force_quit_driver(driver)
        display.stop()
        logger.error('Couldn\'t attach to the "Private Window with Tor"')
        return None

    # Find the path to the temporary profile
    driver.get('chrome://version/')
    profile_path = driver.find_element_by_id('profile_path').text

    # Read the Tor control port
    brave_browser_controlport_file = os.path.join(profile_path, '../../../tor/watch/controlport')
    control_port = ''
    for i in range(30):
        try:
            file = open(brave_browser_controlport_file, 'r')
            control_port = int(file.read().split(':')[1])
            if control_port != '':
                break

        except FileNotFoundError:
            time.sleep(3)

    # Stop if control port was not obtained for some reason
    if control_port == '':
        fetcher_utils.force_quit_driver(driver)
        display.stop()
        logger.error('Cloud not read the control port for Brave Browser')
        return None

    # Connect to the Tor process and stop circuit creation
    controller = Controller.from_port(address='127.0.0.1', port=int(control_port))
    controller.authenticate()
    controller.set_conf('__DisablePredictedCircuits', '1')
    controller.set_conf('__LeaveStreamsUnattached', '1')

    # tor_launcher will take over the Tor control from now on
    brave_browser_tor_dir = os.path.join(profile_path, '../../../tor/data')
    tor = tor_launcher.TorLauncher()
    tor.bind_controller('127.0.0.1', int(control_port), brave_browser_tor_dir)

    # It takes some time for Brave Browser's Tor process to fetch the consensus
    # Keep trying until the consensus is fetched
    succeeded = False
    for i in range(30):
        try:
            tor.new_circuit(exit_node)
            succeeded = True
            break

        except Exception as err:
            time.sleep(5)

    # Stop if the circuit was not created for some reason
    if control_port == '':
        fetcher_utils.force_quit_driver(driver)
        display.stop()
        logger.error('Cloud not create the circuit')
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
        fetcher_utils.force_quit_driver(driver)
        display.stop()
        tor.stop()
        logger.error('webdriver.Chrome.get() says: %s' % err)
        return None

    # Record the results
    results['html_data'] = driver.page_source
    results['requests'] = '{ "data": "At the moment, capturing the HTTP requests are not supported with Brave Browser over Tor" }'

    logger.debug('I\'m done fetching %s', url)

    fetcher_utils.force_quit_driver(driver)
    display.stop()
    tor.stop()

    return results
