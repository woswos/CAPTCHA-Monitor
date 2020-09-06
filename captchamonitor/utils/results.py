import logging
import os
import datetime
from captchamonitor.utils.db import DB


class Results:
    def __init__(self):
        """
        This class is an abstraction layer for the DB class to have a simpler interface
        """
        self.db = DB()
        self.logger = logging.getLogger(__name__)

    def get_results(self, after, before, columns=['*'], identifiers='', identifier_operators=''):
        after = after.strftime('%Y-%m-%d %H:%M:%S')
        before = before.strftime('%Y-%m-%d %H:%M:%S')
        result = self.db.get_table_entries(self.db.results_table_name, columns=columns,
                                           after_timestamp=after,
                                           before_timestamp=before,
                                           identifiers=identifiers,
                                           identifier_operators=identifier_operators,
                                           order_by='timestamp')
        return result
