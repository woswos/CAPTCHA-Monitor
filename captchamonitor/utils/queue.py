import logging
import os
from captchamonitor.utils.sqlite import SQLite

logger = logging.getLogger(__name__)


class Queue:
    def __init__(self):
        """
        This class is an abstraction layer for the SQLite class to have a simpler interface
        """
        self.db = SQLite()
        self.db.check_if_db_exists()

    def get_job(self, worker_id):
        self.db.claim_first_uncompleted_job(worker_id)
        result = self.db.get_claimed_job(worker_id)
        if result is None:
            logger.debug('No jobs available in the queue')
        return result

    def add_job(self, data):
        self.db.insert_job_into_table(self.db.queue_table_name, data)
        logger.info('Added new job for fetching "%s" via "%s" to database',
                    data['url'], data['method'])

    def insert_result(self, data):
        self.db.insert_job_into_table(self.db.results_table_name, data)
        logger.info('Inserted the results of %s into the database', data['url'])

    def remove_job(self, job_id):
        self.db.remove_job(job_id)
        logger.info('Removed the job with id "%s" from queue', job_id)

    def move_failed_job(self, job_id):
        data = self.db.get_job_with_id(job_id)
        del data['claimed_by']
        self.db.insert_job_into_table(self.db.failed_table_name, data)

        self.db.remove_job(job_id)
        logger.info('Moved the job with id "%s" to failed jobs', job_id)

    def count_remaining_jobs(self):
        return self.db.count_table_entries(self.db.queue_table_name)

    def count_completed_jobs(self):
        return self.db.count_table_entries(self.db.results_table_name)

    def count_failed_jobs(self):
        return self.db.count_table_entries(self.db.failed_table_name)
