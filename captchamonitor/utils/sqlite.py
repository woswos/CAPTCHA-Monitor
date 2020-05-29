import os.path
import sqlite3
import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class SQLite:
    def __init__(self, params):
        self.params = params
        self.check_if_db_exists()

    def submit(self):
        """
        Submits given results to the SQLite database
        """

        # Set database connection
        conn = sqlite3.connect(self.params['db_file'])

        # Prepare the SQL query
        sql_query = '''INSERT INTO captcha (
                    measurement,
                    url,
                    captcha_sign,
                    html_data,
                    result,
                    request_headers,
                    response_headers
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)'''
        sql_params = (self.params['method'],
                      self.params['url'],
                      self.params['captcha_sign'],
                      self.params['html_data'],
                      self.params['result'],
                      self.params['request_headers'],
                      self.params['response_headers']
                      )

        logger.debug(sql_query)
        logger.debug(sql_params)

        # Try to connect to the database
        try:
            conn.cursor().execute(sql_query, sql_params)
            conn.commit()

        except Exception as err:
            logger.critical(
                'sqlite3.connect.cursor.execute() says: %s' % err)

        conn.close()

    def check_if_db_exists(self):
        """
        Creates the database tables if the SQLite file doesn't exist
        """

        output_db = self.params['db_file']

        # Return if the database already exists
        if os.path.isfile(output_db) and os.access(output_db, os.R_OK):
            logger.debug('The SQLite database already exists, skipping the creation')
            return

        logger.info('The SQLite database does not exist, creating it now')

        open(output_db, 'w').close()

        # Set database connection
        conn = sqlite3.connect(output_db)

        # SQL query to create the tables for the first time run
        sql_query_create_table = '''CREATE TABLE captcha (
                                	id INTEGER PRIMARY KEY AUTOINCREMENT,
                                	measurement TEXT,
                                	url TEXT,
                                	captcha_sign TEXT,
                                    html_data TEXT,
                                	result TEXT,
                                    request_headers TEXT,
                                    response_headers TEXT
                                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                                    )'''

        conn.cursor().execute(sql_query_create_table)
        conn.commit()
        conn.close()
