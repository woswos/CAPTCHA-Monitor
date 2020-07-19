import logging
import os
from captchamonitor.utils.db import DB


class Queue:
    def __init__(self):
        """
        This class is an abstraction layer for the DB class to have a simpler interface
        """
        self.db = DB()
        self.logger = logging.getLogger(__name__)

    def get_job(self, worker_id):
        self.db.claim_first_uncompleted_job(worker_id)

        identifiers = {'claimed_by': worker_id}
        result = self.db.get_table_entries(self.db.queue_table_name, identifiers=identifiers)

        if not result:
            self.logger.debug('No jobs available in the queue')
            return None
        return result

    def add_job(self, data):
        self.db.insert_entry_into_table(self.db.queue_table_name, data)
        self.logger.debug('Added new job for fetching "%s" via "%s" to database',
                          data['url'], data['method'])

    def insert_result(self, data):
        self.db.insert_entry_into_table(self.db.results_table_name, data)
        self.logger.debug('Inserted the results of %s into the database', data['url'])

    def remove_job(self, job_id):
        identifiers = {'id': job_id}
        self.db.remove_table_entry(self.db.queue_table_name, identifiers=identifiers)

        self.logger.debug('Removed the job with id "%s" from queue', job_id)

    def move_failed_job(self, job_id):
        identifiers = {'id': job_id}
        data = self.db.get_table_entries(self.db.queue_table_name, identifiers=identifiers)[0]

        del data['claimed_by']
        self.db.insert_entry_into_table(self.db.failed_table_name, data)

        identifiers = {'id': job_id}
        self.db.remove_table_entry(self.db.queue_table_name, identifiers=identifiers)

        self.logger.debug('Moved the job with id "%s" to failed jobs', job_id)

    def count_remaining_jobs(self):
        return self.db.count_table_entries(self.db.queue_table_name)

    def count_completed_jobs(self):
        return self.db.count_table_entries(self.db.results_table_name)

    def count_failed_jobs(self):
        return self.db.count_table_entries(self.db.failed_table_name)
