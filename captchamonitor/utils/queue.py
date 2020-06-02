import logging
import configparser
from captchamonitor.utils.sqlite import SQLite

logger = logging.getLogger(__name__)


class Queue:
    def __init__(self, config_file):
        self.params = {}
        config = configparser.ConfigParser()
        config.read(config_file)
        self.params['db_file'] = config['SQLite']['db_file']
        pass

    def check(self):
        db = SQLite(self.params)
        result = db.get_number_of_not_completed_jobs()
        logger.debug('%s job(s) available', result)
        return result

    def get_params(self):
        db = SQLite(self.params)
        result = db.get_first_not_completed_job()

        # params to rename and the rest is same
        result['additional_headers'] = result['request_headers']
        result['job_id'] = result['id']

        return result

    def add_job(self, method, url, captcha_sign, additional_headers=None):
        data = {}
        data['method'] = method
        data['url'] = url
        data['captcha_sign'] = captcha_sign
        data['additional_headers'] = additional_headers

        db = SQLite(self.params)
        db.insert_job(data)
