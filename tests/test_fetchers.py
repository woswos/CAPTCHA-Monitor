import pytest
import sys
import configparser
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


@pytest.mark.parametrize('method', methods_over_tor)
def test_tor_and_exit_node_connection(method):
    url = 'https://check.torproject.org/'

    captcha_sign = 'Cloudflare'
    tor_socks_host = '127.0.0.1'
    tor_socks_port = '9090'
    tbb_path = '/home/woswos/tor-browser_en-US'

    data = method(url=url,
                  tbb_path=tbb_path,
                  tor_socks_host=tor_socks_host,
                  tor_socks_port=tor_socks_port,
                  exit_node=exit_node)

    # Check if the specified exit node is connected
    test = (exit_node in data['html_data'])

    assert test == True


@pytest.mark.parametrize('method', methods_all)
def test_additional_headers(method):
    url = 'http://www.xhaus.com/headers'
    headers = '{"x-test": "pytest"}'

    captcha_sign = 'Cloudflare'
    tor_socks_host = '127.0.0.1'
    tor_socks_port = '9090'
    tbb_path = '/home/woswos/tor-browser_en-US'

    data = method(url=url,
                  additional_headers=headers,
                  tbb_path=tbb_path,
                  tor_socks_host=tor_socks_host,
                  tor_socks_port=tor_socks_port)

    # Check if the custom header was sent to the server
    test_1 = ('pytest' in data['html_data'])

    # Check if the custom header was included in the requests headers
    test_2 = ('pytest' in data['request_headers'])

    assert (test_1 and test_2) == True


# @pytest.mark.parametrize('method', methods_all)
# def test_captcha_check(method):
#     url = 'https://www.cloudflare.com/'
#
#     captcha_sign = 'Cloudflare'
#     tor_socks_host = '127.0.0.1'
#     tor_socks_port = '9090'
#     tbb_path = '/home/woswos/tor-browser_en-US'
#
#     data = method(url=url,
#                   tbb_path=tbb_path,
#                   tor_socks_host=tor_socks_host,
#                   tor_socks_port=tor_socks_port)
#
#     # Check if the custom header was sent to the server
#     test_1 = ('pytest' in data['html_data'])
#
#     # Check if the custom header was included in the requests headers
#     test_2 = ('pytest' in data['request_headers'])
#
#     assert (test_1 and test_2) == True
