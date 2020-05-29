import configparser
import time
import logging
from captchamonitor.fetchers import firefox_with_tor
from captchamonitor.fetchers import tor_browser
from captchamonitor.fetchers import requests
from captchamonitor.fetchers import firefox
from captchamonitor.utils.sqlite import SQLite
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class CaptchaMonitor:
    def __init__(self, method):
        self.params = {}
        self.params['method'] = method

        # Set the default values
        self.params['html_data'] = -1

    def cook(self, url, request_headers=None):
        pass

    def create_params(self):
        config = configparser.ConfigParser()
        config.read('captchamonitor/resources/config.ini')

        # The parameters required to run the tests
        self.params['captcha_sign'] = config['GENERAL']['captcha_sign']
        self.params['tbb_path'] = config['GENERAL']['tbb_path']
        self.params['db_mode'] = config['GENERAL']['db_mode']
        self.params['tor_socks_address'] = config['GENERAL']['tor_socks_address']
        self.params['tor_socks_port'] = config['GENERAL']['tor_socks_port']

        if(self.params['db_mode'] == 'SQLite'):
            self.params['db_file'] = config['SQLite']['db_file']

    def get_params(self):
        return self.params

    def fetch(self, url, additional_headers=None):
        results = {}
        self.params['url'] = url
        self.params['time_stamp'] = int(time.time())
        method = self.params['method']
        tbb_path = self.params['tbb_path']
        tor_socks_address = self.params['tor_socks_address']
        tor_socks_port = self.params['tor_socks_port']

        logger.info('Fetching "%s" via "%s"', url, method)

        if(method == 'firefox_with_tor'):
            results = firefox_with_tor.run(url=url,
                                           additional_headers=additional_headers,
                                           tor_socks_address=tor_socks_address,
                                           tor_socks_port=tor_socks_port)

        elif(method == 'tor_browser'):
            results = tor_browser.run(url=url,
                                      additional_headers=additional_headers,
                                      tbb_path=tbb_path,
                                      tor_socks_address=tor_socks_address,
                                      tor_socks_port=tor_socks_port)

        elif(method == 'requests'):
            results = requests.run(url, additional_headers)

        elif(method == 'firefox'):
            results = firefox.run(url, additional_headers)

        self.params['all_headers'] = results['all_headers']
        self.params['request_headers'] = results['request_headers']
        self.params['response_headers'] = results['response_headers']
        self.params['html_data'] = results['html_data']

    def detect_captcha(self):
        captcha_sign = self.params.get('captcha_sign')
        html_data = self.params.get('html_data')

        logger.debug('Searching for "%s" in "%s"', self.params['captcha_sign'], self.params['url'])

        if(self.params.get('html_data') != -1):
            is_captcha_found = int(html_data.find(captcha_sign) > 0)
            self.params['is_captcha_found'] = is_captcha_found
            if(is_captcha_found == 1):
                logger.info('I found "%s" in "%s"', self.params['captcha_sign'], self.params['url'])

    def store(self):
        db_mode = self.params['db_mode']
        html_data = self.params.get('html_data')

        if(html_data == -1):
            logger.info('There was an error during the process, cannot save to db')
            return

        logger.info('Saving results to the "%s" database', db_mode)

        if(db_mode == 'SQLite'):
            db = SQLite(self.params)
            db.submit()
