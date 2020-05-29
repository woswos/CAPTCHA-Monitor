import configparser
import time
import logging
from captchamonitor.fetchers import tor
from captchamonitor.fetchers import requests
from captchamonitor.utils.sqlite import SQLite
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class CaptchaMonitor:
    def __init__(self, method):
        self.params = {}
        self.params['method'] = method

    def create_params(self):
        config = configparser.ConfigParser()
        config.read('captchamonitor/resources/config.ini')

        # The parameters required to run the tests
        self.params['captcha_sign'] = config['DEFAULT']['captcha_sign']
        self.params['tbb_path'] = config['DEFAULT']['tbb_path']
        self.params['headless_mode'] = config['DEFAULT']['headless_mode']
        self.params['db_mode'] = config['DEFAULT']['db_mode']

        if(self.params['db_mode'] == 'SQLite'):
            self.params['db_file'] = config['SQLite']['db_file']

    def get_params(self):
        return self.params

    def fetch(self, url):
        self.params['url'] = url
        self.params['time_stamp'] = int(time.time())

        if(self.params['method'] == 'tor'):
            self.params['html_data'] = tor.fetch(self.params)

    def detect_captcha(self):
        captcha_sign = self.params.get('captcha_sign')
        html_data = self.params.get('html_data')

        if(html_data != -1):
            self.params['result'] = int(html_data.find(captcha_sign) > 0)

    def store(self):
        if(self.params['db_mode'] == 'SQLite'):
            db = SQLite(self.params)
            db.submit()
