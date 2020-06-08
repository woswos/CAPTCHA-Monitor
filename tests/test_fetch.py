import pytest
import sys
import os
import requests
import random
import string
from captchamonitor.utils.fetch import fetch_via_method


def randomString(stringLength=10):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(stringLength))


os.environ['CM_TBB_PATH'] = '/home/woswos/tor-browser_en-US'
os.environ['CM_TOR_HOST'] = '127.0.0.1'
os.environ['CM_TOR_PORT'] = '9090'

methods = ['firefox',
           'firefox_over_tor',
           'tor_browser',
           'chromium',
           'chromium_over_tor',
           'requests',
           'requests_over_tor',
           'curl',
           'curl_over_tor'
           ]

# Get the list of latest exit nodes and choose the first one in the list
tor_bulk_exit_list = requests.get('https://check.torproject.org/torbulkexitlist')
for exit in tor_bulk_exit_list.iter_lines():
    exit_node = exit.decode("utf-8")
    break

job = {'method': '',
       'url': 'https://check.torproject.org',
       'captcha_sign': '',
       'additional_headers': '',
       'exit_node': exit_node,
       'tbb_security_level': 'medium'}


@pytest.mark.parametrize('method', methods)
def test_tor_and_exit_node_connection(method):
    # Here, the purpose is not to actuall fetch pages, but to
    #   check if the variables are passed correctly without issues
    job['method'] = method

    try:
        fetched_data = fetch_via_method(job)

    except:
        pytest.fail("Error...")
