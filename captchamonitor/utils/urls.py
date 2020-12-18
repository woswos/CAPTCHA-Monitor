import datetime
import logging
import os

from captchamonitor.utils.db import DB


class Urls:
    def __init__(self):
        """
        This class is an abstraction layer for the DB class to have a simpler interface
        """
        self.db = DB()
        self.logger = logging.getLogger(__name__)

    def get_urls(self):
        result = self.db.get_table_entries(self.db.urls_table_name)
        return result
