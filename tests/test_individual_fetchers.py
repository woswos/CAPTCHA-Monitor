import pytest
import sys
import os
import requests
from captchamonitor import fetchers

methods_over_tor = [fetchers.firefox_over_tor,
                    fetchers.tor_browser,
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

# Get the list of latest exit nodes and choose the first one in the list
tor_bulk_exit_list = requests.get('https://check.torproject.org/torbulkexitlist')
for exit in tor_bulk_exit_list.iter_lines():
    exit_node = exit.decode("utf-8")
    break

captcha_sign = 'Cloudflare'
tbb_path = os.environ['CM_TBB_PATH']
tor_socks_host = os.environ['CM_TOR_HOST']
tor_socks_port = os.environ['CM_TOR_SOCKS_PORT']
tor_control_port = int(os.environ['CM_TOR_CONTROL_PORT'])


@pytest.mark.parametrize('method', methods_over_tor)
def test_tor_and_exit_node_connection(method):
    url = 'https://check.torproject.org/'

    data = method(url=url,
                  tbb_path=tbb_path,
                  tor_socks_host=tor_socks_host,
                  tor_socks_port=tor_socks_port,
                  tor_control_port=tor_control_port,
                  exit_node=exit_node)

    # Check if the specified exit node is connected
    test = (exit_node in data['html_data'])

    assert test == True


@pytest.mark.parametrize('method', methods_all)
def test_additional_headers(method):
    url = 'http://www.xhaus.com/headers'
    headers = '{"x-test": "pytest"}'

    data = method(url=url,
                  additional_headers=headers,
                  tbb_path=tbb_path,
                  tor_socks_host=tor_socks_host,
                  tor_socks_port=tor_socks_port,
                  tor_control_port=tor_control_port)

    # Check if the custom header was sent to the server
    test_1 = ('pytest' in data['html_data'])

    # Check if the custom header was included in the requests headers
    test_2 = ('pytest' in data['request_headers'])

    assert (test_1 and test_2) == True
