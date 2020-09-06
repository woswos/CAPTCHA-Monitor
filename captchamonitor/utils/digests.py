import logging
import os
import datetime
from captchamonitor.utils.db import DB


class Digests:
    def __init__(self):
        """
        This class is an abstraction layer for the DB class to have a simpler interface
        """
        self.db = DB()
        self.logger = logging.getLogger(__name__)

    def insert_digest(self, data):
        self.db.insert_entry_into_table(self.db.digest_table_name, data)
