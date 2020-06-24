import pytest
from captchamonitor.utils.fetch import fetch_via_method
import captchamonitor.utils.tor_launcher as tor_launcher
from pathlib import Path
import os

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

os.environ['CM_TOR_DIR_PATH'] = str(os.path.join(str(Path.home()), '.cm_tor', '0'))
# Just get a single exit node for testing purposes
tor = tor_launcher.TorLauncher()
for exit in tor.get_exit_relays().keys():
    exit_node = exit
    break


job = {'method': '',
       'url': 'https://check.torproject.org',
       'captcha_sign': '',
       'additional_headers': '',
       'exit_node': exit_node,
       'tbb_security_level': 'medium',
       'browser_version': ''}


@pytest.fixture(autouse=True, scope="module")
def parametrization_scope():
    """
    This will be run before and after the tests to start and stop Tor
    """
    print("Starting Tor for the tests")
    tor = tor_launcher.TorLauncher()
    tor.start()
    tor.new_circuit()

    # Executing parametrizations
    yield

    print("Stopping Tor")
    tor.stop()


@pytest.mark.parametrize('method', methods)
def test_tor_and_exit_node_connection(method):
    # Here, the purpose is not to actuall fetch pages, but to
    #   check if the variables are passed correctly without issues
    job['method'] = method

    try:
        fetched_data = fetch_via_method(job)

    except:
        pytest.fail("Error...")
