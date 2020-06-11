import pytest
import sys
import os
import requests
from captchamonitor import fetchers
import captchamonitor.utils.tor_launcher as tor_launcher

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

tor_config = {'tor_socks_host': tor_socks_host,
              'tor_socks_port': tor_socks_port,
              'tor_control_port': tor_control_port,
              'exit_node': exit_node
              }


@pytest.mark.parametrize('method', methods_over_tor)
def test_tor_and_exit_node_connection(method):
    url = 'https://check.torproject.org/'

    tor_process = tor_launcher.launch_tor_with_config(
        tor_socks_host, tor_socks_port, tor_control_port, exit_node)

    data = method(url=url,
                  tor_config=tor_config,
                  tbb_path=tbb_path)

    # Check if the specified exit node is connected
    test = (exit_node in data['html_data'])

    tor_launcher.kill(tor_process)

    assert test == True


@pytest.mark.parametrize('method', methods_all)
def test_additional_headers(method):
    url = 'http://www.xhaus.com/headers'
    headers = '{"x-test": "pytest"}'

    tor_process = tor_launcher.launch_tor_with_config(
        tor_socks_host, tor_socks_port, tor_control_port, exit_node)

    data = method(url=url,
                  additional_headers=headers,
                  tor_config=tor_config,
                  tbb_path=tbb_path)

    # Check if the custom header was sent to the server
    test_1 = ('pytest' in data['html_data'])

    # Check if the custom header was included in the requests headers
    test_2 = ('pytest' in data['request_headers'])

    tor_launcher.kill(tor_process)

    assert (test_1 and test_2) == True
