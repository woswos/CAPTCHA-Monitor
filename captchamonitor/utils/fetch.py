import logging
import os
import pwd
from captchamonitor import fetchers
import captchamonitor.utils.tor_launcher as tor_launcher
logger = logging.getLogger(__name__)


def fetch_via_method(data):
    tbb_path = os.environ['CM_TBB_PATH']
    tor_socks_host = os.environ['CM_TOR_HOST']
    tor_socks_port = os.environ['CM_TOR_SOCKS_PORT']
    tor_control_port = int(os.environ['CM_TOR_CONTROL_PORT'])

    method = data['method']
    url = data['url']
    captcha_sign = data['captcha_sign']
    additional_headers = data['additional_headers']
    exit_node = data['exit_node']
    tbb_security_level = data['tbb_security_level']

    results = {}
    logger.info('Fetching "%s" via "%s"', url, method)

    tor_config = {'tor_socks_host': tor_socks_host,
                  'tor_socks_port': tor_socks_port,
                  'tor_control_port': tor_control_port,
                  'exit_node': exit_node,
                  'tor_dir': '/tmp/captchamonitor_tor_datadir_%s' % pwd.getpwuid(os.getuid())[0]
                  }

    if 'tor' in method:
        tor_process = tor_launcher.launch_tor_with_config(tor_config)
        stem_controller = tor_launcher.StemController(tor_config)
        stem_controller.start()

    if(method == 'tor_browser'):
        results = fetchers.tor_browser(tor_config,
                                       tbb_path,
                                       url,
                                       additional_headers,
                                       tbb_security_level)

    elif(method == 'firefox_over_tor'):
        results = fetchers.firefox_over_tor(tor_config, url, additional_headers)

    elif(method == 'chromium_over_tor'):
        results = fetchers.chromium_over_tor(tor_config, url, additional_headers)

    elif(method == 'requests_over_tor'):
        results = fetchers.requests_over_tor(tor_config, url, additional_headers)

    elif(method == 'curl_over_tor'):
        results = fetchers.curl_over_tor(tor_config, url, additional_headers)

    elif(method == 'requests'):
        results = fetchers.requests(url, additional_headers)

    elif(method == 'firefox'):
        results = fetchers.firefox(url, additional_headers)

    elif(method == 'chromium'):
        results = fetchers.chromium(url, additional_headers)

    elif(method == 'curl'):
        results = fetchers.curl(url, additional_headers)

    else:
        logger.info('"%s" is not available, please check the method name"', method)
        return None

    if 'tor' in method:
        stem_controller.join()
        tor_launcher.kill(tor_process)

    return results
