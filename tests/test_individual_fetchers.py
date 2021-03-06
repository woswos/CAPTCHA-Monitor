import pytest
from captchamonitor import fetchers
import captchamonitor.utils.tor_launcher as tor_launcher
import port_for
import os
from pathlib import Path
import json

methods_over_tor = [fetchers.tor_browser,
                    fetchers.firefox_over_tor,
                    fetchers.chromium_over_tor,
                    fetchers.requests_over_tor,
                    fetchers.curl_over_tor
                    ]

methods_over_regular_internet = [fetchers.firefox,
                                 fetchers.chromium,
                                 fetchers.requests,
                                 fetchers.curl
                                 ]

methods_all = methods_over_tor + methods_over_regular_internet

# Just get a single exit node for testing purposes
tor = tor_launcher.TorLauncher()
for exit in tor.get_exit_relays().keys():
    exit_node = exit
    break


@pytest.fixture(autouse=True, scope="module")
def parametrization_scope():
    """
    This will be run before and after the tests to start and stop Tor
    """
    print("Starting Tor for the tests")

    os.environ['CM_TOR_SOCKS_PORT'] = str(port_for.select_random())
    os.environ['CM_TOR_CONTROL_PORT'] = str(port_for.select_random())
    os.environ['CM_DOWNLOAD_FOLDER'] = str(Path.home())

    tor = tor_launcher.TorLauncher()
    tor.start()
    tor.new_circuit(exit_node)

    # Executing parametrizations
    yield

    print("Stopping Tor")
    tor.stop()


@pytest.mark.parametrize('method', methods_over_tor)
def test_tor_and_exit_node_connection(method):
    url = 'https://check.torproject.org/'

    # Retry up to 3 times
    for i in range(3):
        data = method(url)

        if data is not None:
            # Check if the specified exit node is connected
            test = (exit_node in data['html_data'])
            break

    assert test == True


@pytest.mark.parametrize('method', methods_all)
def test_additional_headers(method):
    url = 'http://myhttpheader.com/'
    headers = '{"x-test": "pytest"}'

    # Retry up to 3 times
    for i in range(3):
        data = method(url=url, additional_headers=headers)

        if data is not None:
            # Check if the custom header was sent to the server
            test_1 = ('pytest' in data['html_data'])

            # Check if the custom header was included in the requests headers
            test_2 = ('pytest' in str(json.loads(data['requests'])['data'][0]['request_headers']))

            if(test_1 and test_2) == True:
                break

    assert (test_1 and test_2) == True
