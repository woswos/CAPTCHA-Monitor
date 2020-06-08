import logging
from captchamonitor.utils.sqlite import SQLite

logger = logging.getLogger(__name__)


class Queue:
    def __init__(self, db_file):
        """
        This class is an abstraction layer for the SQLite class to have a simpler interface
        """
        self.db_file = db_file
        db = SQLite(db_file)
        db.check_if_db_exists()

    def get_job(self):
        db_file = self.db_file
        db = SQLite(db_file)
        result = db.get_first_uncompleted_job()
        if result is None:
            logger.debug('No jobs available in the queue')
        return result

    def add_job(self, data):
        db_file = self.db_file
        db = SQLite(db_file)
        db.insert_job(data)
        logger.info('Added new job for fetching "%s" via "%s" to database', data['url'], data['method'])

    def remove_job(self, id):
        db_file = self.db_file
        db = SQLite(db_file)
        db.remove_job(id)
        logger.info('Removed the job with id "%s" from database', id)
