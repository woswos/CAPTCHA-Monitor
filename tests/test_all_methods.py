import logging
import sys
import configparser
import os
sys.path.append('../')
from captchamonitor.chef import CaptchaMonitor

logger_format = '%(asctime)s %(module)s [%(levelname)s] %(message)s'
logging.basicConfig(format=logger_format)
logger = logging.getLogger('captchamonitor')
logger.setLevel(logging.INFO)


if __name__ == '__main__':

    url = 'https://check.torproject.org/'
    methods = ['chromium', 'chromium_over_tor', 'firefox', 'firefox_over_tor', 'tor_browser', 'requests']
    captcha_sign = 'Cloudflare'
    config_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'config.ini')

    logger.info('Deleting the existing db')
    config = configparser.ConfigParser()
    config.read(config_file)
    db_file = config['SQLite']['db_file']
    if os.path.exists(db_file):
        os.remove(db_file)

    logger.info('Testing all available methods')
    for method in methods:
        cm = CaptchaMonitor(method, config_file)
        cm.create_params()
        cm.fetch(url, captcha_sign)
        cm.detect_captcha()
        cm.store_results()
    logger.info('Done testing')
