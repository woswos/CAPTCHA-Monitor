import logging
import configparser
from captchamonitor.utils.sqlite import SQLite
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


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

        params = {}
        params['url'] = result['url']
        params['additional_headers'] = result['request_headers']
        params['job_id'] = result['id']
        params['method'] = result['method']

        return params
