from captchamonitor.chef import CaptchaMonitor
import logging
import sys
import configparser
import os
import requests
sys.path.append('../')

logger_format = '%(asctime)s %(module)s [%(levelname)s] %(message)s'
logging.basicConfig(format=logger_format)
logger = logging.getLogger('captchamonitor')
logger.setLevel(logging.INFO)


if __name__ == '__main__':

    methods = ['firefox_with_tor', 'tor_browser']

    # Get the list of latest exit nodes and choose the first one in the list
    tor_bulk_exit_list = requests.get('https://check.torproject.org/torbulkexitlist')
    for exit in tor_bulk_exit_list.iter_lines():
        exit_node = exit.decode("utf-8")
        logger.info('Using "%s" as the exit node', exit_node)
        break

    url = 'https://check.torproject.org/'
    captcha_sign = 'Cloudflare'
    additional_headers = None
    config_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'config.ini')

    logger.info('Deleting the existing db')
    config = configparser.ConfigParser()
    config.read(config_file)
    db_file = config['SQLite']['db_file']
    if os.path.exists(db_file):
        os.remove(db_file)

    logger.info('Testing the Tor launcher')
    for method in methods:
        cm = CaptchaMonitor(method, config_file)
        cm.create_params()
        cm.fetch(url, captcha_sign, additional_headers, exit_node)

        if exit_node not in cm.params['html_data']:
            logger.warning('This fetcher is not connected to the specified exit node!')
            exit()
        else:
            logger.info('This fetcher is connected to the specified exit node, cool')

    logger.info('Done testing')
