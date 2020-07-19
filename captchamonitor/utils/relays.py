import logging
import os
from captchamonitor.utils.db import DB


class Relays:
    def __init__(self):
        """
        This class is used for interacting with the 'relays' table in the database
        """
        self.db = DB()
        self.logger = logging.getLogger(__name__)

    def get_relays(self):
        result = self.db.get_table_entries(self.db.relays_table_name)
        if result is None:
            self.logger.debug('No relay entries found')
        return result

    def get_online_relays(self):
        identifiers = {'status': 'online'}
        result = self.db.get_table_entries(self.db.relays_table_name, identifiers=identifiers)
        if result is None:
            self.logger.debug('No relay entries found')
        return result

    def get_relays_fingerprints(self):
        columns = ['fingerprint']
        result = self.db.get_table_entries(self.db.relays_table_name, columns=columns)
        if result is None:
            self.logger.debug('No relay entries found')
        return result

    def make_all_relays_offline(self):
        data = {'status': 'offline'}
        self.db.update_table_entry(self.db.relays_table_name, data)

    def add_relay_if_not_exists(self, data):
        self.db.insert_entry_into_table(self.db.relays_table_name, data, ignore_existing=True)

    def remove_relay(self, fpr):
        # self.db.remove_job(job_id)
        #self.logger.debug('Removed the job with id "%s" from queue', job_id)
        pass

    def update_relay(self, fingerprint, data):
        identifiers = {'fingerprint': fingerprint}
        self.db.update_table_entry(self.db.relays_table_name, data, identifiers)

    def get_completed_jobs_for_given_relay(self, address):
        identifiers = {'exit_node': address}
        columns = ['timestamp', 'method', 'url', 'tbb_security_level', 'browser_version', 'is_captcha_found']
        return self.db.get_table_entries(self.db.results_table_name, columns=columns, identifiers=identifiers)
