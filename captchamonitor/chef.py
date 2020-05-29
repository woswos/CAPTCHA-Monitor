import configparser
import time
import logging
from captchamonitor.fetchers import tor
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
        self.params['captcha_sign'] = config['DEFAULT']['captcha_sign']
        self.params['tbb_path'] = config['DEFAULT']['tbb_path']
        self.params['db_mode'] = config['DEFAULT']['db_mode']

        if(self.params['db_mode'] == 'SQLite'):
            self.params['db_file'] = config['SQLite']['db_file']

    def get_params(self):
        return self.params

    def fetch(self, url, request_headers=None):
        self.params['url'] = url
        self.params['request_headers'] = request_headers
        self.params['time_stamp'] = int(time.time())

        logger.info('Fetching "%s" via "%s"', self.params['url'], self.params['method'])

        if(self.params['method'] == 'tor'):
            self.params = tor.fetch(self.params)

        elif(self.params['method'] == 'requests'):
            self.params = requests.fetch(self.params)

        elif(self.params['method'] == 'firefox'):
            self.params = firefox.fetch(self.params)

    def detect_captcha(self):
        captcha_sign = self.params.get('captcha_sign')
        html_data = self.params.get('html_data')

        logger.info('Searching for "%s" in "%s"', self.params['captcha_sign'], self.params['url'])

        if(self.params.get('html_data') != -1):
            self.params['result'] = int(html_data.find(captcha_sign) > 0)

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
