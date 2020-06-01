import logging
import sys
from os.path import join, dirname, realpath
sys.path.append('../')
from captchamonitor.chef import CaptchaMonitor

logger_format = '%(asctime)s %(module)s [%(levelname)s] %(message)s'
logging.basicConfig(format=logger_format)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

if __name__ == '__main__':

    config_file = join(dirname(realpath(__file__)), 'config.ini')
    url = 'https://check.torproject.org'
    methods = ['firefox', 'firefox_with_tor', 'tor_browser', 'requests']

    logger.info('Testing all available methods \n')

    for method in methods:
        cm = CaptchaMonitor(method, config_file)
        cm.create_params()
        cm.fetch(url)
        cm.detect_captcha()
        cm.store()
        print('\n')

    logger.info('Done testing')
